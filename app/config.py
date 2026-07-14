from dataclasses import dataclass
import os


@dataclass(slots=True)
class Settings:
    database_url: str = "sqlite:////tmp/roboticxs.db"
    default_provider: str = "openai"
    default_model: str = "gpt-4o-mini-or-equivalent"
    default_routing_mode: str = "economy"
    file_retrieval_enabled: bool = False
    telegram_bot_token: str | None = None
    telegram_public_webhook_url: str | None = None
    telegram_owner_id: int | None = None
    conversation_enabled: bool = False
    conversation_model: str = "granite4:7b-a1b-h"
    conversation_base_url: str = "http://127.0.0.1:11434"
    conversation_timeout_seconds: float = 8.0


def _read_bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _read_optional_int_env(name: str) -> int | None:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return None
    try:
        return int(raw_value.strip())
    except ValueError:
        return None


def _read_positive_float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = float(raw_value.strip())
    except ValueError:
        return default
    return value if value > 0 else default


def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:////tmp/roboticxs.db"),
        default_provider=os.getenv("ROBOTICXS_PROVIDER", "openai"),
        default_model=os.getenv("ROBOTICXS_MODEL", "gpt-4o-mini-or-equivalent"),
        default_routing_mode=os.getenv("ROBOTICXS_ROUTING_MODE", "economy"),
        file_retrieval_enabled=_read_bool_env("FILE_RETRIEVAL_ENABLED", False),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN") or None,
        telegram_public_webhook_url=os.getenv("TELEGRAM_PUBLIC_WEBHOOK_URL") or None,
        telegram_owner_id=_read_optional_int_env("ROBOTICXS_OWNER_ID"),
        conversation_enabled=_read_bool_env("ROBOTICXS_CONVERSATION_ENABLED", False),
        conversation_model=os.getenv("ROBOTICXS_CONVERSATION_MODEL", "granite4:7b-a1b-h"),
        conversation_base_url=os.getenv("ROBOTICXS_CONVERSATION_BASE_URL", "http://127.0.0.1:11434"),
        conversation_timeout_seconds=_read_positive_float_env("ROBOTICXS_CONVERSATION_TIMEOUT_SECONDS", 8.0),
    )
