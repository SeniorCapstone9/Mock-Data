import os
import smtplib
from email.mime.text import MIMEText
from typing import Tuple


def send_email_notification(to_email: str, subject: str, body: str) -> Tuple[bool, str, str]:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    from_email = os.getenv("SMTP_FROM", username or "")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}

    if not host or not from_email or not username or not password:
        return False, "smtp", "Missing SMTP config (SMTP_HOST, SMTP_USER, SMTP_PASS, SMTP_FROM)"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            if use_tls:
                server.starttls()
            server.login(username, password)
            server.sendmail(from_email, [to_email], msg.as_string())
        return True, "smtp", ""
    except Exception as exc:
        return False, "smtp", str(exc)
