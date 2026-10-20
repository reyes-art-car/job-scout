from job_tracker.config import Settings
from job_tracker.domain.user.mailer import EmailSender
from job_tracker.infrastructure.email.senders import ConsoleEmailSender, SmtpEmailSender


def build_email_sender(settings: Settings) -> EmailSender:
    if settings.email_backend == "smtp":
        return SmtpEmailSender(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password.get_secret_value(),
            sender=settings.email_from,
            security=settings.smtp_security,
        )
    return ConsoleEmailSender()
