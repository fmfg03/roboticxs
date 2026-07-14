# Telegram Document Intake Stub 158P v0.1

`158P - Telegram Document Intake Stub v0` lets the Telegram runtime acknowledge document metadata from an owner-gated Telegram update.

## Scope

- recognize Telegram `message.document` metadata;
- render a customer-facing `Document Intake` reply;
- show filename, MIME type, and size when Telegram provides them;
- explain that document review is draft-only;
- say the robot can later summarize, prepare meeting notes, or flag risks.

## Authority

158P does not download files, parse content, run OCR, summarize documents, flag risks, persist document state, mutate Memory Center, write ProposedMemory, call models, call tools, dispatch workers, activate connectors, read Calendar or Gmail, write Calendar or Gmail, bill, deploy, push, merge, create a PR, or perform external writes beyond approved Telegram replies.

## Customer Reply

The reply must say:

- `I received Telegram metadata only.`
- `Document review is currently draft-only.`
- `File downloaded: false`
- `Content parsed: false`
- `External writes: disabled`
