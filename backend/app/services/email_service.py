"""
Email delivery service — SMTP with HTML templates.
Falls back to console output when SMTP is not configured.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
APP_NAME = "FinMate"


def _smtp_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def _send(to: str, subject: str, html: str) -> bool:
    if not _smtp_configured():
        logger.info("[EMAIL — SMTP not configured] TO: %s | SUBJECT: %s", to, subject)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{APP_NAME} <{FROM_EMAIL}>"
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to, msg.as_string())
        logger.info("Email sent to %s", to)
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
        return False


def _otp_html(name: str, otp: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #F8FAFC; margin: 0; padding: 40px 0; }}
    .wrap {{ max-width: 480px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
    .header {{ background: #2563EB; padding: 32px 40px; text-align: center; }}
    .header h1 {{ color: #fff; font-size: 22px; font-weight: 700; margin: 0; }}
    .body {{ padding: 32px 40px; }}
    .greeting {{ font-size: 16px; color: #0F172A; margin-bottom: 12px; }}
    .message {{ font-size: 14px; color: #475569; line-height: 1.6; margin-bottom: 28px; }}
    .otp-box {{ background: #F1F5F9; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 28px; }}
    .otp {{ font-size: 38px; font-weight: 700; letter-spacing: 10px; color: #2563EB; font-family: 'Courier New', monospace; }}
    .expiry {{ font-size: 12px; color: #94A3B8; margin-top: 10px; }}
    .footer {{ padding: 20px 40px 32px; font-size: 12px; color: #94A3B8; text-align: center; border-top: 1px solid #F1F5F9; }}
    .security {{ background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 8px; padding: 12px 16px; font-size: 13px; color: #92400E; margin-bottom: 16px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header"><h1>FinMate</h1></div>
    <div class="body">
      <p class="greeting">Hi {name},</p>
      <p class="message">
        Use the one-time code below to verify your email address.
        This code expires in <strong>10 minutes</strong> and can only be used once.
      </p>
      <div class="otp-box">
        <div class="otp">{otp}</div>
        <div class="expiry">Expires in 10 minutes</div>
      </div>
      <div class="security">
        If you didn't request this code, you can safely ignore this email.
        Never share this code with anyone.
      </div>
    </div>
    <div class="footer">
      &copy; 2025 FinMate &nbsp;·&nbsp; AI-Powered Personal Finance
    </div>
  </div>
</body>
</html>"""


def send_verification_otp(to_email: str, name: str, otp: str) -> bool:
    """Send OTP verification email. Returns True if sent via SMTP, False if fallback."""
    subject = f"{otp} is your FinMate verification code"
    html = _otp_html(name, otp)
    sent = _send(to_email, subject, html)
    if not sent:
        # Developer console fallback
        print(f"\n{'='*50}")
        print(f"[FinMate OTP] TO: {to_email} | NAME: {name}")
        print(f"  → OTP CODE: {otp}  (valid 10 min)")
        print(f"{'='*50}\n")
    return sent
