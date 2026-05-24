import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from app.config import settings

logger = logging.getLogger("dot.mail")
LOG_FILE = Path(__file__).resolve().parent.parent / "reset_emails.log"


def _write_log(to_email: str, body: str, reset_link: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n---\nTo: {to_email}\nLink: {reset_link}\n{body}\n")
    logger.info("Reset link (dev) for %s: %s", to_email, reset_link)


def _send_smtp(to_email: str, subject: str, body: str, html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.mail_from
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    if settings.smtp_use_ssl:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, context=context) as server:
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.mail_from, [to_email], msg.as_string())
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            if settings.smtp_use_tls:
                server.starttls(context=ssl.create_default_context())
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.mail_from, [to_email], msg.as_string())


def send_reset_email(to_email: str, reset_link: str) -> dict:
    subject = "./dot — сброс пароля"
    body = f"""Здравствуйте!

Вы запросили сброс пароля на платформе ./dot.

Перейдите по ссылке (действует {settings.reset_token_expire_hours} ч.):
{reset_link}

Если вы не запрашивали сброс — проигнорируйте это письмо.
"""
    html = f"""
    <html><body style="font-family:sans-serif">
    <h2>Сброс пароля ./dot</h2>
    <p>Нажмите кнопку ниже, чтобы задать новый пароль (ссылка действует {settings.reset_token_expire_hours} ч.):</p>
    <p><a href="{reset_link}" style="display:inline-block;padding:12px 24px;background:#3d9cf5;color:#fff;text-decoration:none;border-radius:8px">Сбросить пароль</a></p>
    <p style="color:#666;font-size:14px">Или скопируйте ссылку: {reset_link}</p>
    </body></html>
    """

    if settings.smtp_host and settings.smtp_user and settings.smtp_password:
        try:
            _send_smtp(to_email, subject, body, html)
            return {"sent": True, "mode": "smtp", "message": "Письмо отправлено на ваш email"}
        except Exception as exc:
            logger.exception("SMTP error: %s", exc)
            _write_log(to_email, body, reset_link)
            return {
                "sent": False,
                "mode": "smtp_failed",
                "dev_reset_link": reset_link,
                "error": str(exc),
                "message": "Не удалось отправить письмо. Используйте ссылку ниже или настройте SMTP в .env",
            }

    _write_log(to_email, body, reset_link)
    return {
        "sent": True,
        "mode": "dev_log",
        "dev_reset_link": reset_link,
        "message": "SMTP не настроен — ссылка для сброса показана ниже",
    }
