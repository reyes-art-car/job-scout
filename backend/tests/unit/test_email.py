import smtplib
from email.message import EmailMessage
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from job_tracker.config import Settings
from job_tracker.infrastructure.email.factory import build_email_sender
from job_tracker.infrastructure.email.senders import ConsoleEmailSender, SmtpEmailSender

SMTP_CLASS = "job_tracker.infrastructure.email.senders.smtplib.SMTP"


def _sender(**overrides: object) -> SmtpEmailSender:
    values: dict = {
        "host": "smtp.example.com",
        "port": 587,
        "username": "u",
        "password": "p",
        "sender": "no-reply@example.com",
    }
    values.update(overrides)
    return SmtpEmailSender(**values)


def test_smtp_sender_uses_starttls_login_and_builds_a_plain_message() -> None:
    with patch(SMTP_CLASS) as smtp_class:
        smtp = smtp_class.return_value.__enter__.return_value
        _sender().send("ana@example.com", "Asunto", "Cuerpo")
    smtp.starttls.assert_called_once()
    smtp.login.assert_called_once_with("u", "p")
    message: EmailMessage = smtp.send_message.call_args.args[0]
    assert (message["To"], message["Subject"], message["From"]) == ("ana@example.com", "Asunto", "no-reply@example.com")


def test_smtp_sender_uses_implicit_tls_when_asked() -> None:
    with patch(SMTP_CLASS + "_SSL") as smtp_class:
        _sender(security="ssl", port=465).send("ana@example.com", "A", "B")
    smtp_class.assert_called_once()


def test_smtp_failures_never_propagate_nor_log_the_message_body(caplog: pytest.LogCaptureFixture) -> None:
    with patch(SMTP_CLASS, side_effect=smtplib.SMTPException("boom")):
        _sender().send("ana@example.com", "Asunto", "enlace-secreto-con-token")  # no lanza
    assert "enlace-secreto" not in caplog.text and "ana@example.com" not in caplog.text


def test_header_injection_in_the_recipient_is_refused() -> None:
    message = EmailMessage()
    with pytest.raises(ValueError, match=r"[Nn]ewline|[Hh]eader"):
        message["To"] = "ana@example.com\r\nBcc: victima@example.com"


def test_console_backend_is_the_default_and_smtp_is_built_from_settings() -> None:
    assert isinstance(build_email_sender(Settings(_env_file=None)), ConsoleEmailSender)
    smtp = build_email_sender(
        Settings(_env_file=None, email_backend="smtp", smtp_host="h", email_from="a@example.com")  # type: ignore[arg-type]
    )
    assert isinstance(smtp, SmtpEmailSender)


def test_production_requires_smtp_and_an_https_base_url() -> None:
    base = {"app_env": "production", "anthropic_api_key": "k", "jwt_secret": "x" * 32}
    with pytest.raises(ValidationError, match="SMTP_HOST"):
        Settings(_env_file=None, **base)  # type: ignore[arg-type]
    smtp = {"email_backend": "smtp", "smtp_host": "h", "email_from": "a@example.com"}
    with pytest.raises(ValidationError, match="https"):
        Settings(_env_file=None, **base, **smtp, app_base_url="http://example.com")  # type: ignore[arg-type]
    assert Settings(_env_file=None, **base, **smtp, app_base_url="https://example.com")  # type: ignore[arg-type]
