from __future__ import annotations

from dataclasses import dataclass


STATUS_AVAILABLE_READ_ONLY = "AVAILABLE_READ_ONLY"
STATUS_AVAILABLE_DRAFT_ONLY = "AVAILABLE_DRAFT_ONLY"
STATUS_NEEDS_APPROVAL = "NEEDS_APPROVAL"
STATUS_PLANNED = "PLANNED"
STATUS_BLOCKED = "BLOCKED"
STATUS_AGENTIUS_CANDIDATE = "AGENTIUS_CANDIDATE"
STATUS_UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class Capability:
    capability_id: str
    display_name: str
    status: str
    package: str
    description: str
    boundary_label: str = ""
    boundary_summary: str = ""
    commands: tuple[str, ...] = ()
    allowed_actions: tuple[str, ...] = ()
    blocked_actions: tuple[str, ...] = ()


def load_capability_catalog() -> list[Capability]:
    return [
        Capability(
            capability_id="attention_summary",
            display_name="Qué se me pasó",
            status=STATUS_AVAILABLE_READ_ONLY,
            package="core",
            description="Muestra cosas que necesitan atención usando solo estado local.",
            boundary_label="Solo lectura local",
            boundary_summary="Solo lee información local ya registrada. No revisa servicios externos ni cambia nada por ti.",
            commands=("qué se me pasó", "what did i miss", "qué necesita mi atención"),
            allowed_actions=("READ_LOCAL_STATE", "SUMMARIZE_LOCAL_STATE"),
            blocked_actions=("CONNECTOR_ACCESS", "LIVE_RETRIEVAL", "PAYMENT_EXECUTION"),
        ),
        Capability(
            capability_id="robot_folder",
            display_name="Mi información importante",
            status=STATUS_AVAILABLE_READ_ONLY,
            package="core",
            description="Muestra lo que Robbie sabe o tiene pendiente usando memoria y estado local.",
            boundary_label="Solo lectura local",
            boundary_summary="Solo lee información local ya registrada. No revisa servicios externos ni cambia nada por ti.",
            commands=("mi información importante", "lo que robbie sabe", "robot folder", "what does robbie know"),
            allowed_actions=("READ_LOCAL_STATE", "GROUP_LOCAL_STATE"),
            blocked_actions=("MEMORY_MUTATION", "CONNECTOR_ACCESS", "LIVE_RETRIEVAL"),
        ),
        Capability(
            capability_id="approved_memory",
            display_name="Memoria aprobada",
            status=STATUS_NEEDS_APPROVAL,
            package="core",
            description="Robbie puede proponer memorias y tú decides si se guardan.",
            boundary_label="Requiere aprobación",
            boundary_summary="Puede preparar o proponer información, pero requiere aprobación explícita antes de guardar o cambiar algo.",
            allowed_actions=("PROPOSE_MEMORY", "APPROVE_MEMORY_IF_EXISTING_FLOW"),
            blocked_actions=("AUTO_STORE_RAW_DATA", "AUTO_APPROVE_MEMORY"),
        ),
        Capability(
            capability_id="document_review_text",
            display_name="Revisión de documentos desde texto",
            status=STATUS_AVAILABLE_DRAFT_ONLY,
            package="core",
            description="Robbie puede preparar una revisión o resumen usando texto explícito que ya le compartas.",
            boundary_label="Borrador / preparación",
            boundary_summary="Prepara un borrador o lista para que tú lo revises. No compra, no envía y no ejecuta acciones externas.",
            allowed_actions=("DRAFT_REVIEW", "SUMMARIZE_TEXT"),
            blocked_actions=("FILE_DOWNLOAD", "OCR", "PARSING", "CONNECTOR_ACCESS"),
        ),
        Capability(
            capability_id="documents_local",
            display_name="Documentos y archivos registrados",
            status=STATUS_AVAILABLE_READ_ONLY,
            package="core",
            description="Robbie puede mostrar información local registrada sobre archivos o documentos ya conocidos.",
            boundary_label="Solo lectura local",
            boundary_summary="Solo lee información local ya registrada. No revisa servicios externos ni cambia nada por ti.",
            allowed_actions=("READ_FILE_METADATA", "READ_DOCUMENT_METADATA"),
            blocked_actions=("FILE_DOWNLOAD", "OCR", "PARSING", "CONNECTOR_ACCESS"),
        ),
        Capability(
            capability_id="usage_budget_status",
            display_name="Uso y presupuesto local",
            status=STATUS_AVAILABLE_READ_ONLY,
            package="core",
            description="Robbie puede mostrar uso local estimado y estado de presupuesto.",
            boundary_label="Solo lectura local",
            boundary_summary="Solo lee información local ya registrada. No revisa servicios externos ni cambia nada por ti.",
            allowed_actions=("READ_LOCAL_USAGE", "READ_LOCAL_BUDGET"),
            blocked_actions=("LIVE_BILLING", "PAYMENT_EXECUTION"),
        ),
        Capability(
            capability_id="retrieval_control",
            display_name="Control de retrieval",
            status=STATUS_AVAILABLE_READ_ONLY,
            package="core",
            description="Robbie puede mostrar el estado y controles locales de retrieval, que sigue deshabilitado.",
            boundary_label="Solo lectura local",
            boundary_summary="Solo lee información local ya registrada. No revisa servicios externos ni cambia nada por ti.",
            allowed_actions=("READ_LOCAL_CONTROL_STATE",),
            blocked_actions=("LIVE_RETRIEVAL", "FILE_DOWNLOAD", "OCR", "PARSING"),
        ),
        Capability(
            capability_id="super_familiar",
            display_name="Súper Familiar",
            status=STATUS_AVAILABLE_DRAFT_ONLY,
            package="core",
            description="Prepara una vista local de súper familiar con datos conocidos, faltantes y límites. No compra, no crea carrito y no paga.",
            boundary_label="Borrador / preparación",
            boundary_summary="Prepara un borrador o lista para que tú lo revises. No compra, no envía y no ejecuta acciones externas.",
            commands=("súper familiar", "super familiar", "preparar súper familiar", "preparar super familiar", "lista del súper familiar", "lista del super familiar", "family groceries"),
            allowed_actions=("READ_LOCAL_STATE", "PREPARE_LOCAL_GROCERY_BRIEF"),
            blocked_actions=(
                "BROWSER_AUTOMATION",
                "CART_CREATION",
                "CHECKOUT_SUBMISSION",
                "PAYMENT_EXECUTION",
                "LEGAL_ACCEPTANCE",
                "EXTERNAL_ORDER_PLACEMENT",
            ),
        ),
        Capability(
            capability_id="action_approval_packets",
            display_name="Action Approval Packets",
            status=STATUS_AVAILABLE_DRAFT_ONLY,
            package="core",
            description="Prepara paquetes locales de aprobación para revisar qué requeriría confirmación antes de una acción futura.",
            boundary_label="Paquete de aprobación",
            boundary_summary="Prepara un paquete de aprobación para que tú decidas. Crear el paquete no ejecuta la acción.",
            commands=(
                "preparar aprobación",
                "preparar aprobacion",
                "paquete de aprobación",
                "paquete de aprobacion",
                "revisar acción",
                "revisar accion",
                "qué tendría que aprobar",
                "que tendría que aprobar",
                "approval packet",
                "prepare approval",
            ),
            allowed_actions=("CLASSIFY_ACTION_REQUEST", "PREPARE_APPROVAL_PACKET"),
            blocked_actions=(
                "EXTERNAL_EXECUTION",
                "SEND_EXTERNAL_MESSAGE",
                "PAYMENT_EXECUTION",
                "CHECKOUT_SUBMISSION",
                "BROWSER_AUTOMATION",
                "CONNECTOR_ACCESS",
            ),
        ),
        Capability(
            capability_id="web_workflow_preflight",
            display_name="Web Workflow Preflight",
            status=STATUS_AVAILABLE_DRAFT_ONLY,
            package="core",
            description=(
                "Evalúa localmente si una tarea web puede prepararse, qué datos faltan y qué acciones están bloqueadas. "
                "No abre navegador, no usa Webwright y no envía formularios."
            ),
            boundary_label="Preflight / revisión previa",
            boundary_summary="Revisa si una tarea web parece preparable o bloqueada. No abre sitios, no inicia sesión y no envía formularios.",
            commands=(
                "preflight web",
                "revisar tarea web",
                "evaluar trámite web",
                "evaluar tramite web",
                "puedes hacer este trámite",
                "puedes hacer este tramite",
                "web workflow preflight",
                "check web workflow",
            ),
            allowed_actions=("CLASSIFY_LOCAL_WEB_REQUEST", "PREPARE_LOCAL_CHECKLIST"),
            blocked_actions=(
                "BROWSER_AUTOMATION",
                "WEBWRIGHT_EXECUTION",
                "PLAYWRIGHT_EXECUTION",
                "LOGIN_EXECUTION",
                "FORM_SUBMISSION",
                "PAYMENT_EXECUTION",
                "LEGAL_ACCEPTANCE",
                "CREDENTIAL_CHANGE",
                "DESTRUCTIVE_ACTION",
                "EXTERNAL_RECORD_UPDATE",
            ),
        ),
        Capability(
            capability_id="skill_activation",
            display_name="Skill activation",
            status=STATUS_PLANNED,
            package="planned",
            description="Futuro flujo para activar habilidades con límites claros.",
            boundary_label="Planeado",
            boundary_summary="Planeado para una etapa futura. No está activo como capacidad runtime hoy.",
        ),
        Capability(
            capability_id="connectors",
            display_name="Connectors",
            status=STATUS_PLANNED,
            package="planned",
            description="Futuro soporte para fuentes externas autorizadas.",
            boundary_label="Planeado",
            boundary_summary="Planeado para una etapa futura. No está activo como capacidad runtime hoy.",
            blocked_actions=("LIVE_CONNECTOR_ACCESS",),
        ),
        Capability(
            capability_id="blocked_sensitive_actions",
            display_name="Acciones sensibles bloqueadas",
            status=STATUS_BLOCKED,
            package="safety",
            description="Pagos, aceptación legal, credenciales y acciones destructivas están bloqueadas.",
            boundary_label="Bloqueado",
            boundary_summary="Bloqueado por política actual. Robbie no ejecuta esta acción.",
            blocked_actions=("PAYMENT_EXECUTION", "LEGAL_ACCEPTANCE", "CREDENTIAL_CHANGE", "DESTRUCTIVE_ACTION"),
        ),
    ]
