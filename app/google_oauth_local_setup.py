from __future__ import annotations

import argparse
import secrets
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app.google_oauth_workspace import (
    DEFAULT_GOOGLE_OAUTH_CLIENT_SECRETS_FILE,
    DEFAULT_GOOGLE_OAUTH_REDIRECT_PATH,
    DEFAULT_GOOGLE_OAUTH_REDIRECT_PORT,
    DEFAULT_GOOGLE_OAUTH_TIMEOUT_SECONDS,
    DEFAULT_GOOGLE_OAUTH_TOKEN_FILE,
    build_google_oauth_authorization_url,
    build_loopback_redirect_uri,
    build_pkce_code_challenge,
    exchange_google_oauth_code,
    generate_pkce_code_verifier,
    load_google_oauth_client_config,
    redacted_google_oauth_token_summary,
    save_google_oauth_token_record,
    workspace_scopes_for_gmail_mode,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap Google Workspace OAuth for Roboticxs Calendar/Gmail read-only access."
    )
    parser.add_argument(
        "--client-secrets-file",
        default=DEFAULT_GOOGLE_OAUTH_CLIENT_SECRETS_FILE,
        help="Path to the Google OAuth Desktop client JSON file.",
    )
    parser.add_argument(
        "--token-file",
        default=DEFAULT_GOOGLE_OAUTH_TOKEN_FILE,
        help="Where to write the Roboticxs OAuth token JSON.",
    )
    parser.add_argument(
        "--redirect-port",
        type=int,
        default=DEFAULT_GOOGLE_OAUTH_REDIRECT_PORT,
        help="Local loopback port. Use an SSH -L tunnel when running on the VM.",
    )
    parser.add_argument(
        "--gmail-mode",
        choices=("metadata", "readonly", "none"),
        default="metadata",
        help="Gmail scope mode. metadata avoids email body access; readonly allows message body reads.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_GOOGLE_OAUTH_TIMEOUT_SECONDS,
        help="Timeout for the token exchange request.",
    )
    args = parser.parse_args(argv)

    client = load_google_oauth_client_config(args.client_secrets_file)
    redirect_uri = build_loopback_redirect_uri(port=args.redirect_port, path=DEFAULT_GOOGLE_OAUTH_REDIRECT_PATH)
    scopes = workspace_scopes_for_gmail_mode(args.gmail_mode)
    state = secrets.token_urlsafe(24)
    verifier = generate_pkce_code_verifier()
    authorization_url = build_google_oauth_authorization_url(
        client=client,
        redirect_uri=redirect_uri,
        scopes=scopes,
        state=state,
        code_challenge=build_pkce_code_challenge(verifier),
    )

    print("Google Workspace OAuth setup for Roboticxs")
    print("")
    print("Open this URL in your browser:")
    print(authorization_url)
    print("")
    print(f"Waiting for Google redirect on {redirect_uri} ...")

    try:
        callback = _wait_for_oauth_callback(
            port=args.redirect_port,
            path=DEFAULT_GOOGLE_OAUTH_REDIRECT_PATH,
            expected_state=state,
        )
    except ValueError as exc:
        print(f"Google OAuth setup failed: {exc}", file=sys.stderr)
        return 1

    try:
        record = exchange_google_oauth_code(
            client=client,
            code=callback.code,
            redirect_uri=redirect_uri,
            code_verifier=verifier,
            scopes=scopes,
            timeout_seconds=args.timeout_seconds,
        )
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        print(f"Google OAuth token exchange failed: {exc}", file=sys.stderr)
        return 1

    save_google_oauth_token_record(record, args.token_file)
    print("")
    print(redacted_google_oauth_token_summary(record))
    print(f"Token file: {args.token_file}")
    return 0


class _OAuthCallback:
    def __init__(self, code: str) -> None:
        self.code = code


def _wait_for_oauth_callback(
    *,
    port: int,
    path: str,
    expected_state: str,
) -> _OAuthCallback:
    captured: dict[str, str] = {}
    expected_path = path if path.startswith("/") else f"/{path}"

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler.
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            if parsed.path != expected_path:
                self.send_response(404)
                self.end_headers()
                return
            if params.get("state", [""])[0] != expected_state:
                captured["error"] = "rejected_oauth_state_mismatch"
            elif params.get("error", [""])[0]:
                captured["error"] = params.get("error", ["unknown_oauth_error"])[0]
            else:
                captured["code"] = params.get("code", [""])[0]

            self.send_response(200 if "code" in captured else 400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            message = (
                "Roboticxs OAuth authorization captured. You can close this tab.\n"
                if "code" in captured
                else "Roboticxs OAuth authorization was rejected.\n"
            )
            self.wfile.write(message.encode("utf-8"))

        def log_message(self, format: str, *args: object) -> None:
            return

    with ThreadingHTTPServer(("127.0.0.1", port), Handler) as server:
        while "code" not in captured and "error" not in captured:
            server.handle_request()

    if captured.get("error"):
        raise ValueError(captured["error"])
    code = captured.get("code", "").strip()
    if not code:
        raise ValueError("rejected_missing_oauth_code")
    return _OAuthCallback(code)


if __name__ == "__main__":
    raise SystemExit(main())
