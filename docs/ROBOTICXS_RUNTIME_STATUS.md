# Roboticxs Runtime Status

## Runtime snapshot

Roboticxs now has a real local runtime, not only planning docs.

Implemented slices include:
- Telegram text control loop
- memory proposal / approve / reject
- memory list / forget
- text-simulated document review
- document review history / forget
- file metadata intake
- file metadata list / forget
- local model routing and usage/cost scaffolding
- local budget guardrails and per-robot budget configuration
- retrieval intent / retrieval policy / retrieval-control reporting surfaces

## Enabled command families

Current runtime supports command families for:
- memory control
- document review control
- file metadata control
- budget control
- usage and spend visibility
- retrieval-intent control
- retrieval enablement request control
- retrieval-control status, history, summary, and report views

## Authority boundaries

User authority:
- approve or reject memory
- inspect and forget memory
- inspect and forget document-review records
- inspect and forget file metadata
- configure local budget policy
- reset local budget policy
- request retrieval intent
- cancel retrieval intent
- request retrieval enablement
- inspect, approve, and reject retrieval enablement requests

Robot authority:
- classify
- route
- log
- persist approved local metadata
- summarize approved local control state

Robot non-authority:
- no silent transport expansion
- no silent billing/payment behavior
- no silent provider execution
- no silent attachment-content authority

## Disabled capabilities

Explicitly disabled today:
- Telegram `getFile`
- file download
- HTTP/network attachment retrieval
- raw byte persistence
- extracted text persistence
- downloaded file path persistence
- PDF parsing
- OCR
- content review from attachment bytes
- provider execution
- billing/payment/invoice/reconciliation
- connector sync
- dashboard UI

## Retrieval status

Retrieval-control infrastructure exists to preserve trust, not as the product headline.

Current retrieval state:
- retrieval is disabled by explicit local policy
- the adapter seam is mock-only
- retrieval-related commands are metadata/control only

The retrieval-control ladder is sufficient for now and should be considered frozen unless a future approved stage reopens it.

## Stable enough to stop expanding for now

The following are now stable enough to stop expanding by default:
- retrieval policy diagnostics
- retrieval enablement request controls
- retrieval control summary/report surfaces

The next priority should be product utility, not more retrieval governance.
