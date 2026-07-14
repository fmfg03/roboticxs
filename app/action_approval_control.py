from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


APPROVAL_PACKET_COMMANDS = {
    "preparar aprobación",
    "preparar aprobacion",
    "paquete de aprobación",
    "paquete de aprobacion",
    "revisar acción",
    "revisar accion",
    "qué tendría que aprobar",
    "que tendría que aprobar",
    "qué tendria que aprobar",
    "que tendria que aprobar",
    "approval packet",
    "prepare approval",
}

APPROVAL_PACKET_PREFIX_PATTERNS = (
    re.compile(r"^(preparar aprobaci[oó]n)\s+para\s+(.+)$", re.IGNORECASE),
    re.compile(r"^(paquete de aprobaci[oó]n)\s+para\s+(.+)$", re.IGNORECASE),
    re.compile(r"^(revisar acci[oó]n)\s+(.+)$", re.IGNORECASE),
    re.compile(r"^(qu[eé]\s+tendr[ií]a\s+que\s+aprobar)\s+para\s+(.+)$", re.IGNORECASE),
    re.compile(r"^(approval packet)\s+for\s+(.+)$", re.IGNORECASE),
    re.compile(r"^(prepare approval)\s+for\s+(.+)$", re.IGNORECASE),
)


class ActionClass(str, Enum):
    READ_ONLY = "READ_ONLY"
    DRAFT_ONLY = "DRAFT_ONLY"
    PREPARE_ONLY = "PREPARE_ONLY"
    SEND_EXTERNAL_MESSAGE = "SEND_EXTERNAL_MESSAGE"
    UPDATE_EXTERNAL_RECORD = "UPDATE_EXTERNAL_RECORD"
    SCHEDULE_EXTERNAL_EVENT = "SCHEDULE_EXTERNAL_EVENT"
    CHECKOUT_PREPARATION_NO_PAYMENT = "CHECKOUT_PREPARATION_NO_PAYMENT"
    PAYMENT_MANUAL_PREPARATION = "PAYMENT_MANUAL_PREPARATION"
    PAYMENT_EXECUTION_REQUEST = "PAYMENT_EXECUTION_REQUEST"
    LEGAL_OR_PROFESSIONAL_DECISION = "LEGAL_OR_PROFESSIONAL_DECISION"
    CREDENTIAL_OR_PERMISSION_CHANGE = "CREDENTIAL_OR_PERMISSION_CHANGE"
    DESTRUCTIVE_ACTION = "DESTRUCTIVE_ACTION"
    UNKNOWN = "UNKNOWN"


class ApprovalDecision(str, Enum):
    LOCAL_PREPARATION_ONLY = "LOCAL_PREPARATION_ONLY"
    USER_CONFIRMATION_REQUIRED_LATER = "USER_CONFIRMATION_REQUIRED_LATER"
    BLOCKED = "BLOCKED"
    NEEDS_MORE_INFORMATION = "NEEDS_MORE_INFORMATION"
    NOT_SUPPORTED = "NOT_SUPPORTED"


@dataclass(frozen=True, slots=True)
class ParsedApprovalCommand:
    source_command: str
    requested_task: str


@dataclass(frozen=True, slots=True)
class ActionApprovalPacket:
    packet_id: str
    user_id: str
    robot_id: str
    source_command: str
    requested_task: str
    action_class: ActionClass
    approval_decision: ApprovalDecision
    summary: str
    missing_information: list[str]
    user_must_confirm: list[str]
    robot_can_prepare: list[str]
    robot_must_not_do: list[str]
    blocked_reason: str | None
    safe_next_step: str


PAYMENT_EXECUTION_KEYWORDS = (
    "pagar",
    "paga",
    "pay ",
    "pay my",
    "charge my card",
    "ejecuta el pago",
)
MANUAL_PAYMENT_KEYWORDS = (
    "manualmente",
    "checklist",
    "preparar checklist",
    "prepare manual payment checklist",
    "payment checklist only",
    "para que yo pague",
    "pagar yo",
    "pague yo",
)
CHECKOUT_KEYWORDS = (
    "carrito",
    "checkout review",
    "review without payment",
    "sin pagar",
    "grocery order for review",
    "comprar el súper familiar",
    "comprar el super familiar",
)
SEND_MESSAGE_KEYWORDS = (
    "mandar correo",
    "enviar correo",
    "enviar mensaje",
    "send email",
    "send message",
)
SCHEDULE_KEYWORDS = (
    "agendar",
    "reservar cita",
    "book appointment",
    "schedule appointment",
    "sacar cita",
)
UPDATE_RECORD_KEYWORDS = (
    "actualizar",
    "cambiar dirección",
    "cambiar direccion",
    "update customer record",
    "change account information",
    "crm",
)
LEGAL_PROFESSIONAL_KEYWORDS = (
    "aceptar contrato",
    "accept legal terms",
    "decide si firmo",
    "approve tax filing",
    "diagnose patient",
    "diagnosticar paciente",
    "declaración fiscal",
    "declaracion fiscal",
    "fire employee",
)
CREDENTIAL_PERMISSION_KEYWORDS = (
    "cambia mi contraseña",
    "cambia mi contrasena",
    "cambiar mi contraseña",
    "cambiar mi contrasena",
    "change password",
    "dale acceso admin",
    "grant admin access",
    "cambiar permisos",
    "quita permisos",
    "change payment method",
    "change bank account",
    "vendor bank change",
)
DESTRUCTIVE_KEYWORDS = (
    "borra mi cuenta",
    "borrar mi cuenta",
    "delete account",
    "delete all files",
    "delete all records",
    "elimina todos los archivos",
    "cancel service permanently",
)
VAGUE_TASK_KEYWORDS = ("eso", "that", "acción pendiente", "accion pendiente")


def is_action_approval_command(text: str) -> bool:
    return text.strip().lower() in APPROVAL_PACKET_COMMANDS


def parse_action_approval_command(text: str) -> ParsedApprovalCommand | None:
    normalized = text.strip()
    lowered = normalized.lower()
    if lowered in APPROVAL_PACKET_COMMANDS:
        return ParsedApprovalCommand(source_command=normalized, requested_task="")
    for pattern in APPROVAL_PACKET_PREFIX_PATTERNS:
        match = pattern.match(normalized)
        if match is None:
            continue
        return ParsedApprovalCommand(source_command=match.group(1), requested_task=match.group(2).strip())
    return None


def build_action_approval_packet(
    *,
    packet_id: str,
    user_id: str,
    robot_id: str,
    source_command: str,
    requested_task: str,
) -> ActionApprovalPacket:
    normalized = requested_task.strip().lower()

    if not normalized or normalized in VAGUE_TASK_KEYWORDS:
        return ActionApprovalPacket(
            packet_id=packet_id,
            user_id=user_id,
            robot_id=robot_id,
            source_command=source_command,
            requested_task=requested_task or "No especificada",
            action_class=ActionClass.UNKNOWN,
            approval_decision=ApprovalDecision.NEEDS_MORE_INFORMATION,
            summary="Necesito más información antes de preparar el paquete.",
            missing_information=[
                "Qué tipo de tarea es.",
                "Qué sistema, persona o proveedor está involucrado.",
                "Qué resultado quieres lograr.",
                "Si quieres solo preparación o una acción externa futura.",
            ],
            user_must_confirm=[],
            robot_can_prepare=["Aclarar el objetivo y armar una checklist local."],
            robot_must_not_do=["Inventar contexto o asumir el sistema objetivo."],
            blocked_reason=None,
            safe_next_step="Describe la tarea, el objetivo y el sistema o persona involucrada.",
        )

    if _contains_any(normalized, LEGAL_PROFESSIONAL_KEYWORDS):
        return _blocked_packet(
            packet_id=packet_id,
            user_id=user_id,
            robot_id=robot_id,
            source_command=source_command,
            requested_task=requested_task,
            action_class=ActionClass.LEGAL_OR_PROFESSIONAL_DECISION,
            blocked_reason="Esta tarea implica una decisión legal o profesional que Robbie no puede tomar.",
            robot_can_prepare=[
                "Organizar preguntas o puntos a revisar manualmente.",
                "Preparar una checklist no profesional si compartes el contexto de forma segura.",
            ],
            robot_must_not_do=[
                "No puedo decidir si aceptas, firmas o presentas algo.",
                "No doy consejo legal, fiscal, médico, financiero ni laboral.",
            ],
            safe_next_step="Dime qué parte quieres revisar manualmente y preparo una checklist local.",
        )

    if _contains_any(normalized, CREDENTIAL_PERMISSION_KEYWORDS):
        return _blocked_packet(
            packet_id=packet_id,
            user_id=user_id,
            robot_id=robot_id,
            source_command=source_command,
            requested_task=requested_task,
            action_class=ActionClass.CREDENTIAL_OR_PERMISSION_CHANGE,
            blocked_reason="Esta tarea cambiaría credenciales, permisos o configuración sensible.",
            robot_can_prepare=["Preparar una checklist manual de verificación previa."],
            robot_must_not_do=[
                "No puedo cambiar contraseñas, permisos ni métodos de pago.",
                "No puedo modificar cuentas o accesos sensibles.",
            ],
            safe_next_step="Si quieres, dime qué cambio manual piensas hacer y preparo una checklist local de verificación.",
        )

    if _contains_any(normalized, DESTRUCTIVE_KEYWORDS):
        return _blocked_packet(
            packet_id=packet_id,
            user_id=user_id,
            robot_id=robot_id,
            source_command=source_command,
            requested_task=requested_task,
            action_class=ActionClass.DESTRUCTIVE_ACTION,
            blocked_reason="Esta tarea es destructiva y está bloqueada por los límites del robot.",
            robot_can_prepare=["Preparar una checklist manual de riesgos y verificación previa."],
            robot_must_not_do=[
                "No puedo borrar cuentas, archivos o registros.",
                "No puedo iniciar eliminaciones permanentes.",
            ],
            safe_next_step="Si quieres, dime qué quieres revisar antes de hacerlo manualmente y preparo una checklist segura.",
        )

    if _contains_any(normalized, CHECKOUT_KEYWORDS):
        return ActionApprovalPacket(
            packet_id=packet_id,
            user_id=user_id,
            robot_id=robot_id,
            source_command=source_command,
            requested_task=requested_task,
            action_class=ActionClass.CHECKOUT_PREPARATION_NO_PAYMENT,
            approval_decision=ApprovalDecision.USER_CONFIRMATION_REQUIRED_LATER,
            summary="Preparación de revisión de carrito o pedido, sin checkout ni pago.",
            missing_information=["Tienda objetivo.", "Artículos finales.", "Sustituciones permitidas.", "Ventana de entrega preferida."],
            user_must_confirm=[
                "Artículos finales y sustituciones.",
                "Tienda y ventana de entrega.",
                "Que cualquier pago seguirá fuera de Stage 32P.",
            ],
            robot_can_prepare=[
                "Resumen local de lista o carrito para revisión.",
                "Checklist de confirmaciones antes de un checkout futuro.",
            ],
            robot_must_not_do=[
                "No puedo crear checkout ni colocar pedidos.",
                "No puedo ejecutar pagos.",
            ],
            blocked_reason=None,
            safe_next_step="Dime la tienda, los artículos y las sustituciones para preparar el paquete de revisión.",
        )

    if _contains_any(normalized, MANUAL_PAYMENT_KEYWORDS):
        return ActionApprovalPacket(
            packet_id=packet_id,
            user_id=user_id,
            robot_id=robot_id,
            source_command=source_command,
            requested_task=requested_task,
            action_class=ActionClass.PAYMENT_MANUAL_PREPARATION,
            approval_decision=ApprovalDecision.LOCAL_PREPARATION_ONLY,
            summary="Preparación local para pago manual solamente.",
            missing_information=["Monto actual.", "Fecha límite.", "Servicio o cuenta a pagar."],
            user_must_confirm=["Que tú harás el pago manualmente.", "Que el monto y la cuenta son correctos."],
            robot_can_prepare=[
                "Checklist de pago manual.",
                "Resumen local de datos que necesitas verificar antes de pagar.",
            ],
            robot_must_not_do=[
                "No voy a ejecutar pagos ni abrir una sesión de cobro.",
                "No puedo guardar datos de tarjeta o CVV.",
            ],
            blocked_reason=None,
            safe_next_step="Compárteme el monto, la fecha límite y el servicio para preparar la checklist manual.",
        )

    if _contains_any(normalized, PAYMENT_EXECUTION_KEYWORDS):
        return _blocked_packet(
            packet_id=packet_id,
            user_id=user_id,
            robot_id=robot_id,
            source_command=source_command,
            requested_task=requested_task,
            action_class=ActionClass.PAYMENT_EXECUTION_REQUEST,
            blocked_reason="No puedo ejecutar pagos ni iniciar cargos.",
            robot_can_prepare=[
                "Checklist de datos necesarios para revisar el pago manualmente.",
                "Revisión del monto si ya existe información local o la compartes explícitamente.",
            ],
            robot_must_not_do=[
                "No puedo ejecutar pagos ni enviar cargos.",
                "No puedo guardar datos de tarjeta o CVV.",
            ],
            safe_next_step="Dime el monto y la fecha límite, o pega la información del recibo para preparar una checklist manual.",
        )

    if _contains_any(normalized, SEND_MESSAGE_KEYWORDS):
        return ActionApprovalPacket(
            packet_id=packet_id,
            user_id=user_id,
            robot_id=robot_id,
            source_command=source_command,
            requested_task=requested_task,
            action_class=ActionClass.SEND_EXTERNAL_MESSAGE,
            approval_decision=ApprovalDecision.USER_CONFIRMATION_REQUIRED_LATER,
            summary="Preparación de mensaje o correo para revisión posterior.",
            missing_information=["Destinatario exacto.", "Canal.", "Contenido o intención del mensaje.", "Adjuntos o timing si aplica."],
            user_must_confirm=["Destinatario final.", "Contenido final.", "Adjuntos y momento de envío."],
            robot_can_prepare=["Borrador del mensaje.", "Checklist de revisión antes de un envío futuro."],
            robot_must_not_do=[
                "No voy a enviar correos ni mensajes.",
                "No voy a usar canales externos.",
            ],
            blocked_reason=None,
            safe_next_step="Dime el destinatario y el objetivo del mensaje para preparar el borrador o la checklist.",
        )

    if _contains_any(normalized, SCHEDULE_KEYWORDS):
        return ActionApprovalPacket(
            packet_id=packet_id,
            user_id=user_id,
            robot_id=robot_id,
            source_command=source_command,
            requested_task=requested_task,
            action_class=ActionClass.SCHEDULE_EXTERNAL_EVENT,
            approval_decision=ApprovalDecision.USER_CONFIRMATION_REQUIRED_LATER,
            summary="Preparación de cita o evento externo para revisión posterior.",
            missing_information=["Portal o institución.", "Ubicación.", "Fechas u horarios preferidos.", "Datos de identidad o vehículo si aplican."],
            user_must_confirm=["Fecha y hora final.", "Ubicación o portal.", "Datos que se enviarían en la solicitud."],
            robot_can_prepare=["Checklist de requisitos.", "Resumen de datos faltantes antes de una cita futura."],
            robot_must_not_do=[
                "No voy a reservar ni agendar citas.",
                "No voy a enviar formularios ni crear registros externos.",
            ],
            blocked_reason=None,
            safe_next_step="Dime portal, ubicación y fechas preferidas para preparar la checklist de la cita.",
        )

    if _contains_any(normalized, UPDATE_RECORD_KEYWORDS):
        return ActionApprovalPacket(
            packet_id=packet_id,
            user_id=user_id,
            robot_id=robot_id,
            source_command=source_command,
            requested_task=requested_task,
            action_class=ActionClass.UPDATE_EXTERNAL_RECORD,
            approval_decision=ApprovalDecision.USER_CONFIRMATION_REQUIRED_LATER,
            summary="Preparación de cambio externo para revisión posterior.",
            missing_information=["Sistema objetivo.", "Campo a cambiar.", "Valor actual.", "Nuevo valor exacto."],
            user_must_confirm=["Campo y valor final.", "Sistema donde se haría el cambio.", "Consecuencias del cambio."],
            robot_can_prepare=["Resumen del cambio propuesto.", "Checklist de validación antes de una actualización futura."],
            robot_must_not_do=[
                "No voy a actualizar sistemas externos.",
                "No voy a cambiar registros, cuentas o CRMs.",
            ],
            blocked_reason=None,
            safe_next_step="Dime el sistema, el campo y el valor deseado para preparar el paquete.",
        )

    return ActionApprovalPacket(
        packet_id=packet_id,
        user_id=user_id,
        robot_id=robot_id,
        source_command=source_command,
        requested_task=requested_task,
        action_class=ActionClass.UNKNOWN,
        approval_decision=ApprovalDecision.NEEDS_MORE_INFORMATION,
        summary="Necesito clasificar mejor la tarea antes de preparar el paquete.",
        missing_information=[
            "Qué tipo de acción quieres preparar.",
            "Qué sistema, persona o proveedor está involucrado.",
            "Qué resultado final quieres lograr.",
        ],
        user_must_confirm=[],
        robot_can_prepare=["Aclarar el objetivo y armar una checklist local."],
        robot_must_not_do=["No voy a asumir la acción externa ni inventar contexto."],
        blocked_reason=None,
        safe_next_step="Describe la tarea con más detalle para preparar el paquete de aprobación.",
    )


def _blocked_packet(
    *,
    packet_id: str,
    user_id: str,
    robot_id: str,
    source_command: str,
    requested_task: str,
    action_class: ActionClass,
    blocked_reason: str,
    robot_can_prepare: list[str],
    robot_must_not_do: list[str],
    safe_next_step: str,
) -> ActionApprovalPacket:
    return ActionApprovalPacket(
        packet_id=packet_id,
        user_id=user_id,
        robot_id=robot_id,
        source_command=source_command,
        requested_task=requested_task,
        action_class=action_class,
        approval_decision=ApprovalDecision.BLOCKED,
        summary="La acción está bloqueada en esta versión.",
        missing_information=[],
        user_must_confirm=[],
        robot_can_prepare=robot_can_prepare,
        robot_must_not_do=robot_must_not_do,
        blocked_reason=blocked_reason,
        safe_next_step=safe_next_step,
    )


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)
