import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config_data.config import load_config, EmailSender

email_sender: EmailSender = load_config(".env").email_sender


def send_letter(
        *,
        subject: str,
        body: str,
        address: str
) -> str:
    smtp_server = smtplib.SMTP(email_sender.SMPT_HOST, email_sender.SMPT_PORT)
    smtp_server.starttls()
    smtp_server.login(email_sender.EMAIL_NAME, email_sender.EMAIL_PASS)

    msg = MIMEMultipart()
    msg['From'] = email_sender.EMAIL_NAME
    msg['To'] = address
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))
    smtp_server.sendmail(email_sender.EMAIL_NAME, address, msg.as_string())

    return body
