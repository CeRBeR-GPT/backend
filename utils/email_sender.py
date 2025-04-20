import smtplib
from typing import Optional

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header

from config_data.config import load_config, EmailSender

email_sender: EmailSender = load_config(".env").email_sender


def send_letter(
        *,
        subject: str,
        body: str,
        address: str,
        file_content: Optional[str] = None,
        file_name: Optional[str] = None
) -> str:
    smtp_server = smtplib.SMTP(email_sender.SMPT_HOST, email_sender.SMPT_PORT)
    smtp_server.starttls()
    smtp_server.login(email_sender.EMAIL_NAME, email_sender.EMAIL_PASS)

    msg = MIMEMultipart()
    msg['From'] = email_sender.EMAIL_NAME
    msg['To'] = address
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    if file_content and file_name:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(file_content)
        encoders.encode_base64(part)

        encoded_filename = Header(file_name, 'utf-8').encode()
        part.add_header(
            'Content-Disposition',
            'attachment',
            filename=encoded_filename
        )
        msg.attach(part)

    smtp_server.sendmail(email_sender.EMAIL_NAME, address, msg.as_string())
    smtp_server.quit()

    return body
