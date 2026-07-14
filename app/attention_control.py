from __future__ import annotations


WHAT_DID_I_MISS_COMMAND = "qué se me pasó"
WHAT_DID_I_MISS_EN_COMMAND = "what did i miss"
WHAT_NEEDS_MY_ATTENTION_COMMAND = "qué necesita mi atención"


def is_attention_summary_command(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {
        WHAT_DID_I_MISS_COMMAND,
        WHAT_DID_I_MISS_EN_COMMAND,
        WHAT_NEEDS_MY_ATTENTION_COMMAND,
    }
