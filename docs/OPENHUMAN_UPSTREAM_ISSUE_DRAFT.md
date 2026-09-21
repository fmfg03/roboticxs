# openhuman_embed Agent.turn() rejected by hosted policy before provider invocation

We are embedding OpenHuman through its documented public library API.

At OpenHuman `61e80bea0dbe92cb45868737a5db56a5a840a0d3`, a minimal public
`Runtime -> Agent` turn with `Access::full()`, an explicit origin supplied by
that access preset, no tools, and an OpenAI-compatible wiremock provider fails
before the provider receives a request.

Expected: one provider call returning `pong`.

Actual: `hosted agent invocation was rejected by policy`; provider calls: zero.

Environment: Ubuntu 24.04 kernel `6.8.0-139-generic`, rustc `1.98.1`, cargo
`1.98.1`. The self-contained reproducer is `repro/openhuman-embed-policy`.

Source trace: public `Turn::send` dispatches `agent_chat_for`, which reaches
`root_hosted_harness().invoke_agent`. `tinyagents-harness::hosted_error`
maps any `TinyAgentsError::Validation` or `Steering` failure to the fixed
sanitized message above, losing the underlying policy diagnostic.

The same outcome was observed with `Access::readonly()` and with the public
`openhuman_tinyhumans::RuntimeBuilder` plus a local simulated backend.
