from __future__ import annotations

from dataclasses import dataclass


WEB_STATUS_PREPARABLE = "PREPARABLE"
WEB_STATUS_NEEDS_INFO = "NEEDS_INFO"
WEB_STATUS_REQUIRES_LOGIN = "REQUIRES_LOGIN"
WEB_STATUS_REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"
WEB_STATUS_BLOCKED = "BLOCKED"
WEB_STATUS_NOT_SUPPORTED = "NOT_SUPPORTED"
WEB_STATUS_UNKNOWN = "UNKNOWN"

BLOCKED_KEYWORDS = (
    "pagar",
    "pago",
    "tarjeta",
    "checkout",
    "transferencia",
    "payment",
    "aceptar términos",
    "aceptar terminos",
    "aceptar contrato",
    "firmar",
    "firma legal",
    "contraseña",
    "contrasena",
    "password",
    "cambiar permisos",
    "borrar cuenta",
    "eliminar cuenta",
    "delete account",
    "delete data",
    "enviar declaración",
    "enviar declaracion",
    "presentar declaración",
    "presentar declaracion",
    "submit tax",
)
NOT_SUPPORTED_KEYWORDS = (
    "scraping",
    "scrape",
    "crawler",
    "crawl",
    "captcha",
    "2fa",
    "descarga masiva",
    "bulk download",
    "monitorear en tiempo real",
)
LOGIN_KEYWORDS = (
    "entrar a mi cuenta",
    "iniciar sesión",
    "iniciar sesion",
    "login",
    "usuario",
    "contraseña",
    "contrasena",
    "portal privado",
    "cuenta",
    "acceso",
)
CONFIRMATION_KEYWORDS = (
    "enviar formulario",
    "mandar formulario",
    "submit",
    "sacar cita",
    "sacar una cita",
    "agendar cita",
    "agendar una cita",
    "reservar",
    "actualizar datos",
    "cambiar datos",
    "crear registro",
    "mandar solicitud",
)
NEEDS_INFO_KEYWORDS = (
    "trámite",
    "tramite",
    "portal",
    "formulario",
    "web",
    "página",
    "pagina",
    "sitio",
    "cita",
    "verificación",
    "verificacion",
    "gobierno",
    "servicio",
    "recibo",
)
PREPARABLE_KEYWORDS = (
    "preparar",
    "checklist",
    "requisitos",
    "documentos necesarios",
    "qué necesito",
    "que necesito",
    "pasos",
    "revisar antes",
)
SPECIFICITY_KEYWORDS = (
    "portal",
    "institución",
    "institucion",
    "verificación",
    "verificacion",
    "cita",
    "formulario",
    "trámite",
    "tramite",
    "telmex",
    "gobierno",
    "servicio",
)


@dataclass(frozen=True, slots=True)
class WebPreflightResult:
    status: str
    missing_info: tuple[str, ...]
    blocked_reason: str | None = None


def classify_web_preflight(text: str) -> WebPreflightResult:
    normalized = text.strip().lstrip("¿").strip().lower()

    if _contains_any(normalized, BLOCKED_KEYWORDS):
        return WebPreflightResult(
            status=WEB_STATUS_BLOCKED,
            missing_info=(),
            blocked_reason="La tarea incluye una acción bloqueada: pago, aceptación legal, credenciales o una acción vinculante.",
        )

    if _contains_any(normalized, NOT_SUPPORTED_KEYWORDS):
        return WebPreflightResult(status=WEB_STATUS_NOT_SUPPORTED, missing_info=())

    if _contains_any(normalized, LOGIN_KEYWORDS):
        return WebPreflightResult(status=WEB_STATUS_REQUIRES_LOGIN, missing_info=_build_missing_info(normalized))

    if _contains_any(normalized, CONFIRMATION_KEYWORDS):
        return WebPreflightResult(status=WEB_STATUS_REQUIRES_CONFIRMATION, missing_info=_build_missing_info(normalized))

    if _contains_any(normalized, PREPARABLE_KEYWORDS):
        if _contains_any(normalized, SPECIFICITY_KEYWORDS):
            return WebPreflightResult(status=WEB_STATUS_PREPARABLE, missing_info=_build_missing_info(normalized))
        return WebPreflightResult(status=WEB_STATUS_NEEDS_INFO, missing_info=_build_missing_info(normalized))

    if _contains_any(normalized, NEEDS_INFO_KEYWORDS):
        if _contains_any(normalized, SPECIFICITY_KEYWORDS):
            return WebPreflightResult(status=WEB_STATUS_NEEDS_INFO, missing_info=_build_missing_info(normalized))
        return WebPreflightResult(status=WEB_STATUS_NEEDS_INFO, missing_info=_build_missing_info(normalized))

    return WebPreflightResult(status=WEB_STATUS_UNKNOWN, missing_info=())


def _build_missing_info(normalized: str) -> tuple[str, ...]:
    missing: list[str] = []
    if "portal" not in normalized and "institución" not in normalized and "institucion" not in normalized:
        missing.append("¿Cuál es el portal o institución?")
    if not _contains_any(normalized, ("trámite", "tramite", "cita", "formulario", "verificación", "verificacion", "recibo")):
        missing.append("¿Qué trámite quieres hacer?")
    if not _contains_any(normalized, LOGIN_KEYWORDS):
        missing.append("¿Hay login?")
    if "pago" not in normalized and "pagar" not in normalized and "payment" not in normalized:
        missing.append("¿Hay pago?")
    if "términos" not in normalized and "terminos" not in normalized and "contrato" not in normalized:
        missing.append("¿Hay aceptación de términos?")
    if not _contains_any(normalized, ("sacar cita", "agendar cita", "submit", "enviar formulario", "actualizar datos", "crear registro")):
        missing.append("¿El resultado final crea una cita, envía un formulario o cambia un registro?")
    return tuple(missing)


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)
