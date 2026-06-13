# VoxCPM Research Parking Lot v0.1

## Status

Stage 76P parks VoxCPM and VoxCPM2 as `RESEARCH_ONLY`.

This is a local research assessment only. It does not install VoxCPM, activate VoxCPM, download model weights, run inference, process audio, generate audio, clone voices, or claim VoxCPM support in Roboticxs.

## Decision

VoxCPM is parked as RESEARCH_ONLY.
VoxCPM2 is parked as RESEARCH_ONLY.
The upstream repository is an external research source, not a Roboticxs dependency.
The arXiv papers are source references, not product truth.

Roboticxs approval status: RESEARCH_ONLY.
Source status: EXTERNAL_RESEARCH_SOURCE.

## Required source references

| Source | Status | Reference |
| --- | --- | --- |
| Upstream repository | EXTERNAL_RESEARCH_SOURCE | https://github.com/OpenBMB/VoxCPM |
| Upstream owner | EXTERNAL_RESEARCH_SOURCE | OpenBMB |
| VoxCPM arXiv source | EXTERNAL_RESEARCH_SOURCE | https://arxiv.org/abs/2509.24650 |
| VoxCPM arXiv ID | EXTERNAL_RESEARCH_SOURCE | arXiv:2509.24650 |
| VoxCPM2 technical report | EXTERNAL_RESEARCH_SOURCE | https://arxiv.org/abs/2606.06928 |
| VoxCPM2 arXiv ID | EXTERNAL_RESEARCH_SOURCE | arXiv:2606.06928 |

These references may be used only for future research evaluation. They do not authorize dependency installation, model execution, product claims, or runtime behavior.

## Why this exists

Voice remains relevant to Roboticxs because future caregiver, household, and personal-admin workflows may need voice strategy decisions. VoxCPM and VoxCPM2 are worth parking because upstream public materials describe text-to-speech, multilingual speech generation, voice design, controllable cloning, and audio generation capabilities.

Those capabilities are sensitive. Roboticxs v0 already blocks cloned voice and does not have approved voice runtime authority. Stage 76P exists to preserve the research signal while keeping the runtime boundary closed.

## What upstream materials appear to describe

The upstream OpenBMB repository identifies VoxCPM2 as a tokenizer-free TTS system for multilingual speech generation, creative voice design, and true-to-life cloning.

The upstream repository describes VoxCPM2 as a 2B parameter model with 30-language support, Voice Design, Controllable Voice Cloning, 48kHz audio output, streaming-related claims, Apache-2.0 release, and quick-start examples for installation, Python API usage, CLI usage, web demo usage, and serving.

The VoxCPM paper at `arXiv:2509.24650` is titled "VoxCPM: Tokenizer-Free TTS for Context-Aware Speech Generation and True-to-Life Voice Cloning" and was submitted on September 29, 2025.

VoxCPM2 is a newer multilingual controllable speech generation model described by upstream public materials. The separate VoxCPM2 technical-report source parked by 76P is `arXiv:2606.06928` at `https://arxiv.org/abs/2606.06928`. Roboticxs must avoid claims beyond the exact upstream repository and paper/report sources.

This repository has not installed, executed, benchmarked, or audited VoxCPM or VoxCPM2. These observations are parking-lot assessment notes, not verified integration claims.

## Potential Roboticxs value

- Future voice strategy evaluation.
  Status: CANDIDATE_ONLY
  Requires: future voice strategy decision + privacy review + authority policy
- Multilingual speech-generation research.
  Status: CANDIDATE_ONLY
  Requires: future voice strategy decision + privacy review + authority policy
- Voice-design capability assessment.
  Status: CANDIDATE_ONLY
  Requires: explicit identity and consent policy before any future consideration
- Caregiver voice UX research.
  Status: CANDIDATE_ONLY
  Requires: caregiver safety policy + user consent + no emergency reliance
- Local-vs-hosted voice architecture comparison.
  Status: CANDIDATE_ONLY
  Requires: budget policy + hardware policy + privacy review
- Voice cloning risk assessment.
  Status: CANDIDATE_ONLY
  Requires: identity, consent, abuse, and impersonation review

## Hard boundaries

- No runtime integration.
- No production dependency.
- No development dependency.
- No model download.
- No model weights.
- No inference.
- No TTS execution.
- No audio generation.
- No voice cloning.
- No voice design runtime.
- No speaker authentication.
- No speaker identification.
- No Telegram voice handling.
- No audio upload handling.
- No raw audio storage.
- No generated audio storage.
- No durable transcript storage.
- No background listening.
- No streaming audio runtime.
- No local web demo.
- No server process.
- No OpenAI-compatible audio endpoint.
- No CUDA, PyTorch, vLLM, Nano-vLLM, ModelScope, or Hugging Face integration.
- No connector registration.
- No MCP server registration.
- No external API calls.
- No user-facing commands.
- No capability catalog activation.
- No automatic roadmap promotion.
- No claims that Roboticxs supports VoxCPM or VoxCPM2.

## Blocked for now

- Installing `voxcpm` is blocked.
- Installing `modelscope` for VoxCPM is blocked.
- Installing Nano-vLLM or vLLM-Omni for VoxCPM is blocked.
- Adding VoxCPM to `pyproject.toml` or any lockfile is blocked.
- Downloading `openbmb/VoxCPM2` or any related weights is blocked.
- Running repository quick-start examples is blocked.
- Running a VoxCPM web demo is blocked.
- Running a VoxCPM serving endpoint is blocked.
- Processing user audio through VoxCPM is blocked.
- Generating synthetic speech is blocked.
- Cloning a voice from reference audio is blocked.
- Designing a voice from natural-language description is blocked.
- Adding Telegram voice-note handling is blocked.
- Adding voice command routing is blocked.
- Adding voice memory proposals is blocked.
- Adding caregiver voice runtime behavior is blocked.
- Marking VoxCPM as an approved integration is blocked.

## Risk register

| Risk | Required treatment |
| --- | --- |
| Identity and impersonation risk | Voice cloning remains blocked until explicit identity and consent policy exists |
| Consent risk | Any future voice path requires explicit user consent and source ownership review |
| Caregiver safety risk | Must not be used for emergency, medication, monitoring, or surveillance behavior |
| Privacy risk | Raw audio and transcripts remain blocked without a separate storage policy |
| Dependency risk | Heavy ML dependencies require separate supply-chain and hardware review |
| Model-weight risk | Model downloads remain blocked until storage, license, and audit policy exists |
| Runtime cost risk | GPU, latency, and serving costs require budget authority before integration |
| Source reliability risk | Upstream claims must be labeled as upstream claims, not Roboticxs-verified facts |
| Abuse risk | Voice design and cloning require misuse review before any future approval |
| User misunderstanding | UX must not imply Roboticxs can generate or clone voices |

## Authority implications

Any future VoxCPM-style capability must separate:

```text
READ_EXTERNAL_SOURCE
EVALUATE_VOICE_MODEL
DOWNLOAD_MODEL
RUN_INFERENCE
GENERATE_AUDIO
CLONE_VOICE
STORE_AUDIO
SEND_AUDIO
AUTHENTICATE_SPEAKER
```

Only `READ_EXTERNAL_SOURCE` and `EVALUATE_VOICE_MODEL` are candidates for research evaluation.

`DOWNLOAD_MODEL`, `RUN_INFERENCE`, `GENERATE_AUDIO`, `CLONE_VOICE`, `STORE_AUDIO`, `SEND_AUDIO`, and `AUTHENTICATE_SPEAKER` remain blocked unless future stages define explicit authority policy, privacy review, consent controls, tests, and validation.

## Privacy implications

Future voice capability would need explicit consent, reference-audio ownership rules, raw-audio retention limits, transcript retention limits, generated-audio retention limits, speaker identity boundaries, misuse review, and clear disclosure when any audio model is used.

76P enables none of that behavior.

## Budget implications

Future voice capability would need budget limits for model download/storage, GPU runtime, inference duration, serving concurrency, retries, generated-audio volume, provider/API use, and hardware requirements.

76P adds no budget-consuming runtime path.

## Connector implications

VoxCPM is not approved as a connector.

VoxCPM2 is not approved as a connector.

Any future model adapter would need registration policy, model-source allowlists, dependency review, audit logs, consent checks, disable controls, and review before activation.

## Memory implications

VoxCPM is not approved for memory ingestion.

Future voice output, transcripts, prompts, reference audio, speaker descriptions, or model findings must not create `MemoryItem` records, `ProposedMemory` records, or durable user facts automatically. Any memory proposal path would require a later approved stage and explicit user review.

## Runtime implications

No voice runtime is enabled.

Future voice work must not change Telegram handling, command routing, `app/` runtime behavior, model routing, budget enforcement, memory flow, caregiver flow, or safety flow without a separate approved implementation stage.

## Future adapter requirements

A future controlled adapter would require:

- explicit story and technical spec approval;
- identity and consent policy;
- reference-audio ownership rules;
- voice-cloning abuse review;
- privacy review;
- budget and hardware policy;
- dependency and model-weight supply-chain review;
- model-source allowlists;
- generated-audio labeling;
- raw-audio, transcript, and generated-audio retention policy;
- no memory or retrieval writes without separate approval;
- explicit user approval before any external send;
- tests that prove blocked operations remain blocked.

## Open questions

- Does Roboticxs need speech generation at all for v0, or only transcript intake?
- Would any future voice work use local models, hosted APIs, or no synthesis?
- What consent model is required for reference audio?
- How should generated voices be labeled to prevent impersonation?
- What retention policy would apply to raw audio and generated audio?
- What caregiver safety boundary is required before voice UX?
- Which hardware and budget constraints would make local inference unacceptable?
- What future stage, if any, should own voice strategy beyond research parking?

## Recommended next stage

No local next eligible implementation stage is authorized after 76P.

Do not invent 77P unless explicit maintainer direction exists in repository evidence and the canonical roadmap is updated through the required story, technical-spec, implementation, tests, and validation checkpoints.

## Non-claims

- Roboticxs does not support VoxCPM in runtime.
- Roboticxs does not support VoxCPM2 in runtime.
- Roboticxs does not ship VoxCPM as a dependency.
- Roboticxs does not download VoxCPM or VoxCPM2 model weights.
- Roboticxs does not run VoxCPM or VoxCPM2 inference.
- Roboticxs does not generate audio through VoxCPM.
- Roboticxs does not clone voices.
- Roboticxs does not perform voice design.
- Roboticxs does not process Telegram voice notes through VoxCPM.
- Roboticxs does not store raw audio, generated audio, or durable transcripts in 76P.
- Roboticxs does not expose user-facing VoxCPM commands in 76P.
- Roboticxs does not activate connectors, MCP, external APIs, or serving endpoints in 76P.
- Roboticxs does not canonize upstream VoxCPM claims as product truth.
