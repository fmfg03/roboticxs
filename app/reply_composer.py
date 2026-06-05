from __future__ import annotations


def compose_reply_text(scope_decision: str, safety_result: dict[str, str]) -> str:
    if safety_result["decision"] in {"BLOCK", "ASK_CONFIRMATION", "ESCALATE"}:
        return safety_result["user_message"]
    if scope_decision == "CLARIFY":
        return "I can help with meeting prep, summaries, reminders, and drafting. Tell me the concrete task you want your robot to handle."
    return safety_result["user_message"]


def compose_reply_text_with_memory(scope_decision: str, safety_result: dict[str, str], memory_context_summary: str) -> str:
    base = compose_reply_text(scope_decision, safety_result)
    if not memory_context_summary or safety_result["decision"] in {"BLOCK", "ASK_CONFIRMATION", "ESCALATE"}:
        return base
    return f"{base} I used your saved {memory_context_summary} as context for this reply."


def compose_memory_proposal_reply(*, label: str, content: str) -> str:
    return f"I can remember this:\n\n{label}: {content}\n\nReply APPROVE to save it or REJECT to discard it."


def compose_upgrade_interest_proposal_reply(content: str) -> str:
    return (
        "Preparé una propuesta local de interés para que tú la apruebes o rechaces.\n\n"
        f"Interés local: {content}\n\n"
        "Si la apruebas, quedará visible para ti en la memoria local del robot y la podrás borrar después.\n"
        "No voy a crear un lead, avisar a nadie, hacer handoff, conectarlo a CRM, usar conectores, abrir navegador, mandar email o WhatsApp, ni tocar sistemas externos.\n\n"
        "Responde APPROVE para guardarla como memoria local, o REJECT para descartarla."
    )


def compose_memory_boundary_reply(content: str) -> str:
    return f"I can save this as a robot limit:\n\nBoundary: {content}\n\nReply APPROVE to save it or REJECT to discard it."


def compose_memory_approved_reply() -> str:
    return "Saved to your robot memory."


def compose_upgrade_interest_approved_reply() -> str:
    return (
        "Guardado como nota local de interés. Queda solo en la memoria local del robot; "
        "no crea lead, no avisa a nadie, no hace handoff, no toca CRM, no usa conectores, "
        "no abre navegador, no manda email o WhatsApp y no toca sistemas externos."
    )


def compose_memory_rejected_reply() -> str:
    return "Discarded. I will not remember that."


def compose_no_pending_memory_reply() -> str:
    return "There is no pending memory to approve or reject right now."


def compose_memory_list_reply(memories: list[dict[str, str]]) -> str:
    if not memories:
        return "I do not have any approved memories for your robot yet."
    lines = ["Here is what I currently remember:", ""]
    for index, memory in enumerate(memories, start=1):
        lines.append(f"{index}. [{memory['id']}] {memory['label']}: {memory['content']}")
    lines.extend(["", f"To remove one, reply: forget memory {memories[0]['id']}"])
    return "\n".join(lines)


def compose_memory_forgotten_reply() -> str:
    return "Forgotten. I will no longer use that memory."


def compose_memory_not_found_reply() -> str:
    return "I could not find that active memory for your robot."


def compose_memory_needs_clearer_framing_reply() -> str:
    return "I cannot save that as memory in its current form. Rephrase it as a safe preference, profile fact, or robot limit."


def compose_document_refusal_reply() -> str:
    return (
        "I can provide a draft summary or flag items for your review, but I cannot tell you whether to sign, "
        "certify a signature, or provide legal, tax, financial, medical, or professional advice."
    )


def compose_document_list_reply(documents: list[dict[str, str]]) -> str:
    if not documents:
        return "I do not have any retained document-review records for your robot."
    lines = ["Here are the retained document-review records for your robot:", ""]
    for index, document in enumerate(documents, start=1):
        lines.append(
            f"{index}. [{document['id']}] {document['review_type']} | {document['status']} | "
            f"{document['created_at']} | {document['preview']}"
        )
    lines.extend(["", f"To remove one, reply: forget document {documents[0]['id']}"])
    return "\n".join(lines)


def compose_document_forgotten_reply() -> str:
    return "Forgotten. I will no longer retain that document-review record as active history."


def compose_document_not_found_reply() -> str:
    return "I could not find that active document-review record for your robot."


def compose_usage_empty_reply(kind: str) -> str:
    if kind == "spend":
        return "I do not have prior usage records for this robot yet. This report uses local estimated logs only, not live billing."
    return "I do not have prior token usage records for this robot yet. This report uses local estimated logs only."


def compose_spend_summary_reply(summary) -> str:
    lines = [
        "Local estimated spend summary:",
        f"- Total estimated cost (USD): ${summary.total_estimated_cost_usd:.6f}",
        f"- Total input tokens: {summary.total_input_tokens}",
        f"- Total output tokens: {summary.total_output_tokens}",
        f"- Total usage events: {summary.total_usage_events}",
    ]
    if summary.provider_model_breakdown:
        lines.extend(["", "Provider/model breakdown:"])
        for item in summary.provider_model_breakdown:
            lines.append(
                f"- {item['provider']} / {item['model']}: {item['events']} events | "
                f"in {item['input_tokens']} | out {item['output_tokens']} | est ${item['estimated_cost_usd']:.6f}"
            )
    if summary.highest_cost_routes:
        lines.extend(["", "Highest-cost local routes:"])
        for item in summary.highest_cost_routes:
            lines.append(
                f"- {item['task_family']} / {item['task_class']} | {item['provider']} / {item['model']} | "
                f"task {item['task_id']} | est ${item['estimated_cost_usd']:.6f}"
            )
    lines.extend(["", "This is a local estimate from robot logs only, not live billing or provider reconciliation."])
    return "\n".join(lines)


def compose_token_usage_summary_reply(summary) -> str:
    lines = [
        "Local token usage summary:",
        f"- Total input tokens: {summary.total_input_tokens}",
        f"- Total output tokens: {summary.total_output_tokens}",
        f"- Total tokens: {summary.total_tokens}",
        f"- Total usage events: {summary.total_usage_events}",
    ]
    if summary.provider_model_breakdown:
        lines.extend(["", "Provider/model breakdown:"])
        for item in summary.provider_model_breakdown:
            lines.append(
                f"- {item['provider']} / {item['model']}: {item['events']} events | "
                f"in {item['input_tokens']} | out {item['output_tokens']}"
            )
    if summary.task_family_breakdown:
        lines.extend(["", "Flow family breakdown:"])
        for item in summary.task_family_breakdown:
            lines.append(f"- {item['task_family']}: {item['events']} events")
    if summary.task_class_breakdown:
        lines.extend(["", "Task class breakdown:"])
        for item in summary.task_class_breakdown:
            lines.append(f"- {item['task_class']}: {item['events']} events")
    lines.extend(["", "This is local usage data only, derived from estimated robot logs."])
    return "\n".join(lines)


def compose_budget_status_reply(*, posture) -> str:
    return (
        f"Budget status: {posture.status}. "
        f"Local budget limit: ${posture.budget_limit_usd:.6f}. "
        f"Warn threshold: {posture.warn_threshold_percent}%. "
        f"Block threshold: {posture.block_threshold_percent}%. "
        f"Current local estimated spend: ${posture.current_estimated_spend_usd:.6f}. "
        f"Remaining local estimated budget: ${posture.remaining_estimated_budget_usd:.6f}. "
        f"Usage: {posture.usage_percentage:.2f}%. "
        "This is based on local estimates only, not live billing or provider reconciliation."
    )


def compose_budget_warn_prefix(*, posture) -> str:
    return (
        f"Budget warning: {posture.status}. "
        f"You have used about {posture.usage_percentage:.2f}% of your local estimated budget for this robot. "
        f"This task would project local estimated spend to ${posture.projected_estimated_spend_usd:.6f}. "
        "This is based on local estimates only, not live billing.\n\n"
    )


def compose_budget_block_reply(*, posture) -> str:
    return (
        "I cannot continue this task because your local estimated budget threshold has been reached. "
        f"Current local estimated spend is ${posture.current_estimated_spend_usd:.6f} "
        f"against a local budget limit of ${posture.budget_limit_usd:.6f}. "
        "You can still ask: show budget status or what did you spend. "
        "This is based on local estimates only, not live billing or provider reconciliation."
    )


def compose_budget_limit_updated_reply(*, amount: float) -> str:
    return (
        f"Budget limit updated for this robot: ${amount:.6f} local estimated spend.\n"
        "This is a local guardrail only. It is not billing, payment, or provider account enforcement."
    )


def compose_budget_limit_invalid_reply() -> str:
    return "I could not set the budget limit. Use a positive amount such as: set budget limit 0.01 or set budget limit $0.01."


def compose_budget_warn_threshold_updated_reply(*, threshold_percent: int) -> str:
    return (
        f"Budget warn threshold updated for this robot: {threshold_percent}%.\n"
        "This is a local guardrail only. It is not billing, payment, or provider account enforcement."
    )


def compose_budget_warn_threshold_invalid_reply() -> str:
    return (
        "I could not set the budget warn threshold. Use a whole percent above 0 and below the current block threshold, "
        "such as: set budget warn threshold 70 or set budget warn threshold 70%."
    )


def compose_budget_block_threshold_updated_reply(*, threshold_percent: int) -> str:
    return (
        f"Budget block threshold updated for this robot: {threshold_percent}%.\n"
        "This is a local guardrail only. It is not billing, payment, or provider account enforcement."
    )


def compose_budget_block_threshold_invalid_reply() -> str:
    return (
        "I could not set the budget block threshold. Use a whole percent above 0, at most 100, and above the current warn "
        "threshold, such as: set budget block threshold 95 or set budget block threshold 95%."
    )


def compose_budget_policy_reset_reply() -> str:
    return (
        "Budget policy reset for this robot. It is now using the default local budget limit and default warn/block thresholds.\n"
        "This is a local guardrail only. It is not billing, payment, or provider account enforcement."
    )


def compose_file_retrieval_preflight_reply(*, request_kind: str, file_name: str) -> str:
    action = "retrieve" if request_kind == "RETRIEVE" else "prepare for review"
    return (
        f"I recorded your request to {action} {file_name}.\n\n"
        "File retrieval and content review are not enabled yet. I did not call Telegram getFile, did not download the file, parse it, OCR it, "
        "did not review it, or store file contents.\n\n"
        "This step only stored request/status metadata so your robot can track the preflight request."
    )


def compose_file_retrieval_not_found_reply() -> str:
    return "I could not find an active file metadata record with that ID for this robot."


def compose_pending_file_retrievals_reply(retrievals: list[dict[str, str]]) -> str:
    if not retrievals:
        return "I do not have any pending file retrieval requests for this robot."
    lines = ["Here are the pending file retrieval requests for this robot:", ""]
    for index, retrieval in enumerate(retrievals, start=1):
        lines.append(
            f"{index}. [{retrieval['id']}] {retrieval['request_kind']} | {retrieval['status']} | "
            f"{retrieval['file_name']} | {retrieval['created_at']}"
        )
    lines.extend(
        [
            "",
            "Retrieval is still not enabled. I have not called Telegram getFile, downloaded the file, parsed it, OCRed it, reviewed it, or stored file contents.",
            f"To cancel one, reply: cancel file retrieval {retrievals[0]['id']}",
        ]
    )
    return "\n".join(lines)


def compose_file_retrieval_cancelled_reply() -> str:
    return "Cancelled. I will no longer keep that file retrieval request pending."


def compose_file_retrieval_cancel_not_found_reply() -> str:
    return "I could not find a pending file retrieval request with that ID for this robot."


def compose_file_retrieval_policy_status_reply(*, status: str, reason_code: str) -> str:
    return (
        f"File retrieval status: {status.lower()}.\n"
        f"Reason: {reason_code}.\n\n"
        "Live retrieval is not active. Roboticxs will not call Telegram getFile, download files, parse PDFs, OCR content, "
        "store raw bytes, store extracted text, or claim the file was reviewed."
    )


def compose_file_retrieval_enablement_request_reply(*, reason_code: str) -> str:
    return (
        "I recorded your request for file retrieval enablement.\n"
        "Retrieval remains disabled.\n"
        f"Reason: {reason_code}.\n\n"
        "Roboticxs will not call Telegram getFile, download files, parse PDFs, OCR content, store raw bytes, "
        "store extracted text, or claim the file was reviewed."
    )


def compose_pending_file_retrieval_enablement_requests_reply(requests: list[dict[str, str]]) -> str:
    if not requests:
        return "I do not have any pending retrieval enablement requests for this robot."
    lines = ["Here are the pending retrieval enablement requests for this robot:", ""]
    for index, request in enumerate(requests, start=1):
        lines.append(
            f"{index}. [{request['id']}] {request['status']} | {request['reason_code']} | {request['created_at']}"
        )
    lines.extend(
        [
            "",
            "Retrieval remains disabled. Roboticxs will not call Telegram getFile, download files, parse PDFs, OCR content, store raw bytes, store extracted text, or claim the file was reviewed.",
            f"To approve one, reply: approve retrieval enablement request {requests[0]['id']}",
            f"To reject one, reply: reject retrieval enablement request {requests[0]['id']}",
        ]
    )
    return "\n".join(lines)


def compose_file_retrieval_enablement_request_history_reply(requests: list[dict[str, str]]) -> str:
    if not requests:
        return "I do not have any retrieval enablement request history for this robot."
    lines = ["Here is the retrieval enablement request history for this robot:", ""]
    for index, request in enumerate(requests, start=1):
        lines.append(
            f"{index}. [{request['id']}] {request['status']} | {request['reason_code']} | "
            f"created {request['created_at']} | updated {request['updated_at']}"
        )
    lines.extend(
        [
            "",
            "Retrieval remains disabled. Roboticxs will not call Telegram getFile, download files, parse PDFs, OCR content, store raw bytes, store extracted text, or claim the file was reviewed.",
        ]
    )
    return "\n".join(lines)


def compose_file_retrieval_control_summary_reply(
    *,
    policy_status: str,
    reason_code: str,
    pending_retrieval_intents_count: int,
    pending_enablement_requests_count: int,
    recent_enablement_request_outcomes: list[dict[str, str]],
) -> str:
    lines = [
        "Retrieval control summary:",
        f"- Retrieval policy: {policy_status}",
        f"- Reason: {reason_code}",
        f"- Pending file retrieval intents: {pending_retrieval_intents_count}",
        f"- Pending retrieval enablement requests: {pending_enablement_requests_count}",
    ]
    if recent_enablement_request_outcomes:
        lines.extend(["", "Recent retrieval enablement request outcomes:"])
        for item in recent_enablement_request_outcomes:
            lines.append(
                f"- [{item['id']}] {item['status']} | {item['reason_code']} | {item['updated_at']}"
            )
    lines.extend(
        [
            "",
            "Retrieval remains disabled. Roboticxs will not call Telegram getFile, download files, parse PDFs, OCR content, store raw bytes, store extracted text, or claim the file was reviewed.",
        ]
    )
    return "\n".join(lines)


def compose_file_retrieval_control_report_reply(
    *,
    policy_status: str,
    reason_code: str,
    pending_retrieval_intents_count: int,
    pending_enablement_requests_count: int,
    recent_enablement_request_outcomes: list[dict[str, str]],
) -> str:
    lines = [
        "Retrieval control report:",
        f"- Retrieval policy: {policy_status}",
        f"- Reason: {reason_code}",
        f"- Pending file retrieval intents: {pending_retrieval_intents_count}",
        f"- Pending retrieval enablement requests: {pending_enablement_requests_count}",
    ]
    if recent_enablement_request_outcomes:
        lines.extend(["", "Recent retrieval enablement request outcomes:"])
        for item in recent_enablement_request_outcomes:
            lines.append(
                f"- [{item['id']}] {item['status']} | {item['reason_code']} | {item['updated_at']}"
            )
    lines.extend(
        [
            "",
            "Retrieval remains disabled. Roboticxs will not call Telegram getFile, download files, parse PDFs, OCR content, store raw bytes, store extracted text, or claim the file was reviewed.",
        ]
    )
    return "\n".join(lines)


def compose_attention_summary_reply(findings: list[str]) -> str:
    if not findings:
        return (
            "No encontré nada pendiente con el estado local que Robbie conoce hoy.\n\n"
            "No revisé correo, WhatsApp, calendario, web ni archivos nuevos. "
            "Solo usé memoria, archivos registrados, reviews, presupuesto y estados locales ya persistidos."
        )

    lines = [f"Encontré {len(findings)} cosas que necesitan atención usando solo lo que Robbie ya conoce:", ""]
    for index, finding in enumerate(findings, start=1):
        lines.append(f"{index}. {finding}")
    lines.extend(
        [
            "",
            "No revisé correo, WhatsApp, calendario ni web en vivo.",
        ]
    )
    return "\n".join(lines)


def compose_robot_folder_reply(sections) -> str:
    lines = [
        "Mi información importante",
        "",
        "Esto es lo que Robbie conoce usando solo información local aprobada o pendiente:",
        "",
    ]
    for section in sections:
        lines.append(section.title)
        for item in section.items:
            lines.append(item)
        lines.append("")
    lines.append(
        "No revisé correo, WhatsApp, calendario, web ni archivos nuevos. Solo usé información local ya registrada."
    )
    return "\n".join(lines)


def compose_robot_folder_empty_reply() -> str:
    return (
        "Todavía no tengo información importante organizada para este robot.\n\n"
        "Puedo ir construyéndola cuando apruebes memorias, revises documentos o registres datos importantes.\n\n"
        "No revisé correo, WhatsApp, calendario, web ni archivos nuevos. Solo usé estado local ya persistido."
    )


def compose_capability_catalog_reply(catalog) -> str:
    available_now = [item for item in catalog if item.status == "AVAILABLE_READ_ONLY"]
    needs_approval = [item for item in catalog if item.status == "NEEDS_APPROVAL"]
    preparation_only = [item for item in catalog if item.status == "AVAILABLE_DRAFT_ONLY"]
    planned = [item for item in catalog if item.status == "PLANNED"]
    blocked = [item for item in catalog if item.status == "BLOCKED"]
    lines = ["Estas son las habilidades que Robbie tiene hoy:", ""]
    if available_now:
        lines.append("Disponible ahora")
        for index, item in enumerate(available_now, start=1):
            lines.append(_compose_capability_catalog_line(index=index, item=item))
        lines.append("")
    if needs_approval:
        lines.append("Necesita aprobación")
        for index, item in enumerate(needs_approval, start=1):
            lines.append(_compose_capability_catalog_line(index=index, item=item))
        lines.append("")
    if preparation_only:
        lines.append("Solo preparación / revisión previa")
        for index, item in enumerate(preparation_only, start=1):
            lines.append(_compose_capability_catalog_line(index=index, item=item))
        lines.append("")
    if planned:
        lines.append("Planeado / no activo todavía")
        for index, item in enumerate(planned, start=1):
            lines.append(_compose_capability_catalog_line(index=index, item=item))
        lines.append("")
    if blocked:
        lines.append("Bloqueado")
        for index, item in enumerate(blocked, start=1):
            lines.append(_compose_capability_catalog_line(index=index, item=item))
        lines.append("")
    lines.extend(
        [
            "Límites globales: Robbie no ejecuta pagos, compras, envíos, reservas, cambios externos, uso de credenciales, navegador, conectores ni decisiones legales, médicas, fiscales, financieras o laborales.",
            "",
            "No revisé correo, WhatsApp, calendario, web ni sistemas externos. Esta respuesta usa solo el catálogo local de Robbie.",
        ]
    )
    return "\n".join(lines)


def _compose_capability_catalog_line(*, index: int, item) -> str:
    base = f"• {item.display_name} — {item.description}"
    if item.boundary_label and item.boundary_summary:
        return f"{base}\n  Límite: {item.boundary_label}; {item.boundary_summary}"
    return base


def _capability_next_step_guidance(*, status: str, capability_id: str | None = None) -> str:
    if capability_id == "web_workflow_preflight":
        return (
            "Siguiente paso: dime la tarea y te diré qué datos faltan, qué está bloqueado y qué tendrías que aprobar manualmente."
        )
    if capability_id == "action_approval_packets":
        return (
            "Siguiente paso: dime la acción que quieres revisar y puedo preparar el paquete; tú decides antes de enviar, guardar o cambiar algo."
        )
    if capability_id == "blocked_sensitive_actions":
        return (
            "Siguiente paso: puedo ayudarte a preparar una lista, resumen o checklist para que tú lo hagas manualmente, si aplica."
        )

    if status == "AVAILABLE_READ_ONLY":
        return (
            "Siguiente paso: dime qué quieres revisar o preparar y trabajaré solo con información local ya registrada."
        )
    if status == "NEEDS_APPROVAL":
        return (
            "Siguiente paso: puedo preparar la propuesta o paquete; tú confirmas antes de guardar, enviar o cambiar algo."
        )
    if status == "AVAILABLE_DRAFT_ONLY":
        return (
            "Siguiente paso: dime la tarea y te diré qué datos faltan, qué está bloqueado y qué podrías aprobar manualmente."
        )
    if status == "PLANNED":
        return (
            "Siguiente paso: puedo explicarte el alcance previsto o revisar qué parte sí puede prepararse hoy con capacidades actuales."
        )
    if status == "BLOCKED":
        return (
            "Siguiente paso: puedo ayudarte a preparar una lista, resumen o checklist para que tú lo hagas manualmente, si aplica."
        )
    if status == "AGENTIUS_CANDIDATE":
        return (
            "Siguiente paso: si quieres, puedo ayudarte a reformularlo como tarea personal local, preparar un resumen manual o una checklist sin guardar, notificar ni tocar nada externo."
        )
    return "Siguiente paso: puedo ayudarte a reformular la tarea o revisar si encaja con una capacidad disponible."


def compose_capability_resolution_reply(*, resolution) -> str:
    if resolution.status == "AVAILABLE_READ_ONLY":
        if resolution.capability_id == "attention_summary":
            return (
                'Sí. Esa habilidad está disponible en modo lectura local.\n\n'
                "Límite: solo usa información local ya registrada. No revisa servicios externos ni cambia nada por ti.\n"
                'Siguiente paso: si quieres usarla ahora, escribe: "qué se me pasó".'
            )
        if resolution.capability_id == "robot_folder":
            return (
                'Sí. Esa habilidad está disponible en modo lectura local.\n\n'
                "Límite: solo usa información local ya registrada. No revisa servicios externos ni cambia nada por ti.\n"
                'Siguiente paso: si quieres usarla ahora, escribe: "mi información importante".'
            )
        return (
            "Sí. Esa habilidad está disponible en modo lectura local dentro del runtime actual de Robbie.\n\n"
            "Límite: solo usa información local ya registrada. No revisa servicios externos ni cambia nada por ti.\n"
            f"{_capability_next_step_guidance(status=resolution.status, capability_id=resolution.capability_id)}"
        )
    if resolution.status == "AVAILABLE_DRAFT_ONLY":
        if resolution.capability_id == "action_approval_packets":
            return (
                "Sí, puedo prepararte un paquete de aprobación.\n\n"
                "Límite: puedo mostrar qué se haría, qué falta y qué tendrías que confirmar después. No voy a ejecutar nada ni enviar nada.\n"
                f"{_capability_next_step_guidance(status=resolution.status, capability_id=resolution.capability_id)}"
            )
        if resolution.capability_id == "super_familiar":
            return (
                "Sí, puedo ayudarte en modo preparación.\n\n"
                "Límite: puedo organizar lo que ya sé localmente, mostrar lo que falta confirmar y recordarte los límites. Todavía no puedo entrar a Walmart, crear carrito, elegir horarios, pagar ni hacer pedidos.\n"
                f"{_capability_next_step_guidance(status=resolution.status, capability_id=resolution.capability_id)}"
            )
        return (
            "Sí, pero solo en modo borrador o preparación.\n\n"
            "Límite: puedo ayudarte a preparar texto, checklist o revisión local, pero no puedo enviar, publicar, pagar, actualizar sistemas externos ni ejecutar acciones fuera del runtime local.\n"
            f"{_capability_next_step_guidance(status=resolution.status, capability_id=resolution.capability_id)}"
        )
    if resolution.status == "NEEDS_APPROVAL":
        return (
            "Sí, pero esa capacidad necesita aprobación.\n\n"
            "Límite: Robbie puede proponerte memoria o contexto para guardar, y tú decides si se aprueba o no.\n"
            f"{_capability_next_step_guidance(status=resolution.status, capability_id=resolution.capability_id)}"
        )
    if resolution.status == "PLANNED":
        if resolution.capability_id == "super_familiar":
            return (
                "Todavía no como automatización.\n\n"
                "Límite: esa capacidad está planeada como “Súper Familiar”. En esta versión puedo ayudarte a organizar información local que ya exista, pero no puedo entrar a Walmart, armar un carrito, elegir horarios, pagar ni hacer pedidos.\n"
                f"{_capability_next_step_guidance(status=resolution.status, capability_id=resolution.capability_id)}"
            )
        if resolution.capability_id == "web_workflow_preflight":
            return (
                "Todavía no.\n\n"
                "Límite: esa capacidad está planeada como “Revisión previa de tareas web”. En esta versión Robbie no puede abrir portales, navegar la web, enviar formularios ni ejecutar tareas de navegador.\n"
                f"{_capability_next_step_guidance(status=resolution.status, capability_id=resolution.capability_id)}"
            )
        return (
            "Todavía no. Esa capacidad está planeada, pero Robbie aún no la tiene disponible en esta versión.\n\n"
            f"{_capability_next_step_guidance(status=resolution.status, capability_id=resolution.capability_id)}"
        )
    if resolution.status == "BLOCKED":
        return (
            "No. Esa acción está bloqueada.\n\n"
            "Límite: Robbie no puede ejecutar pagos, aceptar términos legales, cambiar credenciales ni hacer acciones destructivas.\n"
            f"{_capability_next_step_guidance(status=resolution.status, capability_id=resolution.capability_id)}"
        )
    if resolution.status == "AGENTIUS_CANDIDATE":
        return (
            "Eso suena más a una automatización de negocio para Agentius que a una tarea de robot personal en Roboticxs v0.\n\n"
            "Límite: aquí no voy a crear leads, guardar la solicitud, avisar a nadie, hacer handoff, conectar un CRM, usar conectores, abrir navegador, mandar email o WhatsApp, ni tocar sistemas externos.\n"
            "Esto es solo una clasificación boundary-only; no es una capacidad activa de Robbie en v0.\n"
            f"{_capability_next_step_guidance(status=resolution.status, capability_id=resolution.capability_id)}"
        )
    return (
        "No tengo esa capacidad registrada todavía.\n\n"
        "Límite: no voy a inventar una capacidad ni prometer que exista en roadmap.\n"
        f'{_capability_next_step_guidance(status="UNKNOWN", capability_id=resolution.capability_id)}\n'
        'También puedo decirte qué habilidades tengo si escribes: "qué puedes hacer".'
    )


def compose_web_preflight_reply(*, result) -> str:
    lines = ["Preflight web", "", f"Resultado: {result.status}", ""]

    if result.status == "BLOCKED":
        reason = result.blocked_reason or "acción bloqueada"
        lines.extend(
            [
                f"La tarea incluye una acción bloqueada: {reason}.",
                "",
                "Puedo ayudarte a preparar una checklist o revisar qué datos necesitarías, pero no puedo ejecutar pagos, aceptar términos legales ni enviar acciones vinculantes.",
            ]
        )
    elif result.status == "NOT_SUPPORTED":
        lines.extend(
            [
                "Esto parece una tarea web, pero no está cubierta por el preflight local actual.",
                "",
                "Puedo ayudarte si describes el portal, el trámite y el resultado que quieres preparar.",
            ]
        )
    else:
        lines.extend(
            [
                "Lo que puedo hacer ahora",
                "- Preparar una checklist local del trámite.",
                "- Decirte qué datos faltan.",
                "- Marcar acciones que requerirían aprobación.",
            ]
        )
        if result.status == "REQUIRES_LOGIN":
            lines.extend(["", "Este flujo probablemente requeriría login en una capacidad futura, pero aquí no voy a iniciar sesión ni usar credenciales."])
        elif result.status == "REQUIRES_CONFIRMATION":
            lines.extend(["", "El resultado final implicaría enviar o actualizar algo afuera. En una capacidad futura eso tendría que detenerse antes del envío para pedir confirmación."])

    if result.missing_info and result.status in {"PREPARABLE", "NEEDS_INFO", "REQUIRES_LOGIN", "REQUIRES_CONFIRMATION"}:
        lines.extend(["", "Falta confirmar"])
        for item in result.missing_info:
            lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "Límites",
            "- No abrí ningún sitio web.",
            "- No usé navegador, Webwright ni Playwright.",
            "- No hice login.",
            "- No envié formularios.",
            "- No pagué.",
            "- No acepté términos legales.",
        ]
    )
    return "\n".join(lines)


def compose_web_preflight_unknown_reply() -> str:
    return (
        "No puedo clasificar esta tarea web con las reglas locales actuales.\n"
        "Puedo ayudarte si describes el portal, el trámite y qué resultado quieres preparar."
    )


def compose_action_approval_packet_reply(*, packet) -> str:
    lines = [
        "Paquete de aprobación preparado",
        "",
        "Tarea solicitada:",
        packet.requested_task,
        "",
        "Estado:",
        packet.summary,
        "",
        "Lo que puedo preparar:",
    ]
    for item in packet.robot_can_prepare:
        lines.append(f"- {item}")

    if packet.missing_information:
        lines.extend(["", "Lo que falta:"])
        for item in packet.missing_information:
            lines.append(f"- {item}")

    if packet.user_must_confirm:
        lines.extend(["", "Tendrías que confirmar:"])
        for item in packet.user_must_confirm:
            lines.append(f"- {item}")

    if packet.blocked_reason:
        lines.extend(["", "Motivo de bloqueo:", f"- {packet.blocked_reason}"])

    lines.extend(["", "Límites:", "- No voy a ejecutar nada ni enviar nada."])
    for item in packet.robot_must_not_do:
        lines.append(f"- {item}")
    if packet.action_class in {"PAYMENT_MANUAL_PREPARATION", "PAYMENT_EXECUTION_REQUEST"}:
        lines.append("- No puedo ejecutar pagos ni guardar datos de tarjeta/CVV.")

    lines.extend(["", "Siguiente paso seguro:", packet.safe_next_step])
    return "\n".join(lines)


def compose_file_retrieval_enablement_request_resolved_reply(*, resolution: str) -> str:
    action = "approved" if resolution == "APPROVED_PENDING_POLICY_CHANGE" else "rejected"
    return (
        f"Retrieval enablement request {action}.\n"
        "Retrieval remains disabled.\n\n"
        "Roboticxs will not call Telegram getFile, download files, parse PDFs, OCR content, store raw bytes, "
        "store extracted text, or claim the file was reviewed."
    )


def compose_file_retrieval_enablement_request_not_found_reply() -> str:
    return "I could not find a pending retrieval enablement request with that ID for this robot."


def compose_super_familiar_reply(context) -> str:
    lines = [
        "Súper Familiar",
        "",
        "Esto puedo preparar usando solo información local que ya conozco:",
        "",
    ]
    if context.family_targets:
        lines.append("Para quién")
        for target in context.family_targets:
            lines.append(f"- {target} registrado en memoria aprobada.")
        lines.append("")
    if context.known_preferences:
        lines.append("Lo que ya sé")
        for preference in context.known_preferences:
            lines.append(f"- {preference}.")
        lines.append("")
    if context.base_items:
        lines.append("Lista base")
        for item in context.base_items:
            lines.append(f"- {item}")
        lines.append("")
    if context.pending_memory_count:
        lines.append("Pendiente de aprobación")
        lines.append(f"- Hay {context.pending_memory_count} memoria pendiente relacionada con compras familiares.")
        lines.append("")
    lines.append("Falta confirmar")
    for item in context.missing_info:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "Límites",
            "- No puedo entrar a Walmart, Costco ni otra tienda todavía.",
            "- No puedo crear carrito ni checkout.",
            "- No puedo ejecutar pagos.",
            "- No puedo buscar horarios de entrega en vivo.",
            "- Cualquier pedido real requeriría aprobación final del usuario.",
            "",
            "No revisé Walmart, Costco, correo, WhatsApp, calendario, web ni archivos nuevos. Solo usé información local ya registrada.",
        ]
    )
    return "\n".join(lines)


def compose_super_familiar_empty_reply(context) -> str:
    lines = [
        "Súper Familiar todavía no tiene suficiente información local.",
        "",
    ]
    if context.pending_memory_count:
        lines.extend(
            [
                "Pendiente de aprobación",
                f"- Hay {context.pending_memory_count} memoria pendiente relacionada con compras familiares.",
                "",
            ]
        )
    lines.append("Falta confirmar")
    for index, item in enumerate(context.missing_info, start=1):
        lines.append(f"{index}. {item}")
    lines.extend(
        [
            "",
            "Límites",
            "- No puedo entrar a Walmart, Costco ni otra tienda todavía.",
            "- No puedo crear carrito ni checkout.",
            "- No puedo ejecutar pagos.",
            "- No puedo buscar horarios de entrega en vivo.",
            "- Cualquier pedido real requeriría aprobación final del usuario.",
            "",
            "No revisé Walmart, Costco, correo, WhatsApp, calendario, web ni archivos nuevos. Solo usé información local ya registrada.",
        ]
    )
    return "\n".join(lines)
