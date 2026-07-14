# Roboticxs Pilot Launch Runbook

This runbook replaces open-ended numbered-stage continuation with a finite launch gate.

## Exit criteria

The pilot is launched only when all five conditions are true:

1. `python3 -m app.runtime_doctor --json` reports `launch_status: ready`.
2. The service is running under a dedicated non-root account.
3. HTTPS routes Telegram to `/api/telegram/runtime/webhook`.
4. One allowlisted friendly user completes onboarding, daily brief, feedback, and exit/export checks.
5. Safety logs show no owner/robot scope leak or prohibited external write.

## Required configuration

Copy `.env.example` to `/etc/roboticxs/roboticxs.env` and provide at least:

- `DATABASE_URL`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_PUBLIC_WEBHOOK_URL`
- `ROBOTICXS_RUNTIME_MODE=pilot`
- `ROBOTICXS_ROBOT_ID`
- `ROBOTICXS_OWNER_ID`
- `ROBOTICXS_LOCAL_STATE_DIR=/var/lib/roboticxs`

Google Calendar and Gmail read-only access are optional for initial service startup. When enabled, OAuth files must pass the runtime doctor and Gmail must include the appropriate read-only scope.

## Install

1. Create a dedicated `roboticxs` system user.
2. Install the repository at `/opt/roboticxs` and create its virtual environment.
3. Create `/var/lib/roboticxs` owned by the service user.
4. Install `deploy/roboticxs.service.example` as `/etc/systemd/system/roboticxs.service`.
5. Put secrets in `/etc/roboticxs/roboticxs.env` with mode `0600`.
6. Place a TLS reverse proxy in front of `127.0.0.1:8080`.

## Validate before starting

```bash
python3 -m compileall -q app tests
python3 -m pytest -q tests/test_health.py tests/test_telegram_webhook.py tests/test_telegram_runtime_smoke.py tests/test_runtime_doctor_149p.py
python3 -m app.runtime_doctor --json
```

Do not start the pilot while `launch_status` is `blocked`.

## Start and verify

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now roboticxs
curl --fail http://127.0.0.1:8080/health
sudo systemctl status roboticxs --no-pager
```

Register the exact HTTPS webhook URL with Telegram only after the local health check and TLS endpoint pass. Never include the bot token in the public URL or logs.

## Stop conditions

Stop the pilot immediately on any cross-user data exposure, missing consent, approval bypass, secret exposure, destructive action, Gmail send, Calendar write, CRM write, or WhatsApp execution.
