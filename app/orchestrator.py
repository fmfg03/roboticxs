from __future__ import annotations

from app.command_registry import dispatch_registered_flow
from app.flow_runtime import FlowContext, resolve_user_and_robot
from app.flows import (
    process_file_intake,
    process_general_task,
    process_memory_proposal,
)
from app.memory_extraction import detect_memory_intent, extract_proposed_memory
from app.skills import get_active_skill_manifest


def process_telegram_message(*, session, settings, envelope) -> dict:
    user, robot = resolve_user_and_robot(session=session, envelope=envelope)
    context = FlowContext(session=session, settings=settings, envelope=envelope, user=user, robot=robot)

    get_active_skill_manifest(session)

    routed = dispatch_registered_flow(context=context)
    if routed is not None:
        return routed

    if envelope.document is not None:
        return process_file_intake(context=context)

    if detect_memory_intent(envelope.text):
        proposal_payload = extract_proposed_memory(envelope.text)
        if proposal_payload is not None:
            return process_memory_proposal(context=context, proposal_payload=proposal_payload)

    return process_general_task(context=context)
