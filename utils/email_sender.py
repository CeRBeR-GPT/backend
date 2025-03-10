import random
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config_data.config import load_config, EmailSender

email_sender: EmailSender = load_config(".env").email_sender


def _generate_code():
    return random.randint(email_sender.MIN_CODE, email_sender.MAX_CODE)


def send_verification_code(email: str) -> int:
    smtp_server = smtplib.SMTP("smtp.gmail.com", 587)
    smtp_server.starttls()
    smtp_server.login(email_sender.EMAIL_NAME, email_sender.EMAIL_PASS)

    msg = MIMEMultipart()
    msg['From'] = email_sender.EMAIL_NAME
    msg['To'] = email
    msg['Subject'] = "Регистрация в ToDo"

    code = _generate_code()
    body = f"Ваш код подтверждения: {code}\n\nЭто сообщение отправлено автоматически."

    msg.attach(MIMEText(body, 'plain'))
    smtp_server.sendmail(email_sender.EMAIL_NAME, email, msg.as_string())

    return code
