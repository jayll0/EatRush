import random, string, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import make_msgid, formatdate


class OTPManager:
    def __init__(self, sender_email, sender_password, smtp_server, smtp_port=465):
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def generate_otp(self, length=6):
        """Membuat OTP dengan panjang tertentu (default: 6 digit angka)."""
        return ''.join(random.choices(string.digits, k=length))

    def send_otp_email(self, recipient_email, otp):
        """Mengirim email OTP ke alamat tujuan."""
        subjects = [
            "Kode verifikasi EatRush Anda",
            "Gunakan kode berikut untuk login EatRush",
            "EatRush — Kode verifikasi akun",
            "Kode OTP untuk EatRush",
        ]
        subject = random.choice(subjects)
        plain_body = f"Kode OTP Anda adalah: {otp}\n\nKode ini hanya berlaku sebentar. Jangan bagikan kode ini kepada siapa pun."

        html_body = f"""\
<!doctype html>
<html lang="id">
  <head>
    <meta charset="utf-8"/>
    <style>
      body {{ font-family: Arial; background:#f8fafc; }}
      .otp {{ font-size: 34px; font-weight: bold; color: #ff7a00; }}
    </style>
  </head>
  <body>
    <h3>Kode OTP Anda</h3>
    <div class="otp">{otp}</div>
    <p>Jangan bagikan kode ini kepada siapa pun.</p>
  </body>
</html>
"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"EatRush Delivery <{self.sender_email}>"
        msg["To"] = recipient_email
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain="eatrushdelivery.web.id")

        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, [recipient_email], msg.as_string())
            print("OTP email sent successfully!")
            return True
        except Exception as e:
            print("Error sending OTP:", e)
            return False
