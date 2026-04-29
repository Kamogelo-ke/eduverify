"""
Email utility for EduVerify.
Sends temporary password emails to newly created invigilator accounts.
If MAIL_USERNAME is not configured, logs the email content instead
so the system works in development without an SMTP server.
"""

import logging
from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
from core.config import settings

logger = logging.getLogger(__name__)


def _get_mail_config() -> ConnectionConfig:
    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )


def _build_email_body(full_name: str, email: str, temp_password: str) -> str:
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px;">
        <div style="background-color: #003087; padding: 20px; border-radius: 8px 8px 0 0;">
          <h1 style="color: white; margin: 0;">EduVerify</h1>
          <p style="color: #cce0ff; margin: 5px 0 0;">Tshwane University of Technology</p>
        </div>

        <div style="background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 8px 8px;">
          <h2 style="color: #003087;">Welcome to EduVerify, {full_name}!</h2>

          <p>An administrator has created an invigilator account for you on the
          EduVerify exam verification system.</p>

          <p>Your login credentials are:</p>

          <div style="background-color: #fff; border: 1px solid #003087; border-radius: 6px;
                      padding: 15px 20px; margin: 20px 0;">
            <p style="margin: 5px 0;"><strong>Email:</strong> {email}</p>
            <p style="margin: 5px 0;"><strong>Temporary Password:</strong>
              <span style="font-family: monospace; font-size: 16px; color: #c0392b;">
                {temp_password}
              </span>
            </p>
          </div>

          <div style="background-color: #fff3cd; border: 1px solid #ffc107;
                      border-radius: 6px; padding: 12px 16px; margin: 20px 0;">
            <strong>⚠ Important:</strong> This is a temporary password.
            Please change it immediately after your first login.
          </div>

          <p>You can access the system at:
            <a href="http://localhost:8008/docs" style="color: #003087;">
              EduVerify System
            </a>
          </p>

          <hr style="border: none; border-top: 1px solid #ddd; margin: 25px 0;">
          <p style="color: #888; font-size: 12px;">
            This is an automated message from EduVerify. Do not reply to this email.<br>
            Tshwane University of Technology — Exam Verification System
          </p>
        </div>
      </body>
    </html>
    """


async def send_temporary_password_email(
    full_name: str,
    email: str,
    temp_password: str,
) -> bool:
    """
    Send a temporary password email to a newly created invigilator.
    Returns True if sent successfully, False otherwise.
    If email is not configured, logs the credentials instead.
    """
    if not settings.MAIL_ENABLED:
        # Development fallback — print to console so admin can relay manually
        logger.info("=" * 60)
        logger.info("EMAIL NOT CONFIGURED — Temporary credentials:")
        logger.info("  To      : %s <%s>", full_name, email)
        logger.info("  Password: %s", temp_password)
        logger.info("=" * 60)
        return True

    try:
        message = MessageSchema(
            subject="EduVerify — Your Invigilator Account Has Been Created",
            recipients=[email],
            body=_build_email_body(full_name, email, temp_password),
            subtype=MessageType.html,
        )
        fm = FastMail(_get_mail_config())
        await fm.send_message(message)
        logger.info("Temporary password email sent to %s", email)
        return True

    except Exception as exc:
        logger.error("Failed to send email to %s: %s", email, exc)
        return False