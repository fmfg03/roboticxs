from dataclasses import dataclass, field
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
    telegram_allowed_user_ids: frozenset[int] = field(default_factory=frozenset)
    conversation_enabled: bool = False
    conversation_model: str = "qwen3:8b"
    conversation_base_url: str = "http://127.0.0.1:11434"
    conversation_timeout_seconds: float = 8.0
    conversation_history_enabled: bool = False
    conversation_history_max_turns: int = 6
    conversation_history_ttl_minutes: int = 120
    helper_discovery_enabled: bool = False
    helper_interview_provider: str = "local"
    helper_interview_model: str = "gpt-5.6-luna"
    helper_interview_timeout_seconds: float = 12.0
    openai_api_key: str | None = None

    def __post_init__(self) -> None:
        self.telegram_allowed_user_ids = frozenset(
            user_id
            for user_id in self.telegram_allowed_user_ids
            if isinstance(user_id, int) and user_id > 0
        )
        self.conversation_history_max_turns = max(1, min(self.conversation_history_max_turns, 6))
        self.conversation_history_ttl_minutes = max(1, min(self.conversation_history_ttl_minutes, 1440))
        self.helper_interview_provider = (
            "openai" if self.helper_interview_provider.strip().lower() == "openai" else "local"
        )

    def is_telegram_user_allowed(self, user_id: int) -> bool:
        if self.telegram_owner_id is None:
            return False
        return user_id == self.telegram_owner_id or user_id in self.telegram_allowed_user_ids


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


def _read_int_set_env(name: str) -> frozenset[int]:
    raw_value = os.getenv(name, "")
    values: set[int] = set()
    for item in raw_value.split(","):
        normalized = item.strip()
        if not normalized:
            continue
        try:
            value = int(normalized)
        except ValueError:
            continue
        if value > 0:
            values.add(value)
    return frozenset(values)


def _read_positive_float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = float(raw_value.strip())
    except ValueError:
        return default
    return value if value > 0 else default


def _read_positive_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value.strip())
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
        telegram_allowed_user_ids=_read_int_set_env("ROBOTICXS_TELEGRAM_ALLOWED_USER_IDS"),
        conversation_enabled=_read_bool_env("ROBOTICXS_CONVERSATION_ENABLED", False),
        conversation_model=os.getenv("ROBOTICXS_CONVERSATION_MODEL", "qwen3:8b"),
        conversation_base_url=os.getenv("ROBOTICXS_CONVERSATION_BASE_URL", "http://127.0.0.1:11434"),
        conversation_timeout_seconds=_read_positive_float_env("ROBOTICXS_CONVERSATION_TIMEOUT_SECONDS", 8.0),
        conversation_history_enabled=_read_bool_env("ROBOTICXS_CONVERSATION_HISTORY_ENABLED", False),
        conversation_history_max_turns=_read_positive_int_env("ROBOTICXS_CONVERSATION_HISTORY_MAX_TURNS", 6),
        conversation_history_ttl_minutes=_read_positive_int_env("ROBOTICXS_CONVERSATION_HISTORY_TTL_MINUTES", 120),
        helper_discovery_enabled=_read_bool_env("ROBOTICXS_HELPER_DISCOVERY_ENABLED", False),
        helper_interview_provider=os.getenv("ROBOTICXS_HELPER_INTERVIEW_PROVIDER", "local"),
        helper_interview_model=os.getenv("ROBOTICXS_HELPER_INTERVIEW_MODEL", "gpt-5.6-luna"),
        helper_interview_timeout_seconds=_read_positive_float_env(
            "ROBOTICXS_HELPER_INTERVIEW_TIMEOUT_SECONDS", 12.0
        ),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
    )
