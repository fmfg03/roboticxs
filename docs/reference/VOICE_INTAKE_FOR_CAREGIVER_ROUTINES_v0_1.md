# Voice Intake for Caregiver Routines v0.1

## Purpose

Stage 71P adds a local transcript-stub caregiver intake bridge. It accepts provided transcript text and prepares a review-only caregiver intake packet that may point to existing 68P caregiver relay packets or 69P guided routine packets.

71P does not process audio. It does not transcribe voice. It does not add Telegram voice handling, ASR runtime, VibeVoice, Whisper, TTS, voice cloning, speaker identification, voice authentication, background listening, durable transcript storage, routine execution, medication decisioning, emergency response, surveillance, or external sending.

Correct claim:

```text
Roboticxs can turn a provided voice transcript into a reviewable caregiver intake packet.
```

Forbidden claim:

```text
Roboticxs can safely act on a voice note automatically.
```

Core rule:

```text
A transcript is input evidence, not confirmation, not memory, and not execution authority.
```

## 71P policy

```json voice-caregiver-intake-policy
{
  "stage_id":"71P",
  "transcript_stub_processing_authorized":true,
  "audio_processing_authorized":false,
  "asr_runtime_authorized":false,
  "telegram_voice_processing_authorized":false,
  "vibevoice_runtime_authorized":false,
  "whisper_runtime_authorized":false,
  "external_transcription_api_authorized":false,
  "tts_authorized":false,
  "voice_clone_authorized":false,
  "speaker_identification_authorized":false,
  "voice_authentication_authorized":false,
  "background_listening_authorized":false,
  "durable_transcript_storage_authorized":false,
  "routine_execution_authorized":false,
  "external_send_authorized":false
}
```

## Source channels

```json voice-caregiver-source-channel-registry
[
  {"source_channel":"VOICE_TRANSCRIPT_STUB","accepted_in_71P":true,"notes":"Local transcript-like input supplied for intake testing or review."},
  {"source_channel":"USER_PROVIDED_TRANSCRIPT","accepted_in_71P":true,"notes":"User-provided text that represents a voice note."},
  {"source_channel":"TEST_FIXTURE_TRANSCRIPT","accepted_in_71P":true,"notes":"Test-only transcript text."},
  {"source_channel":"TELEGRAM_VOICE_FILE","accepted_in_71P":false,"notes":"Telegram voice file processing remains outside 71P."},
  {"source_channel":"AUDIO_UPLOAD","accepted_in_71P":false,"notes":"Audio upload handling remains outside 71P."},
  {"source_channel":"LIVE_MICROPHONE","accepted_in_71P":false,"notes":"Live microphone input remains outside 71P."},
  {"source_channel":"BACKGROUND_AUDIO_STREAM","accepted_in_71P":false,"notes":"Background audio streaming remains outside 71P."},
  {"source_channel":"EXTERNAL_ASR_RESULT_AUTO_ACCEPTED","accepted_in_71P":false,"notes":"External ASR output cannot be auto-accepted as confirmation."}
]
```

## Intake packet contract

```json voice-caregiver-intake-packet-contract
{
  "packet_name":"VoiceCaregiverIntakePacket",
  "required_fields":[
    "packet_id",
    "source_channel",
    "transcript_text",
    "transcript_confidence",
    "language_detected",
    "code_switching_detected",
    "caregiver_context_detected",
    "routine_intent_detected",
    "medication_adjacent_detected",
    "medical_decision_requested",
    "dosage_or_schedule_requested",
    "ingestion_verification_requested",
    "emergency_like_detected",
    "surveillance_requested",
    "external_action_requested",
    "sensitive_context_detected",
    "intake_decision",
    "requires_human_review",
    "requires_caregiver_confirmation",
    "storage_lane",
    "audio_processing_authorized",
    "asr_runtime_authorized",
    "external_send_authorized",
    "tts_authorized",
    "voice_clone_authorized",
    "background_listening_authorized",
    "durable_transcript_storage_authorized",
    "voice_authentication_authorized",
    "routine_packet_review",
    "relay_packet_review",
    "blocked_reason",
    "future_stage_required",
    "created_at"
  ],
  "required_invariants":{
    "audio_processing_authorized":false,
    "asr_runtime_authorized":false,
    "external_send_authorized":false,
    "tts_authorized":false,
    "voice_clone_authorized":false,
    "background_listening_authorized":false,
    "durable_transcript_storage_authorized":false,
    "voice_authentication_authorized":false
  },
  "storage_lane":"SESSION_ONLY_OR_DO_NOT_STORE"
}
```

## Intake decisions

```json voice-caregiver-intake-decision-registry
[
  {"decision_id":"BLOCK_EXTERNAL_ACTION","precedence":1,"allowed_effect":"local_block_notice_only","forbidden_effect":["external_send","connector_activation","browser_email_whatsapp_execution"],"requires_human_review":true},
  {"decision_id":"BLOCK_SURVEILLANCE","precedence":2,"allowed_effect":"local_block_notice_only","forbidden_effect":["background_listening","continuous_monitoring","hidden_surveillance"],"requires_human_review":true},
  {"decision_id":"BLOCK_MEDICAL_DECISION","precedence":3,"allowed_effect":"local_block_notice_only","forbidden_effect":["medication_selection","dosage_decision","schedule_decision","ingestion_verification"],"requires_human_review":true},
  {"decision_id":"ESCALATE_TO_HUMAN_CAREGIVER","precedence":4,"allowed_effect":"human_caregiver_guidance_only","forbidden_effect":["emergency_triage","routine_execution","external_send"],"requires_human_review":true},
  {"decision_id":"ASK_CLARIFICATION","precedence":5,"allowed_effect":"local_clarification_only","forbidden_effect":["routine_packet_creation","caregiver_relay_creation","memory_creation"],"requires_human_review":true},
  {"decision_id":"PREPARE_MEDICATION_ADJACENT_REVIEW","precedence":6,"allowed_effect":"review_only_medication_adjacent_packet","forbidden_effect":["medical_decision","ingestion_verification","external_send"],"requires_human_review":true},
  {"decision_id":"PREPARE_ROUTINE_PACKET_REVIEW","precedence":7,"allowed_effect":"review_only_guided_routine_packet","forbidden_effect":["routine_execution","scheduler","external_send"],"requires_human_review":true},
  {"decision_id":"PREPARE_CAREGIVER_RELAY_REVIEW","precedence":8,"allowed_effect":"review_only_caregiver_relay_packet","forbidden_effect":["telegram_send","group_management","external_send"],"requires_human_review":true},
  {"decision_id":"ROUTE_TO_CONVERSATION_CONTINUITY_REVIEW","precedence":9,"allowed_effect":"conversation_continuity_review_only","forbidden_effect":["memory_auto_save","external_send"],"requires_human_review":false},
  {"decision_id":"DISCARD_OR_NO_ACTION","precedence":10,"allowed_effect":"no_action","forbidden_effect":["storage","external_send"],"requires_human_review":false}
]
```

## Confidence policy

```json voice-caregiver-confidence-policy
[
  {"confidence_level":"UNKNOWN","can_prepare_routine_packet":false,"can_prepare_caregiver_relay":false,"requires_human_review":true,"notes":"Unknown confidence asks clarification or human review."},
  {"confidence_level":"LOW","can_prepare_routine_packet":false,"can_prepare_caregiver_relay":false,"requires_human_review":true,"notes":"Low confidence asks clarification and cannot create review packets."},
  {"confidence_level":"MEDIUM","can_prepare_routine_packet":true,"can_prepare_caregiver_relay":true,"requires_human_review":true,"notes":"Medium confidence may prepare review-only packets if safety gates pass."},
  {"confidence_level":"HIGH","can_prepare_routine_packet":true,"can_prepare_caregiver_relay":true,"requires_human_review":false,"notes":"High confidence still does not authorize action, storage, identity, or external sends."}
]
```

Medication-adjacent content requires caregiver confirmation regardless of confidence. Emergency-like content must not become a guided routine packet regardless of confidence.

## Review-only handoff

71P may prepare a local 69P guided routine packet review when the transcript is medium or high confidence, routine-like, non-emergency, non-surveillance, non-external-action, and not a medical decision request. The 69P packet must keep its existing invariants: no external send, no background reminders, no medical decision, no dosage decision, no medication scheduling, no ingestion verification, no emergency claim, no surveillance, and session-only progress.

71P may prepare a local 68P caregiver relay packet review for medication-adjacent, sensitive, emergency-like, or caregiver-status context. The 68P packet must keep its existing invariants: no external send, no medical decision, no emergency claim, and no routine execution.

No relay packet may be sent.

## Memory boundary

Transcript text is session-only. No raw audio is stored. No transcript is stored durably. No sensitive caregiver transcript becomes memory. No voice-derived inference becomes fact. No transcript becomes confirmed memory. Any future memory proposal must use the existing memory approval flow.

Default storage lane:

```text
SESSION_ONLY_OR_DO_NOT_STORE
```

## Required non-claims

- Roboticxs does not process audio in 71P.
- Roboticxs does not transcribe voice in 71P.
- Roboticxs does not handle Telegram voice files in 71P.
- Roboticxs does not run VibeVoice or Whisper in 71P.
- Roboticxs does not identify or authenticate speakers in 71P.
- Roboticxs does not treat a transcript as user confirmation.
- Roboticxs does not store transcripts durably in 71P.
- Roboticxs does not execute routines from voice intake.
- Roboticxs does not send caregiver messages automatically.
- Roboticxs does not make medication decisions.
- Roboticxs does not provide emergency response.
- Roboticxs does not perform surveillance or background listening.

## Closeout transition

After 71P closes, 72P Research Radar / Last30Days Skill becomes the next eligible stage. 71P does not implement 72P behavior.

## Validation

- `python3 -m compileall app tests`
- `python3 -m pytest -q tests/test_voice_caregiver_intake.py`
- `python3 -m pytest -q tests/test_voice_notes_intelligence_spike.py`
- `python3 -m pytest -q tests/test_guided_routines.py`
- `python3 -m pytest -q tests/test_caregiver_relay.py`
- `python3 -m pytest -q tests/test_caregiver_mode_boundary.py`
- `python3 -m pytest -q tests/test_memory_stack_architecture.py`
- `python3 -m pytest -q tests/test_conversation_continuity_spine.py`
- `python3 -m pytest -q tests/test_budget_authority_guard.py`
- `python3 -m pytest -q tests/test_canonical_roadmap.py`
- `python3 -m pytest -q tests/test_runtime_surface_audit.py`
- `python3 -m pytest -q tests/test_retrieval_control_freeze.py`
- `python3 -m pytest -q`
- `git diff -- app`
- `git diff --check`
- `git status --short`
