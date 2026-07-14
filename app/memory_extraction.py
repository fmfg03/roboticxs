from __future__ import annotations


TRIGGERS = [
    "remember that ",
    "remember this ",
    "i prefer ",
    "i usually ",
    "never ",
    "ask before ",
    "guarda esto para agentius",
    "guarda esto como algo que quiero revisar para agentius",
    "quiero revisar esto para agentius",
    "guarda este interés de agentius",
    "guarda este interes de agentius",
]

PROFILE_PATTERNS = [
    "my name is ",
    "my role is ",
    "my company is ",
    "my timezone is ",
    "my working hours are ",
    "my preferred ",
]


def is_memory_approval_command(text: str) -> bool:
    return text.strip().upper() in {"APPROVE", "REJECT"}


def detect_memory_intent(text: str) -> bool:
    normalized = text.strip().lower()
    return any(normalized.startswith(trigger) for trigger in TRIGGERS) or any(
        normalized.startswith(pattern) for pattern in PROFILE_PATTERNS
    )


def extract_proposed_memory(text: str) -> dict[str, str] | None:
    stripped = text.strip()
    normalized = stripped.lower()

    if normalized.startswith("guarda esto para agentius"):
        return build_upgrade_interest_memory(detail=stripped)
    if normalized.startswith("guarda esto como algo que quiero revisar para agentius"):
        return build_upgrade_interest_memory(detail=stripped)
    if normalized.startswith("quiero revisar esto para agentius"):
        return build_upgrade_interest_memory(detail=stripped)
    if normalized.startswith("guarda este interés de agentius"):
        return build_upgrade_interest_memory(detail=stripped)
    if normalized.startswith("guarda este interes de agentius"):
        return build_upgrade_interest_memory(detail=stripped)
    if normalized.startswith("remember that "):
        content = stripped[len("remember that ") :].strip()
        return classify_memory_content(content)
    if normalized.startswith("remember this "):
        content = stripped[len("remember this ") :].strip()
        return classify_memory_content(content)
    if normalized.startswith("i prefer "):
        detail = stripped[len("I prefer ") :].strip()
        return {
            "memory_type": "WORK_PREFERENCE",
            "label": "Preference",
            "content": f"You prefer {detail.rstrip('.')}.",
            "importance": "high",
        }
    if normalized.startswith("i usually "):
        detail = stripped[len("I usually ") :].strip()
        return {
            "memory_type": "WORK_PREFERENCE",
            "label": "Work habit",
            "content": f"You usually {detail.rstrip('.')}.",
            "importance": "normal",
        }
    if normalized.startswith("never "):
        detail = stripped[len("Never ") :].strip()
        return {
            "memory_type": "BOUNDARY_MEMORY",
            "label": "Boundary",
            "content": normalize_boundary(detail, prefix="Never"),
            "importance": "high",
        }
    if normalized.startswith("ask before "):
        detail = stripped[len("Ask before ") :].strip()
        return {
            "memory_type": "BOUNDARY_MEMORY",
            "label": "Boundary",
            "content": f"Ask before {detail.rstrip('.')}.",
            "importance": "high",
        }
    for pattern in PROFILE_PATTERNS:
        if normalized.startswith(pattern):
            detail = stripped[len(pattern) :].strip()
            return build_profile_memory(pattern=pattern, detail=detail)
    return None


def build_profile_memory(*, pattern: str, detail: str) -> dict[str, str]:
    detail = detail.rstrip(".")
    if pattern == "my name is ":
        return {
            "memory_type": "USER_PROFILE",
            "label": "Profile",
            "content": f"Your name is {detail}.",
            "importance": "high",
        }
    if pattern == "my role is ":
        return {
            "memory_type": "USER_PROFILE",
            "label": "Profile",
            "content": f"Your role is {detail}.",
            "importance": "high",
        }
    if pattern == "my company is ":
        return {
            "memory_type": "BUSINESS_CONTEXT",
            "label": "Business context",
            "content": f"Your company is {detail}.",
            "importance": "high",
        }
    if pattern == "my timezone is ":
        return {
            "memory_type": "USER_PROFILE",
            "label": "Profile",
            "content": f"Your timezone is {detail}.",
            "importance": "high",
        }
    if pattern == "my working hours are ":
        return {
            "memory_type": "WORK_PREFERENCE",
            "label": "Work habit",
            "content": f"Your working hours are {detail}.",
            "importance": "normal",
        }
    return {
        "memory_type": "WORK_PREFERENCE",
        "label": "Preference",
        "content": f"Your preferred {detail}.",
        "importance": "normal",
    }


def build_upgrade_interest_memory(*, detail: str) -> dict[str, str]:
    normalized = detail.strip().rstrip(".")
    lowered = normalized.lower()
    prefixes = (
        "guarda esto para agentius después",
        "guarda esto para agentius despues",
        "guarda esto para agentius",
        "guarda esto como algo que quiero revisar para agentius después",
        "guarda esto como algo que quiero revisar para agentius despues",
        "guarda esto como algo que quiero revisar para agentius",
        "quiero revisar esto para agentius después",
        "quiero revisar esto para agentius despues",
        "quiero revisar esto para agentius",
        "guarda este interés de agentius",
        "guarda este interes de agentius",
    )
    extracted = ""
    for prefix in prefixes:
        if lowered.startswith(prefix):
            extracted = normalized[len(prefix) :].strip(" .:-")
            break
    if extracted:
        content = f"Interés local para revisar después con Agentius: {extracted.rstrip('.')}."
    else:
        content = "Interés local para revisar después con Agentius."
    return {
        "memory_type": "UPGRADE_INTEREST",
        "label": "Interés local",
        "content": content,
        "importance": "normal",
    }


def classify_memory_content(content: str) -> dict[str, str]:
    lowered = content.lower()
    clean = content.rstrip(".")
    if lowered.startswith("i prefer "):
        return {
            "memory_type": "WORK_PREFERENCE",
            "label": "Preference",
            "content": f"You prefer {content[9:].rstrip('.')}.",
            "importance": "high",
        }
    if lowered.startswith("my company is "):
        return {
            "memory_type": "BUSINESS_CONTEXT",
            "label": "Business context",
            "content": f"Your company is {content[14:].rstrip('.')}.",
            "importance": "high",
        }
    if lowered.startswith("my timezone is "):
        return {
            "memory_type": "USER_PROFILE",
            "label": "Profile",
            "content": f"Your timezone is {content[15:].rstrip('.')}.",
            "importance": "high",
        }
    if lowered.startswith("never "):
        return {
            "memory_type": "BOUNDARY_MEMORY",
            "label": "Boundary",
            "content": normalize_boundary(content[6:].strip(), prefix="Never"),
            "importance": "high",
        }
    if lowered.startswith("ask before "):
        return {
            "memory_type": "BOUNDARY_MEMORY",
            "label": "Boundary",
            "content": f"Ask before {content[11:].rstrip('.')}.",
            "importance": "high",
        }
    return {
        "memory_type": "TASK_MEMORY",
        "label": "Memory",
        "content": clean if clean.endswith(".") else f"{clean}.",
        "importance": "normal",
    }


def normalize_boundary(detail: str, prefix: str) -> str:
    normalized = detail.rstrip(".")
    if normalized.lower().startswith("send messages to clients without asking me first"):
        return "Ask before sending messages to clients."
    if prefix == "Never":
        return f"Never {normalized}."
    return f"{normalized}."
