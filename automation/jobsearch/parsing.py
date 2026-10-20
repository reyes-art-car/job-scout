"""Extracción del JSON de ofertas de la respuesta del modelo.

La lógica vive en el backend (`job_tracker.application.search.parsing`) y es la misma que usa el servicio con cuentas:
una sola implementación, un solo sitio donde corregir un fallo de parseo.
"""

from job_tracker.application.search.parsing import MAX_OFFERS, extract_offer_dicts

__all__ = ["MAX_OFFERS", "extract_offer_dicts"]
