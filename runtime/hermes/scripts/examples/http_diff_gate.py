from __future__ import annotations

import argparse
import hashlib
import json


def response_fingerprint(status_code: str, etag: str | None, last_modified: str | None, body: str | None) -> dict:
    body_sha256 = hashlib.sha256(body.encode("utf-8")).hexdigest() if body is not None else None
    return {
        "type": "http_metadata",
        "status_code": status_code,
        "etag": etag,
        "last_modified": last_modified,
        "body_sha256": body_sha256,
    }


def build_packet(
    url: str,
    status_code: str,
    etag: str | None,
    last_modified: str | None,
    body: str | None,
    previous_fingerprint: str | None,
) -> dict:
    fingerprint = response_fingerprint(status_code, etag, last_modified, body)
    current_fingerprint = json.dumps(fingerprint, sort_keys=True)
    changed = previous_fingerprint is not None and current_fingerprint != previous_fingerprint

    return {
        "decision": "WAKE_AGENT" if changed else "SKIP_NO_CHANGE",
        "wakeAgent": changed,
        "token_expectation": "bounded_by_budget_policy" if changed else 0,
        "model_router_allowed": changed,
        "source_fingerprints": [{"url": url, **fingerprint}],
        "bounded_context": {"url": url, "changed": True, "status_code": status_code} if changed else None,
        "observable_error": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Example HTTP metadata diff wake gate.")
    parser.add_argument("url")
    parser.add_argument("--status-code", default="200")
    parser.add_argument("--etag")
    parser.add_argument("--last-modified")
    parser.add_argument("--body")
    parser.add_argument("--previous-fingerprint")
    args = parser.parse_args()

    packet = build_packet(
        url=args.url,
        status_code=args.status_code,
        etag=args.etag,
        last_modified=args.last_modified,
        body=args.body,
        previous_fingerprint=args.previous_fingerprint,
    )
    print(json.dumps(packet, sort_keys=True))


if __name__ == "__main__":
    main()
