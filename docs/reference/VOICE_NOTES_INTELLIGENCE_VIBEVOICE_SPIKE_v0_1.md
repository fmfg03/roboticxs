# Voice Notes Intelligence / VibeVoice Spike v0.1

## Purpose

Stage 70P defines the voice-note intelligence boundary for Roboticxs before any caregiver voice intake is implemented. Voice notes are treated as an input modality that may later produce text, memory proposals, routine-packet review drafts, or caregiver-relay review drafts. Voice transcription is not execution authority.

70P is a research spike, architecture boundary, structured registry, and test baseline. It does not authorize audio upload handling, Telegram voice attachment processing, ASR inference, model download, external audio API calls, TTS, cloned voice, speaker identification, voice authentication, background listening, audio storage, durable transcript storage, caregiver voice runtime, or external sends.

Correct claim:

```text
Roboticxs can prepare voice-note intelligence boundaries so future stages can turn approved voice notes into safe text, memory proposals, routine packets, or caregiver relay packets.
```

Forbidden claim:

```text
Roboticxs can safely understand, identify, imitate, or act on voice automatically.
```

## Voice spike policy

```json voice-spike-policy
{
  "stage_id":"70P",
  "voice_runtime_authorized":false,
  "audio_upload_handling_authorized":false,
  "asr_inference_authorized":false,
  "external_audio_api_authorized":false,
  "model_download_authorized":false,
  "model_weights_authorized":false,
  "tts_authorized":false,
  "voice_clone_authorized":false,
  "speaker_identification_authorized":false,
  "voice_authentication_authorized":false,
  "background_listening_authorized":false,
  "raw_audio_durable_storage_authorized":false,
  "durable_transcript_storage_authorized":false,
  "caregiver_voice_runtime_authorized":false,
  "external_send_authorized":false
}
```

## Research summary

VibeVoice-ASR is relevant to Roboticxs because Microsoft describes it as a unified long-form speech-to-text model that can process up to 60 minutes in one pass and return structured transcription with speaker, timestamp, and content fields. The VibeVoice-ASR technical report describes the same direction: long-form speech recognition, speaker diarization, timestamping, multilingual and code-switching support, and prompt-based context injection for domain terms or hotwords.

Those capabilities are useful only as future evaluation signals for Roboticxs. Telegram voice notes may include Spanish, Mexican Spanish, code switching, family names, routine terms, noisy audio, multiple speakers, caregiver context, medication-adjacent discussion, or emergency-like language. A future ASR provider must therefore be judged on accuracy, latency, privacy, retention, hardware, language coverage, confidence behavior, diarization reliability, and cost before any runtime stage opens.

VibeVoice-TTS is not the Roboticxs v0 target. Microsoft describes VibeVoice as a family that includes TTS and ASR, and the TTS side is designed for long-form multi-speaker speech generation. Microsoft also documents misuse risk for synthetic speech, including deepfake and disinformation concerns. For Roboticxs v0, speech generation, generated caregiver voices, TTS, and voice cloning are blocked because they create identity and impersonation risk that is unrelated to voice-note intake.

Speaker labels are not identity verification. Transcription confidence does not equal action authority. Voice-derived memory candidates require the same approval path as text-derived memory. Voice caregiver content remains sensitive and session-only unless a future approved stage changes that. Voice cost must be governed before long or multi-speaker audio processing. Stage 71P may open caregiver voice intake only after 70P closes.

## Research source register

```json voice-research-source-register
[
  {"source_id":"microsoft_vibevoice_repo","category":"VOICE_ASR","title":"microsoft/VibeVoice repository","organization_or_origin":"Microsoft","source_type":"primary_repository","research_use":"Source for VibeVoice family, ASR/TTS separation, model availability, and documented risks.","boundary_implication":"Repository evidence supports evaluation only; it does not authorize Roboticxs model download, inference, TTS, or voice cloning."},
  {"source_id":"vibevoice_asr_technical_report","category":"VOICE_ASR","title":"VIBEVOICE-ASR Technical Report","organization_or_origin":"Microsoft Research authors on arXiv","source_type":"technical_report","research_use":"Source for long-form ASR, diarization, timestamps, multilingual/code-switching, and prompt/context hotword claims.","boundary_implication":"ASR may be evaluated later for structured transcript packets; 70P does not integrate it."},
  {"source_id":"vibevoice_tts_technical_report","category":"VOICE_TTS","title":"VibeVoice Technical Report","organization_or_origin":"Microsoft Research authors on arXiv","source_type":"technical_report","research_use":"Source for long-form multi-speaker speech synthesis capabilities and TTS scope.","boundary_implication":"TTS capability is explicitly separated from voice-note transcription and blocked for Roboticxs v0."},
  {"source_id":"vibevoice_tts_docs","category":"VOICE_TTS","title":"VibeVoice TTS documentation and model cards","organization_or_origin":"Microsoft / Hugging Face","source_type":"documentation","research_use":"Source for text-to-speech task framing, model availability, language notes, and deployment implications.","boundary_implication":"TTS and synthetic caregiver voice remain blocked; model availability is not implementation authority."},
  {"source_id":"roboticxs_project_brief","category":"PRODUCT_BOUNDARY","title":"ROBOTICXS_PROJECT_BRIEF.md","organization_or_origin":"Roboticxs local repository","source_type":"local_product_context","research_use":"Defines Telegram-first robot context and product boundaries.","boundary_implication":"Voice notes support the robot input modality only; they do not add autonomous action authority."},
  {"source_id":"roboticxs_66p2_memory_boundary","category":"MEMORY_BOUNDARY","title":"Memory Stack Architecture / Criterio Store Spec","organization_or_origin":"Roboticxs local repository","source_type":"local_reference_spec","research_use":"Defines memory lane, approval, sensitive inference, and session-only boundaries.","boundary_implication":"Voice-derived memory candidates must follow the same proposal and approval path as text-derived memory."},
  {"source_id":"roboticxs_67p_caregiver_boundary","category":"CAREGIVER_BOUNDARY","title":"Caregiver Mode Boundary Spec","organization_or_origin":"Roboticxs local repository","source_type":"local_reference_spec","research_use":"Defines caregiver safety, no medical advice, no emergency triage, and no surveillance boundaries.","boundary_implication":"Caregiver voice content requires review and cannot authorize medical, emergency, surveillance, or caregiver runtime behavior."},
  {"source_id":"roboticxs_68p_relay_boundary","category":"RELAY_BOUNDARY","title":"Caregiver Telegram Group Relay v0","organization_or_origin":"Roboticxs local repository","source_type":"local_reference_spec","research_use":"Defines relay packets as local drafts only.","boundary_implication":"Voice-derived relay candidates can prepare review packets only and cannot send externally."},
  {"source_id":"roboticxs_69p_guided_routine_boundary","category":"ROUTINE_BOUNDARY","title":"Guided Routine Packets v0","organization_or_origin":"Roboticxs local repository","source_type":"local_reference_spec","research_use":"Defines guided routine packet boundaries, no medication execution, and no scheduler/runtime authority.","boundary_implication":"Voice-derived routine candidates can only prepare review packets after confidence and caregiver safety gates."}
]
```

## Technology candidate registry

```json voice-technology-candidate-registry
[
  {"candidate_id":"VIBEVOICE_ASR","candidate_type":"ASR","potential_use":"Future structured long-form transcript evaluation for approved voice notes.","benefits":["long_form_asr","speaker_diarization","timestamps","customized_hotwords","multilingual_support","code_switching_support"],"risks":["model_size","hardware_requirements","latency","spanish_accuracy_unknown","elderly_speech_accuracy_unknown","noisy_telegram_audio_accuracy_unknown","privacy_retention_review_required","license_and_model_availability_review_required","supply_chain_risk","speaker_label_misattribution"],"implementation_status":"EVALUATION_ONLY","authorized_in_70P":false,"future_evaluation_required":true,"blocked_reason":"70P is docs/tests only and does not authorize ASR inference, model download, model weights, or audio runtime."},
  {"candidate_id":"OPENAI_TRANSCRIPTION","candidate_type":"MANAGED_ASR","potential_use":"Future managed ASR candidate for short approved voice notes if privacy and cost authority are approved.","benefits":["managed_operation","no_local_gpu_requirement","likely_fast_path_for_short_notes"],"risks":["external_audio_api","privacy_review_required","retention_terms_required","cost_authority_required","provider_dependency"],"implementation_status":"NOT_SELECTED","authorized_in_70P":false,"future_evaluation_required":true,"blocked_reason":"External audio API calls are not authorized in 70P."},
  {"candidate_id":"LOCAL_WHISPER_OR_FASTER_WHISPER","candidate_type":"LOCAL_ASR","potential_use":"Future privacy spike candidate for local ASR without external audio API calls.","benefits":["local_processing_possible","broad_language_support_candidate","mature_ecosystem"],"risks":["dependency_and_model_weight_addition","hardware_cost","accuracy_validation_required","maintenance_burden","diarization_may_require_extra_stack"],"implementation_status":"NOT_SELECTED","authorized_in_70P":false,"future_evaluation_required":true,"blocked_reason":"70P does not authorize Whisper dependencies, model weights, or inference."},
  {"candidate_id":"CLOUD_SPEECH_PROVIDER","candidate_type":"MANAGED_ASR","potential_use":"Future enterprise/cloud speech provider comparison after privacy, retention, and cost review.","benefits":["operational_maturity","diarization_options","language_options","support_contracts_possible"],"risks":["external_audio_api","data_residency_review_required","vendor_lock_in","cost_variability","retention_terms_required"],"implementation_status":"NOT_SELECTED","authorized_in_70P":false,"future_evaluation_required":true,"blocked_reason":"Cloud speech provider calls are not authorized in 70P."},
  {"candidate_id":"NO_VOICE_FOR_NOW","candidate_type":"PRODUCT_OPTION","potential_use":"Keep voice intake closed until evidence, privacy, cost, and caregiver boundaries are sufficient.","benefits":["lowest_privacy_risk","lowest_cost_risk","no_runtime_expansion","preserves_current_text_boundaries"],"risks":["voice_note_user_friction_remains","caregiver_intake_delayed"],"implementation_status":"EVALUATION_ONLY","authorized_in_70P":false,"future_evaluation_required":false,"blocked_reason":"This is the default no-runtime stance for 70P."},
  {"candidate_id":"VIBEVOICE_TTS_REJECTED_FOR_V0","candidate_type":"TTS","potential_use":"None in Roboticxs v0.","benefits":["not_used_for_v0"],"risks":["identity_impersonation","deepfake_risk","synthetic_caregiver_voice_risk","user_confusion","misleading_generated_audio"],"implementation_status":"REJECTED_FOR_V0","authorized_in_70P":false,"future_evaluation_required":false,"blocked_reason":"TTS and generated or cloned voice are outside the Roboticxs v0 identity and caregiver boundary."},
  {"candidate_id":"VOXCPM_PARKING_LOT","candidate_type":"VOICE_MODEL_PARKING_LOT","potential_use":"No current use; possible later research-only comparison if voice strategy reopens.","benefits":["future_research_optional"],"risks":["premature_provider_selection","voice_strategy_drift","privacy_and_authority_unknowns"],"implementation_status":"PARKING_LOT","authorized_in_70P":false,"future_evaluation_required":true,"blocked_reason":"VoxCPM remains a parking-lot candidate only."}
]
```

## Voice note packet contract

Future stages may generate a `VoiceNoteIntelligencePacket` only after an approved runtime story and spec. 70P defines the contract but does not generate packets.

```json voice-note-packet-contract
{
  "packet_name":"VoiceNoteIntelligencePacket",
  "required_fields":[
    "packet_id",
    "source_channel",
    "audio_ref",
    "audio_retention_policy",
    "transcript_text",
    "transcript_confidence",
    "language_detected",
    "code_switching_detected",
    "speaker_labels_available",
    "speaker_labels_confidence",
    "timestamps_available",
    "hotwords_used",
    "sensitivity_level",
    "contains_caregiver_context",
    "contains_medication_adjacent_content",
    "contains_emergency_like_content",
    "contains_external_action_request",
    "contains_memory_candidate",
    "downstream_decision",
    "requires_human_review",
    "requires_caregiver_confirmation",
    "storage_lane",
    "external_send_authorized",
    "tts_authorized",
    "voice_clone_authorized",
    "background_listening_authorized",
    "created_at"
  ],
  "required_invariants":{
    "external_send_authorized":false,
    "tts_authorized":false,
    "voice_clone_authorized":false,
    "background_listening_authorized":false
  }
}
```

## Downstream decision registry

Voice notes do not bypass 66P classification, 66P2 memory approval, 67P caregiver boundaries, 68P relay no-send invariants, or 69P guided routine no-medical/no-scheduler invariants.

```json voice-downstream-decision-registry
[
  {"decision_id":"ASK_CLARIFICATION","description":"Ask the user to clarify unclear, low-confidence, ambiguous, or sensitive voice-derived text.","allowed_effect":"local_clarification_prompt_only","forbidden_effect":["memory_creation","routine_packet_creation","caregiver_relay_creation","external_send"],"requires_human_review":false,"requires_caregiver_confirmation":false,"storage_lane":"SESSION_ONLY_OR_DO_NOT_STORE","downstream_stage":"66P"},
  {"decision_id":"ROUTE_TO_CONVERSATION_CONTINUITY","description":"Route safe transcript text into normal 66P conversation continuity classification.","allowed_effect":"conversation_classification_only","forbidden_effect":["external_send","durable_sensitive_memory","routine_execution"],"requires_human_review":false,"requires_caregiver_confirmation":false,"storage_lane":"SESSION_ONLY_OR_DO_NOT_STORE","downstream_stage":"66P"},
  {"decision_id":"PROPOSE_MEMORY_REVIEW","description":"Prepare a reviewable memory proposal only when confidence and sensitivity gates allow it.","allowed_effect":"memory_proposal_review_only","forbidden_effect":["auto_memory_save","external_send","sensitive_memory_without_approval"],"requires_human_review":true,"requires_caregiver_confirmation":false,"storage_lane":"CURRENT_ROBOTICXS_MEMORY_FLOW","downstream_stage":"66P2"},
  {"decision_id":"PREPARE_ROUTINE_PACKET_REVIEW","description":"Prepare a guided routine packet for review only after confidence, safety, and caregiver boundaries pass.","allowed_effect":"local_routine_packet_review_only","forbidden_effect":["routine_execution","scheduler","medication_decision","external_send"],"requires_human_review":true,"requires_caregiver_confirmation":false,"storage_lane":"SESSION_ONLY_OR_DO_NOT_STORE","downstream_stage":"69P"},
  {"decision_id":"PREPARE_CAREGIVER_RELAY_REVIEW","description":"Prepare a caregiver relay draft for review without sending it.","allowed_effect":"local_caregiver_relay_review_only","forbidden_effect":["telegram_send","group_management","external_send","medical_decision"],"requires_human_review":true,"requires_caregiver_confirmation":true,"storage_lane":"SESSION_ONLY_OR_DO_NOT_STORE","downstream_stage":"68P"},
  {"decision_id":"ESCALATE_TO_HUMAN_CAREGIVER","description":"Escalate sensitive caregiver or medication-adjacent content to human caregiver review without taking action.","allowed_effect":"human_review_guidance_only","forbidden_effect":["medical_advice","routine_execution","external_send","emergency_claim"],"requires_human_review":true,"requires_caregiver_confirmation":true,"storage_lane":"SESSION_ONLY_OR_DO_NOT_STORE","downstream_stage":"67P"},
  {"decision_id":"BLOCK_MEDICAL_OR_EMERGENCY_DECISION","description":"Block medical or emergency-like interpretation and provide human caregiver or emergency-services guidance.","allowed_effect":"block_and_human_guidance_only","forbidden_effect":["routine_handling","medical_decision","triage","external_send"],"requires_human_review":true,"requires_caregiver_confirmation":true,"storage_lane":"SESSION_ONLY_OR_DO_NOT_STORE","downstream_stage":"67P"},
  {"decision_id":"BLOCK_EXTERNAL_ACTION","description":"Block any voice-derived request to send, contact, publish, browse, email, message, or write externally.","allowed_effect":"local_block_notice_only","forbidden_effect":["external_send","connector_activation","browser_email_whatsapp_execution"],"requires_human_review":true,"requires_caregiver_confirmation":false,"storage_lane":"SESSION_ONLY_OR_DO_NOT_STORE","downstream_stage":"68P"},
  {"decision_id":"DISCARD_AUDIO","description":"Discard audio when policy, consent, retention, sensitivity, or budget gates do not allow processing.","allowed_effect":"delete_or_ignore_audio_reference","forbidden_effect":["transcript_storage","audio_storage","external_send","model_inference_loop"],"requires_human_review":false,"requires_caregiver_confirmation":false,"storage_lane":"SESSION_ONLY_OR_DO_NOT_STORE","downstream_stage":"70P"}
]
```

## Confidence policy

```json voice-confidence-policy
[
  {"confidence_level":"UNKNOWN","can_create_memory_proposal":false,"can_prepare_routine_packet":false,"can_prepare_caregiver_relay":false,"requires_human_review":true,"notes":"Unknown confidence can only ask for clarification or human review."},
  {"confidence_level":"LOW","can_create_memory_proposal":false,"can_prepare_routine_packet":false,"can_prepare_caregiver_relay":false,"requires_human_review":true,"notes":"Low confidence cannot create memory, routine, or relay packets and should map to clarification or review."},
  {"confidence_level":"MEDIUM","can_create_memory_proposal":true,"can_prepare_routine_packet":true,"can_prepare_caregiver_relay":true,"requires_human_review":true,"notes":"Medium confidence may prepare review packets only; sensitive, medication-adjacent, caregiver, or emergency-like content adds stricter review."},
  {"confidence_level":"HIGH","can_create_memory_proposal":true,"can_prepare_routine_packet":true,"can_prepare_caregiver_relay":true,"requires_human_review":false,"notes":"High confidence does not authorize sensitive action, external sends, durable sensitive memory, medication decisions, or identity proof."}
]
```

Low-confidence transcript text cannot create memory, caregiver relay, or guided routine packets without clarification or human review. Medication-adjacent content requires human or caregiver review regardless of confidence. Emergency-like content must not be handled as routine. Transcript text must not be treated as user confirmation for sensitive action.

## Privacy and retention policy

Default stance:

```text
Do not store raw audio by default.
Do not store transcripts durably by default.
Use transcript text only to create reviewable packets or memory proposals.
Sensitive caregiver transcripts are session-only unless future approval says otherwise.
```

```json voice-privacy-retention-policy
[
  {"data_class":"RAW_AUDIO","default_retention":"SESSION_ONLY_DELETE_AFTER_PROCESSING","durable_storage_authorized_in_70P":false,"redaction_required":false,"delete_after_processing_default":true,"future_approval_required":true},
  {"data_class":"TRANSCRIPT_TEXT","default_retention":"SESSION_ONLY","durable_storage_authorized_in_70P":false,"redaction_required":true,"delete_after_processing_default":true,"future_approval_required":true},
  {"data_class":"SENSITIVE_CAREGIVER_TRANSCRIPT","default_retention":"SESSION_ONLY_OR_DO_NOT_STORE","durable_storage_authorized_in_70P":false,"redaction_required":true,"delete_after_processing_default":true,"future_approval_required":true},
  {"data_class":"SPEAKER_LABELS","default_retention":"SESSION_ONLY_NOT_IDENTITY","durable_storage_authorized_in_70P":false,"redaction_required":true,"delete_after_processing_default":true,"future_approval_required":true},
  {"data_class":"HOTWORDS","default_retention":"SESSION_ONLY_OR_USER_APPROVED_CONFIG_LATER","durable_storage_authorized_in_70P":false,"redaction_required":true,"delete_after_processing_default":true,"future_approval_required":true},
  {"data_class":"VOICE_METADATA","default_retention":"SESSION_ONLY_MINIMAL","durable_storage_authorized_in_70P":false,"redaction_required":true,"delete_after_processing_default":true,"future_approval_required":true}
]
```

## Budget class registry

```json voice-budget-class-registry
[
  {"budget_class":"VOICE_SHORT_NOTE","description":"Short single-speaker note suitable only for future approved low-cost transcription evaluation.","requires_budget_check":false,"requires_user_confirmation":false,"requires_privacy_review":false,"background_processing_authorized":false,"notes":"Still requires explicit future runtime approval; 70P authorizes no processing."},
  {"budget_class":"VOICE_LONG_NOTE","description":"Long audio note that may materially increase inference time and cost.","requires_budget_check":true,"requires_user_confirmation":true,"requires_privacy_review":true,"background_processing_authorized":false,"notes":"Long audio requires budget authority before processing."},
  {"budget_class":"VOICE_MULTI_SPEAKER","description":"Audio with diarization or multiple speakers, likely higher cost and higher misattribution risk.","requires_budget_check":true,"requires_user_confirmation":true,"requires_privacy_review":true,"background_processing_authorized":false,"notes":"Speaker labels are never identity proof."},
  {"budget_class":"VOICE_CAREGIVER_SENSITIVE","description":"Caregiver, family, health, medication-adjacent, or sensitive household voice content.","requires_budget_check":true,"requires_user_confirmation":true,"requires_privacy_review":true,"background_processing_authorized":false,"notes":"Requires caregiver/privacy review and session-only default handling."},
  {"budget_class":"VOICE_RESEARCH_LONG_FORM","description":"Research-only long-form ASR evaluation such as meeting-like audio.","requires_budget_check":true,"requires_user_confirmation":true,"requires_privacy_review":true,"background_processing_authorized":false,"notes":"No production provider selection or background loop is authorized."}
]
```

No background transcription loop and no always-on listening are authorized. Premium or expensive ASR requires explicit confirmation in any future runtime stage.

## Downstream routing rules

- Voice notes do not bypass 66P classification.
- Voice notes do not bypass 66P2 memory approval.
- Voice notes do not bypass 67P caregiver boundary.
- Voice notes do not bypass 68P relay no-send invariant.
- Voice notes do not bypass 69P routine no-medical, no-scheduler, no-execution invariant.
- Speaker labels must never be treated as identity proof.
- Transcription confidence must never be treated as action authority.
- Emergency-like content must block routine handling and must direct the user toward human caregiver or emergency-services guidance.
- Medication-adjacent content must require caregiver confirmation and must not authorize medical decisions.

## Future 71P prerequisites

71P Voice Intake for Caregiver Routines may open only after 70P closes. A future 71P story and technical spec must define consent, privacy, retention, deletion, transcript confidence, caregiver confirmation, budget checks, packet review, no-send invariants, no-medical decisions, no emergency triage, and no durable sensitive storage before any runtime work begins.

71P must remain bounded caregiver voice intake. It must not add TTS, cloned voice, continuous listening, speaker authentication, model downloads without approval, external sends, medication execution, emergency automation, or background monitoring.

## Non-claims

- Roboticxs does not identify a person by voice in 70P.
- Roboticxs does not authenticate a user by voice in 70P.
- Roboticxs does not clone voices.
- Roboticxs does not generate caregiver voices.
- Roboticxs does not continuously listen.
- Roboticxs does not store raw audio durably in 70P.
- Roboticxs does not store transcripts durably in 70P.
- Roboticxs does not execute actions from voice notes.
- Roboticxs does not treat transcripts as confirmed memory.
- Roboticxs does not treat speaker labels as identity proof.

## References

- Microsoft VibeVoice repository: https://github.com/microsoft/VibeVoice
- VIBEVOICE-ASR Technical Report: https://arxiv.org/abs/2601.18184
- VibeVoice Technical Report: https://arxiv.org/abs/2508.19205
- Microsoft VibeVoice-1.5B model card: https://huggingface.co/microsoft/VibeVoice-1.5B
- Local Roboticxs project brief: `docs/ROBOTICXS_PROJECT_BRIEF.md`
- Local memory boundary: `docs/reference/MEMORY_STACK_ARCHITECTURE_CRITERIO_STORE_v0_1.md`
- Local caregiver boundary: `docs/reference/CAREGIVER_MODE_BOUNDARY_SPEC_v0_1.md`
- Local caregiver relay boundary: `docs/reference/CAREGIVER_TELEGRAM_GROUP_RELAY_v0_1.md`
- Local guided routine boundary: `docs/reference/GUIDED_ROUTINE_PACKETS_v0_1.md`
