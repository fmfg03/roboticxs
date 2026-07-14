from __future__ import annotations

import re


CATALOG_COMMANDS = {
    "qué puedes hacer",
    "qué habilidades tienes",
    "habilidades",
    "skill catalog",
    "what can you do",
    "what skills do you have",
}

CAPABILITY_QUERY_PATTERNS = (
    re.compile(r"^puedes ayudarme con .+$", re.IGNORECASE),
    re.compile(r"^puedes hacer .+$", re.IGNORECASE),
    re.compile(r"^puedes .+$", re.IGNORECASE),
    re.compile(r"^can you help me with .+$", re.IGNORECASE),
    re.compile(r"^can you .+$", re.IGNORECASE),
)


def is_capability_catalog_command(text: str) -> bool:
    return text.strip().lower() in CATALOG_COMMANDS


def is_capability_query(text: str) -> bool:
    normalized = text.strip().lstrip("¿").strip()
    return any(pattern.match(normalized) for pattern in CAPABILITY_QUERY_PATTERNS)
