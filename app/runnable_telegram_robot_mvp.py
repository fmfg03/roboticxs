from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
import time
from typing import Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen


RUNNABLE_TELEGRAM_ROBOT_STAGE = "130P"
DEFAULT_ROBOT_ID = "roboticxs-dev"
DEFAULT_OWNER_ID = "local-owner"
DEFAULT_POLL_TIMEOUT_SECONDS = 30
DEFAULT_POLL_LIMIT = 10
DEFAULT_DEV_MODE = True
DEFAULT_DRY_RUN = False
SUPPORTED_COMMANDS = ("/start", "/help", "/status")


class TelegramRobotConfigError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TelegramRobotConfig:
    bot_token: str
    owner_ids: frozenset[int]
    robot_id: str
    owner_id: str
    poll_timeout_seconds: int
    poll_limit: int
    dry_run: bool
    dev_mode: bool


@dataclass(frozen=True, slots=True)
class TelegramIncomingCommand:
    update_id: int | None
    chat_id: int
    telegram_user_id: int
    message_id: int | None
    command: str
    raw_text: str


@dataclass(frozen=True, slots=True)
class TelegramSendReceipt:
    chat_id: int
    telegram_user_id: int
    command: str
    authorized: bool
    reply_text: str
    message_id: int | None
    api_receipt: dict | None


@dataclass(frozen=True, slots=True)
class TelegramPollingCycleResult:
    next_offset: int | None
    processed_update_ids: tuple[int, ...]
    ignored_update_ids: tuple[int, ...]
    receipts: tuple[TelegramSendReceipt, ...]


class TelegramClientProtocol(Protocol):
    def get_updates(self, offset: int | None, timeout: int, limit: int) -> list[dict]:
        ...

    def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: int | None = None,
    ) -> dict:
        ...


class TelegramBotApiClient:
    def __init__(self, *, bot_token: str) -> None:
        self._bot_token = bot_token
        self._base_url = f"https://api.telegram.org/bot{bot_token}/"

    def get_updates(self, offset: int | None, timeout: int, limit: int) -> list[dict]:
        payload: dict[str, int] = {
            "timeout": timeout,
            "limit": limit,
        }
        if offset is not None:
            payload["offset"] = offset
        body = self._post("getUpdates", payload)
        result = body.get("result")
        if not isinstance(result, list):
            raise TelegramRobotConfigError("rejected_invalid_get_updates_result")
        return [item for item in result if isinstance(item, dict)]

    def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: int | None = None,
    ) -> dict:
        payload: dict[str, int | str] = {
            "chat_id": chat_id,
            "text": text,
        }
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        return self._post("sendMessage", payload)

    def _post(self, method: str, payload: dict[str, int | str]) -> dict:
        data = urlencode(payload).encode("utf-8")
        request = Request(
            self._base_url + method,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
        if body.get("ok") is not True:
            raise TelegramRobotConfigError(f"telegram_api_error:{method}")
        return body


def _env_bool(name: str, default: bool = False, env: dict[str, str] | None = None) -> bool:
    source = os.environ if env is None else env
    raw = source.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _parse_owner_ids(raw: str | None) -> frozenset[int]:
    if raw is None or not raw.strip():
        return frozenset()
    owner_ids: set[int] = set()
    for part in raw.split(","):
        candidate = part.strip()
        if not candidate:
            continue
        if not candidate.isdigit():
            raise TelegramRobotConfigError("rejected_invalid_owner_allowlist")
        owner_ids.add(int(candidate))
    return frozenset(owner_ids)


def load_telegram_robot_config_from_env(env: dict[str, str] | None = None) -> TelegramRobotConfig:
    source = os.environ if env is None else env
    poll_timeout_raw = source.get(
        "ROBOTICXS_TELEGRAM_POLL_TIMEOUT_SECONDS",
        str(DEFAULT_POLL_TIMEOUT_SECONDS),
    )
    poll_limit_raw = source.get("ROBOTICXS_TELEGRAM_POLL_LIMIT", str(DEFAULT_POLL_LIMIT))
    try:
        poll_timeout_seconds = int(poll_timeout_raw)
        poll_limit = int(poll_limit_raw)
    except ValueError as exc:
        raise TelegramRobotConfigError("rejected_invalid_polling_configuration") from exc
    return TelegramRobotConfig(
        bot_token=source.get("ROBOTICXS_TELEGRAM_BOT_TOKEN", "").strip(),
        owner_ids=_parse_owner_ids(source.get("ROBOTICXS_TELEGRAM_OWNER_IDS")),
        robot_id=source.get("ROBOTICXS_ROBOT_ID", DEFAULT_ROBOT_ID).strip(),
        owner_id=source.get("ROBOTICXS_OWNER_ID", DEFAULT_OWNER_ID).strip(),
        poll_timeout_seconds=poll_timeout_seconds,
        poll_limit=poll_limit,
        dry_run=_env_bool("ROBOTICXS_TELEGRAM_DRY_RUN", DEFAULT_DRY_RUN, env=source),
        dev_mode=_env_bool("ROBOTICXS_TELEGRAM_DEV_MODE", DEFAULT_DEV_MODE, env=source),
    )


def validate_telegram_robot_config(config: TelegramRobotConfig) -> TelegramRobotConfig:
    if not config.robot_id:
        raise TelegramRobotConfigError("rejected_missing_robot_id")
    if not config.owner_id:
        raise TelegramRobotConfigError("rejected_missing_owner_id")
    if not config.owner_ids:
        raise TelegramRobotConfigError("rejected_missing_owner_allowlist")
    if not config.dry_run and not config.bot_token:
        raise TelegramRobotConfigError("rejected_missing_bot_token")
    if config.poll_timeout_seconds <= 0:
        raise TelegramRobotConfigError("rejected_invalid_poll_timeout")
    if config.poll_limit <= 0:
        raise TelegramRobotConfigError("rejected_invalid_poll_limit")
    return config


def parse_telegram_incoming_command(update: dict) -> TelegramIncomingCommand | None:
    if not isinstance(update, dict):
        return None
    message = update.get("message")
    if not isinstance(message, dict):
        return None
    chat = message.get("chat")
    sender = message.get("from")
    raw_text = message.get("text")
    if not isinstance(chat, dict) or not isinstance(sender, dict) or not isinstance(raw_text, str):
        return None
    chat_id = chat.get("id")
    telegram_user_id = sender.get("id")
    if not isinstance(chat_id, int) or not isinstance(telegram_user_id, int):
        return None
    stripped_text = raw_text.strip()
    if not stripped_text:
        return None
    command = normalize_telegram_command(stripped_text)
    if command is None:
        return None
    update_id = update.get("update_id")
    message_id = message.get("message_id")
    return TelegramIncomingCommand(
        update_id=update_id if isinstance(update_id, int) else None,
        chat_id=chat_id,
        telegram_user_id=telegram_user_id,
        message_id=message_id if isinstance(message_id, int) else None,
        command=command,
        raw_text=stripped_text,
    )


def normalize_telegram_command(raw_text: str) -> str | None:
    stripped = raw_text.strip()
    if not stripped:
        return None
    first_token = stripped.split()[0].lower()
    if first_token.startswith("/"):
        base = first_token.split("@", 1)[0]
        return base
    return first_token


def is_owner_authorized(
    *,
    telegram_user_id: int,
    config: TelegramRobotConfig,
) -> bool:
    return telegram_user_id in config.owner_ids


def render_start_command_reply(config: TelegramRobotConfig) -> str:
    return "\n".join(
        [
            f"Roboticxs is online.",
            f"Robot: {config.robot_id}",
            "This dev bot is owner-gated.",
            "Available commands: /help, /status.",
            "No external actions are enabled.",
            "No action was taken.",
        ]
    )


def render_help_command_reply() -> str:
    return "\n".join(
        [
            "Available commands:",
            "/start",
            "/help",
            "/status",
            "/miss and /brief are not enabled yet.",
        ]
    )


def render_status_command_reply(config: TelegramRobotConfig) -> str:
    live_telegram_state = "disabled" if config.dry_run else "enabled"
    dev_mode_state = "enabled" if config.dev_mode else "disabled"
    return "\n".join(
        [
            f"robot_id: {config.robot_id}",
            "owner_gated: enabled",
            "Hermes runtime bootstrap: available",
            f"Telegram dev/sandbox mode: {dev_mode_state}",
            f"live Telegram: {live_telegram_state}",
            "external connectors: disabled",
            "LLM/model calls: disabled",
            "tools: disabled",
            "Memory Center mutation: disabled",
            "proactive outbound: disabled",
            "roadmap state: 95P-129P closed, 130P runtime active",
        ]
    )


def render_unknown_command_reply() -> str:
    return "\n".join(
        [
            "Command not enabled.",
            "Available commands: /start, /help, /status.",
            "No action was taken.",
        ]
    )


def render_unauthorized_reply() -> str:
    return "This Roboticxs bot is private. No action was taken."


def render_command_reply(command: str, config: TelegramRobotConfig) -> str:
    if command == "/start":
        return render_start_command_reply(config)
    if command == "/help":
        return render_help_command_reply()
    if command == "/status":
        return render_status_command_reply(config)
    return render_unknown_command_reply()


def handle_incoming_command(
    *,
    incoming_command: TelegramIncomingCommand,
    client: TelegramClientProtocol,
    config: TelegramRobotConfig,
) -> TelegramSendReceipt:
    authorized = is_owner_authorized(
        telegram_user_id=incoming_command.telegram_user_id,
        config=config,
    )
    if authorized:
        reply_text = render_command_reply(incoming_command.command, config)
    else:
        reply_text = render_unauthorized_reply()
    receipt = client.send_message(
        incoming_command.chat_id,
        reply_text,
        reply_to_message_id=incoming_command.message_id,
    )
    return TelegramSendReceipt(
        chat_id=incoming_command.chat_id,
        telegram_user_id=incoming_command.telegram_user_id,
        command=incoming_command.command,
        authorized=authorized,
        reply_text=reply_text,
        message_id=incoming_command.message_id,
        api_receipt=receipt,
    )


def run_polling_once(
    *,
    client: TelegramClientProtocol,
    config: TelegramRobotConfig,
    offset: int | None = None,
) -> TelegramPollingCycleResult:
    validated = validate_telegram_robot_config(config)
    updates = client.get_updates(
        offset=offset,
        timeout=validated.poll_timeout_seconds,
        limit=validated.poll_limit,
    )
    next_offset = offset
    processed_update_ids: list[int] = []
    ignored_update_ids: list[int] = []
    receipts: list[TelegramSendReceipt] = []
    for update in updates:
        update_id = update.get("update_id")
        incoming_command = parse_telegram_incoming_command(update)
        if incoming_command is None:
            if isinstance(update_id, int):
                ignored_update_ids.append(update_id)
                next_offset = update_id + 1
            continue
        receipts.append(
            handle_incoming_command(
                incoming_command=incoming_command,
                client=client,
                config=validated,
            )
        )
        if incoming_command.update_id is not None:
            processed_update_ids.append(incoming_command.update_id)
            next_offset = incoming_command.update_id + 1
    return TelegramPollingCycleResult(
        next_offset=next_offset,
        processed_update_ids=tuple(processed_update_ids),
        ignored_update_ids=tuple(ignored_update_ids),
        receipts=tuple(receipts),
    )


def run_polling_loop(
    *,
    client: TelegramClientProtocol,
    config: TelegramRobotConfig,
    offset: int | None = None,
    max_cycles: int | None = None,
    idle_sleep_seconds: float = 0.0,
) -> TelegramPollingCycleResult:
    validated = validate_telegram_robot_config(config)
    if max_cycles is not None and max_cycles < 0:
        raise TelegramRobotConfigError("rejected_invalid_max_cycles")
    cycle_count = 0
    current_offset = offset
    all_processed: list[int] = []
    all_ignored: list[int] = []
    all_receipts: list[TelegramSendReceipt] = []
    while max_cycles is None or cycle_count < max_cycles:
        result = run_polling_once(client=client, config=validated, offset=current_offset)
        current_offset = result.next_offset
        all_processed.extend(result.processed_update_ids)
        all_ignored.extend(result.ignored_update_ids)
        all_receipts.extend(result.receipts)
        cycle_count += 1
        if max_cycles is not None and cycle_count >= max_cycles:
            break
        if idle_sleep_seconds > 0:
            time.sleep(idle_sleep_seconds)
    return TelegramPollingCycleResult(
        next_offset=current_offset,
        processed_update_ids=tuple(all_processed),
        ignored_update_ids=tuple(all_ignored),
        receipts=tuple(all_receipts),
    )


def build_telegram_robot_startup_report(config: TelegramRobotConfig) -> str:
    validated = validate_telegram_robot_config(config)
    return "\n".join(
        [
            "Roboticxs Telegram Robot: online",
            f"Stage: {RUNNABLE_TELEGRAM_ROBOT_STAGE}",
            f"Robot: {validated.robot_id}",
            f"Owner gate: enabled ({len(validated.owner_ids)} allowed Telegram user id(s))",
            f"Dev mode: {'enabled' if validated.dev_mode else 'disabled'}",
            f"Dry run: {'enabled' if validated.dry_run else 'disabled'}",
            "Available commands: /start, /help, /status",
            "External connectors: disabled",
            "LLM/model calls: disabled",
            "Tools: disabled",
            "Memory Center mutation: disabled",
            "Proactive outbound: disabled",
        ]
    )


def create_telegram_client(config: TelegramRobotConfig) -> TelegramClientProtocol:
    return TelegramBotApiClient(bot_token=config.bot_token)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m app.runnable_telegram_robot_mvp")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--max-cycles", type=int, default=None)
    args = parser.parse_args(argv)
    try:
        config = validate_telegram_robot_config(load_telegram_robot_config_from_env())
        client = create_telegram_client(config)
    except TelegramRobotConfigError as exc:
        print(f"Roboticxs Telegram Robot: offline\nReason: {exc}")
        return 1
    print(build_telegram_robot_startup_report(config))
    try:
        if args.once:
            run_polling_once(client=client, config=config)
        else:
            run_polling_loop(client=client, config=config, max_cycles=args.max_cycles)
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
