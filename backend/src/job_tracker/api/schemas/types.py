"""Tipos Pydantic que saneán y acotan el texto recibido en la API."""

from typing import Annotated

from pydantic import AfterValidator, StringConstraints

from job_tracker.shared.sanitize import clean_text, validate_http_url

# La longitud se comprueba antes de sanear, para no procesar entradas enormes.
Text100 = Annotated[str, StringConstraints(max_length=100), AfterValidator(clean_text)]
Text255 = Annotated[str, StringConstraints(max_length=255), AfterValidator(clean_text)]
Text4000 = Annotated[str, StringConstraints(max_length=4000), AfterValidator(clean_text)]
SafeUrl = Annotated[str, StringConstraints(max_length=1000), AfterValidator(validate_http_url)]
