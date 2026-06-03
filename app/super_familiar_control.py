from __future__ import annotations


SUPER_FAMILIAR_COMMANDS = {
    "súper familiar",
    "super familiar",
    "preparar súper familiar",
    "preparar super familiar",
    "lista del súper familiar",
    "lista del super familiar",
    "family groceries",
}


def is_super_familiar_command(text: str) -> bool:
    return text.strip().lower() in SUPER_FAMILIAR_COMMANDS
