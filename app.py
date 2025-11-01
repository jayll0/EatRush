from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from models.auth_model import AuthModel
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config.update({
    'MYSQL_HOST': '127.0.0.1',
    'MYSQL_USER': 'eatrushd',
    'MYSQL_PASSWORD': '6!6Sgk1KP5s+Md',
    'MYSQL_DB': 'eatrushd_eatrushh'
})


auth_model = AuthModel()
# ---------- ROUTES ----------
@app.route('/')
def index():
    return redirect(url_for('auth_page'))


# 🔹 GABUNG LOGIN + REGISTER DALAM SATU HALAMAN
@app.route('/auth', methods=['GET'])
def auth_page():
    return render_template('auth.html')


# 🔹 LOGIN (dipanggil via fetch POST dari JS)
@app.route('/login', methods=['POST'])
def login():
    identifier = request.form['identifier']
    password = request.form['password']
    user = auth_model.login_user(identifier, password)

    if user:
        session['user'] = user
        return jsonify({'status': 'success', 'message': 'Login berhasil'})
    else:
        return jsonify({'status': 'fail', 'message': 'Email/Nama atau password salah'})


# 🔹 REGISTER (dipanggil via fetch POST dari JS)
@app.route('/register', methods=['POST'])
def register():
    nama_pengguna = request.form['username']
    email = request.form['email']
    password = request.form['password']

    result = auth_model.signup_user(nama_pengguna, email, password)
    return result  


# 🔹 OTP, RESET, GOOGLE, dan lain-lain tetap sama
@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'GET':
        return render_template('verify_otp.html')
    if 'resend' in request.form:
        return auth_model.verify_otp(None, resend=True)
    return auth_model.verify_otp(request.form['otp'])


@app.route('/forgot', methods=['GET'])
def forgot_page():
    return render_template('forgot.html')


@app.route('/forgot', methods=['POST'])
def forgot():
    return auth_model.send_reset_otp(request.form['email'])


@app.route('/reset_password', methods=['POST'])
def reset_password():
    return auth_model.reset_password(
        request.form['otp'],
        request.form['new_password']
    )


@app.route('/login_google')
def login_google():
    return auth_model.login_google()


@app.route('/callback')
def callback():
    return auth_model.google_callback()


@app.route('/home', methods=['GET'])
def home():
    if 'user' not in session:
        return redirect(url_for('auth_page'))
    return render_template('home.html', user=session['user'])


@app.route('/logout', methods=['POST'])
def logout():
    return auth_model.logout()


if __name__ == '__main__':
    app.run(debug=True)
