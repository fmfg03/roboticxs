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


def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:////tmp/roboticxs.db"),
        default_provider=os.getenv("ROBOTICXS_PROVIDER", "openai"),
        default_model=os.getenv("ROBOTICXS_MODEL", "gpt-4o-mini-or-equivalent"),
        default_routing_mode=os.getenv("ROBOTICXS_ROUTING_MODE", "economy"),
        file_retrieval_enabled=_read_bool_env("FILE_RETRIEVAL_ENABLED", False),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN") or None,
        telegram_public_webhook_url=os.getenv("TELEGRAM_PUBLIC_WEBHOOK_URL") or None,
    )
