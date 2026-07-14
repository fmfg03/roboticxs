from __future__ import annotations

import argparse
import json


def build_packet(flag_name: str, current_value: str, previous_value: str | None, alert_value: str) -> dict:
    changed = previous_value is not None and current_value != previous_value
    alert = changed and current_value == alert_value
    decision = "SCRIPT_ONLY_ALERT" if alert else "SKIP_NO_CHANGE"

    return {
        "decision": decision,
        "wakeAgent": False,
        "token_expectation": 0,
        "model_router_allowed": False,
        "source_fingerprints": [
            {
                "type": "external_flag",
                "flag_name": flag_name,
                "value": current_value,
            }
        ],
        "bounded_context": None,
        "script_only_alert": {"flag_name": flag_name, "value": current_value} if alert else None,
        "observable_error": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Example external-flag script-only wake gate.")
    parser.add_argument("flag_name")
    parser.add_argument("current_value")
    parser.add_argument("--previous-value")
    parser.add_argument("--alert-value", default="true")
    args = parser.parse_args()

    packet = build_packet(args.flag_name, args.current_value, args.previous_value, args.alert_value)
    print(json.dumps(packet, sort_keys=True))


if __name__ == "__main__":
    main()
