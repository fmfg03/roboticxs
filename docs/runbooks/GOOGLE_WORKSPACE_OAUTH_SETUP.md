# Google Workspace OAuth Setup

This runbook configures Roboticxs for Google Calendar and Gmail read-only OAuth without committing secrets.

## Boundaries

- Do not paste `client_secret`, authorization codes, access tokens, or refresh tokens into chat.
- Keep OAuth files under `/root/roboticxs/.secrets/`.
- Calendar starts read-only with `https://www.googleapis.com/auth/calendar.readonly`.
- Gmail defaults to metadata-only with `https://www.googleapis.com/auth/gmail.metadata`.
- Use `--gmail-mode readonly` only when Roboticxs must read email body content.
- Google classifies Gmail `metadata` and `readonly` as restricted scopes; keep this as an owner/test-user pilot unless the app goes through the required verification and security assessment path.

## Google Cloud setup

1. In Google Cloud Console, select the Roboticxs project or create one.
2. Enable the Google Calendar API.
3. Enable the Gmail API.
4. Configure the OAuth consent screen. While testing, add the owner Google account as a test user.
5. Create an OAuth client of type `Desktop app`.
6. Download the client JSON.
7. Place it on the VM:

```bash
mkdir -p /root/roboticxs/.secrets
chmod 700 /root/roboticxs/.secrets
# Save the downloaded JSON as:
# /root/roboticxs/.secrets/google_oauth_client.json
chmod 600 /root/roboticxs/.secrets/google_oauth_client.json
```

## VM OAuth bootstrap

From local PowerShell, open an SSH session with loopback forwarding:

```powershell
ssh -i C:\Users\ffg\.ssh\codex_vm_root_ed25519_20260624 -L 8765:127.0.0.1:8765 root@95.216.70.50
```

Inside that SSH session:

```bash
cd /root/roboticxs
python3 -m app.google_oauth_local_setup --gmail-mode metadata
```

Open the printed Google authorization URL in the local browser. After consent, Google redirects to `127.0.0.1:8765`; the SSH tunnel forwards the callback to the VM process, which writes:

```text
/root/roboticxs/.secrets/google_workspace_token.json
```

## Environment

Roboticxs reads these defaults automatically from the repo root:

```bash
export ROBOTICXS_GOOGLE_OAUTH_CLIENT_SECRETS_FILE=/root/roboticxs/.secrets/google_oauth_client.json
export ROBOTICXS_GOOGLE_OAUTH_TOKEN_FILE=/root/roboticxs/.secrets/google_workspace_token.json
```

The legacy direct-token override still works:

```bash
export ROBOTICXS_GOOGLE_CALENDAR_ACCESS_TOKEN=ya29...
```

## Smoke checks

```bash
cd /root/roboticxs
python3 -m app.google_calendar_readonly_connector
python3 -m app.real_calendar_meeting_brief
```

Expected result: Calendar commands read real events and report read-only boundaries. No Calendar event, email, memory, external write, model call, or worker dispatch is performed.
