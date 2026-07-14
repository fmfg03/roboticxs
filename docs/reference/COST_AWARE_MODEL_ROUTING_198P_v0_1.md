# Cost-Aware Model Routing v1 - 198P

198P adds a customer-visible local routing receipt for Economy, Balanced, and Premium task modes.

The receipt ties together:

- local model-router decision from 169P;
- local estimated usage ledger entry from 188P;
- estimated input/output tokens;
- estimated cost before a task run;
- confirmation requirement and reason;
- source trace;
- explicit authority boundaries.

## Customer behavior

Before an expensive or premium task is represented as runnable, Roboticxs can show the selected mode, provider/model estimate, estimated cost, confirmation state, and source basis.

This improves cost control and trust without switching providers or calling a live model.

## Boundaries

198P is local estimated routing only.

It does not authorize provider calls, live billing reconciliation, BYOK activation, connector activation, Telegram sends beyond existing owner-requested replies, Gmail send/archive/delete, Calendar writes, CRM writes, WhatsApp, external writes, persistence expansion, deployment, push, merge, or PR creation.

Premium mode requires explicit confirmation. Cost estimates are not live invoices.

## Local evidence

- `app/cost_aware_model_routing_v1.py`
- `tests/test_cost_aware_model_routing_v1_198p.py`
