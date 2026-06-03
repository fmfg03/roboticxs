from __future__ import annotations


WEB_PREFLIGHT_COMMANDS = {
    "preflight web",
    "revisar tarea web",
    "evaluar trámite web",
    "evaluar tramite web",
    "puedes hacer este trámite",
    "puedes hacer este tramite",
    "web workflow preflight",
    "check web workflow",
}


def is_web_preflight_command(text: str) -> bool:
    return text.strip().lower() in WEB_PREFLIGHT_COMMANDS
