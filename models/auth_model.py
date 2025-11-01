from datetime import datetime, timedelta
from flask import redirect, url_for, session, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from .db import get_db_connection
from .otp_model import OTPManager
import requests, os
from google_auth_oauthlib.flow import Flow

class AuthModel:
    def __init__(self, nama_pengguna=None, email=None, password=None, identifier=None):
        self.otp_manager = OTPManager(
            sender_email="delivery@eatrushdelivery.web.id",
            sender_password="6!6Sgk1KP5s+Md",
            smtp_server="mail.eatrushdelivery.web.id"
        )
        self.nama_pengguna = nama_pengguna
        self.email = email
        self.password = generate_password_hash(password) if password else None
        self.identifier = identifier
        self.otp = self.otp_manager.generate_otp() if email else None
        self.pending_user = {
            'nama_pengguna': self.nama_pengguna,
            'email': self.email,
            'password': self.password,
            'otp': self.otp,
            'otp_expiry': (datetime.now() + timedelta(minutes=5)).isoformat()
        } if self.email else None
        self.reset_email = None
        self.reset_otp = None

    def signup_user(self):
        session['pending_user'] = self.pending_user
        self.otp_manager.send_otp_email(self.email, self.otp)
        return jsonify({'status': 'success', 'redirect': '/verify_otp'})

    def verify_otp(self, otp_input=None, resend=False):
        self.pending_user = session.get('pending_user')
        if not self.pending_user:
            return jsonify({'status': 'fail', 'message': 'Tidak ada sesi pendaftaran aktif.'})

        if resend:
            self.otp = self.otp_manager.generate_otp()
            self.pending_user['otp'] = self.otp
            self.pending_user['otp_expiry'] = (datetime.now() + timedelta(minutes=5)).isoformat()
            session['pending_user'] = self.pending_user
            self.otp_manager.send_otp_email(self.pending_user['email'], self.otp)
            return jsonify({'status': 'ok', 'message': 'OTP baru dikirim (berlaku 5 menit).'})

        if not otp_input:
            return jsonify({'status': 'fail', 'message': 'OTP tidak boleh kosong.'})

        otp_expiry = datetime.fromisoformat(self.pending_user['otp_expiry'])
        if datetime.now() > otp_expiry:
            session.pop('pending_user', None)
            return jsonify({'status': 'fail', 'message': 'OTP sudah kedaluwarsa. Silakan kirim ulang.'})

        if otp_input != self.pending_user['otp']:
            return jsonify({'status': 'fail', 'message': 'OTP salah!'})

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Pengguna (NamaPengguna, Email, Password) VALUES (%s, %s, %s)",
            (self.pending_user['nama_pengguna'], self.pending_user['email'], self.pending_user['password'])
        )
        conn.commit()
        cur.close()
        conn.close()
        session.pop('pending_user', None)
        return jsonify({'status': 'success', 'message': 'Registrasi berhasil!'})

    def login_user(self, identifier, password):
        self.identifier = identifier
        self.password = password
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM Pengguna WHERE Email=%s OR NamaPengguna=%s",
            (self.identifier, self.identifier)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user and check_password_hash(user['Password'], self.password):
            return user
        return None

    def send_reset_otp(self, email):
        self.reset_email = email
        self.reset_otp = self.otp_manager.generate_otp()
        session['reset_email'] = self.reset_email
        session['reset_otp'] = self.reset_otp
        self.otp_manager.send_otp_email(email, self.reset_otp)
        return jsonify({'status': 'ok', 'message': 'OTP reset dikirim ke email'})

    def reset_password(self, otp_input, new_password):
        if otp_input != session.get('reset_otp'):
            return jsonify({'status': 'fail', 'message': 'OTP salah!'})

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE Pengguna SET Password=%s WHERE Email=%s",
            (generate_password_hash(new_password), session['reset_email'])
        )
        conn.commit()
        cur.close()
        conn.close()
        session.pop('reset_email', None)
        session.pop('reset_otp', None)
        return jsonify({'status': 'success', 'message': 'Password berhasil diubah'})

    def login_google(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        GOOGLE_CLIENT_ID = GOOGLE_CLIENT_ID
        GOOGLE_CLIENT_SECRET = GOOGLE_CLIENT_SECRET
        REDIRECT_URI = "https://eatrushdelivery.web.id/callback"

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [REDIRECT_URI],
                }
            },
            scopes=["https://www.googleapis.com/auth/userinfo.email", "openid"]
        )
        flow.redirect_uri = REDIRECT_URI
        authorization_url, _ = flow.authorization_url(prompt='consent')
        return redirect(authorization_url)

    def google_callback(self):
        GOOGLE_CLIENT_ID = GOOGLE_CLIENT_ID
        GOOGLE_CLIENT_SECRET = GOOGLE_CLIENT_SECRET
        REDIRECT_URI = "https://eatrushdelivery.web.id/callback"

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=["https://www.googleapis.com/auth/userinfo.email", "openid"],
            redirect_uri=REDIRECT_URI
        )

        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        r = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {credentials.token}'}
        )
        info = r.json()
        self.email = info.get('email')
        self.nama_pengguna = info.get('name', 'User')

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM Pengguna WHERE Email=%s", (self.email,))
        user = cur.fetchone()
        if not user:
            cur.execute(
                "INSERT INTO Pengguna (NamaPengguna, Email, Password) VALUES (%s, %s, '')",
                (self.nama_pengguna, self.email)
            )
            conn.commit()
            cur.execute("SELECT * FROM Pengguna WHERE Email=%s", (self.email,))
            user = cur.fetchone()
        cur.close()
        conn.close()
        session['user'] = user
        return redirect(url_for('home'))

    def logout(self):
        session.clear()
        return redirect(url_for('index'))
