import random
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config_data.config import load_config, EmailSender

email_sender: EmailSender = load_config(".env").email_sender


def generate_confirmation_mode():
    return random.randint(email_sender.MIN_CODE, email_sender.MAX_CODE)


def send_feedback(name: str, message: str, from_email: str) -> str:
    smtp_server = smtplib.SMTP("smtp.gmail.com", 587)
    smtp_server.starttls()
    smtp_server.login(email_sender.EMAIL_NAME, email_sender.EMAIL_PASS)

    msg = MIMEMultipart()
    msg['From'] = email_sender.EMAIL_NAME
    msg['To'] = email_sender.ADMIN_EMAIL
    msg['Subject'] = f"Обратная связь от {name}"

    body = (
        f"Пользователь {from_email} оставил обратную связь:\n\n"
        f"{message}"
    )

    msg.attach(MIMEText(body, 'plain'))
    smtp_server.sendmail(email_sender.EMAIL_NAME, email_sender.ADMIN_EMAIL, msg.as_string())

    return body


def send_verification_code(email: str, code: int) -> int:
    smtp_server = smtplib.SMTP("smtp.gmail.com", 587)
    smtp_server.starttls()
    smtp_server.login(email_sender.EMAIL_NAME, email_sender.EMAIL_PASS)

    msg = MIMEMultipart()
    msg['From'] = email_sender.EMAIL_NAME
    msg['To'] = email
    msg['Subject'] = "Регистрация в AI-Chat"

    body = f"Ваш код подтверждения: **{code}**\n\nЭто сообщение отправлено автоматически."

    msg.attach(MIMEText(body, 'plain'))
    smtp_server.sendmail(email_sender.EMAIL_NAME, email, msg.as_string())

    return code
