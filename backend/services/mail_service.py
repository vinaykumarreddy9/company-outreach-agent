import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    async def send_email(to_email: str, subject: str, body: str, to_name: str = None) -> bool:
        """
        Sends an email asynchronously using SMTP credentials from settings.
        """
        try:
            # Check if credentials are set
            if not settings.EMAIL_HOST or not settings.EMAIL_USER or not settings.EMAIL_PASSWORD:
                logger.warning("Email credentials not configured. Skipping email send.")
                return False

            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_FROM
            msg['To'] = f"{to_name} <{to_email}>" if to_name else to_email
            msg['Subject'] = subject

            # Attach body as plain text
            msg.attach(MIMEText(body, 'plain'))

            async with aiosmtplib.SMTP(
                hostname=settings.EMAIL_HOST, 
                port=settings.EMAIL_PORT, 
                use_tls=True if settings.EMAIL_PORT == 465 else False,
                start_tls=True if settings.EMAIL_PORT == 587 else False
            ) as server:
                await server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
                await server.send_message(msg)
            
            logger.info(f"Email sent successfully (async) to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email asynchronously to {to_email}: {e}")
            return False
