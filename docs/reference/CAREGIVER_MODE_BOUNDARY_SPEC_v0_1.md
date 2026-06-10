# Caregiver Mode Boundary Spec v0.1

## Purpose

Stage 67P defines the Caregiver Mode boundary before any caregiver implementation.

Caregiver Mode should be guided routine support plus family visibility plus explicit boundaries. It must not become medical automation, surveillance, autonomous care decisions, medication administration authority, emergency response, or a substitute for family/professional supervision.

Allowed claim:

```text
Roboticxs can help prepare and guide caregiver-approved routines in future stages, with human confirmation and explicit boundaries.
```

Forbidden claim:

```text
Roboticxs safely manages medication or supervises a person with dementia.
```

## Research Summary

The research sources below support a conservative boundary:

- Dementia communication and daily routines require patience, person-specific adaptation, flexibility, and caregiver involvement.
- Home safety for dementia is a human-supervised environment concern, not a software-only guarantee.
- Medicines support requires defined human/clinical responsibility. Reminders and organization are different from dosage, substitution, administration, or clinical decisions.
- Assistive technology can support functioning, independence, participation, and safety, but it does not replace care or supervision.
- Caregiver support must account for caregiver burden, stress, and the family role.

```json caregiver-research-source-register
[
  {
    "source_id": "cdc_caregivers_family_friends",
    "category": "CAREGIVER_SUPPORT",
    "organization": "Centers for Disease Control and Prevention",
    "source_type": "official_public_health_resource",
    "title": "For Caregivers, Family and Friends",
    "url_or_reference": "https://www.cdc.gov/aging/caregiving/index.htm",
    "research_use": "Frames informal caregivers as central to long-term home care and notes caregiver health risks.",
    "boundary_implication": "Roboticxs may support caregiver summaries and routine visibility, but must not replace caregiver responsibility or increase hidden burden."
  },
  {
    "source_id": "alz_daily_care_plan",
    "category": "DEMENTIA_CAREGIVING",
    "organization": "Alzheimer's Association",
    "source_type": "caregiver_guidance",
    "title": "Daily Care Plan",
    "url_or_reference": "https://www.alz.org/help-support/caregiving/daily-care/daily-care-plan",
    "research_use": "Supports structured daily routines, flexibility, meaningful activities, and adaptation as abilities change.",
    "boundary_implication": "Roboticxs may later prepare caregiver-approved routine prompts, but only as guidance and not as supervision."
  },
  {
    "source_id": "alz_communication",
    "category": "DEMENTIA_CAREGIVING",
    "organization": "Alzheimer's Association",
    "source_type": "caregiver_guidance",
    "title": "Communication and Alzheimer's",
    "url_or_reference": "https://www.alz.org/help-support/caregiving/daily-care/communications",
    "research_use": "Supports patience, direct communication, listening, time to respond, and sensitivity to sensory issues such as hearing.",
    "boundary_implication": "Roboticxs caregiver copy must avoid coercive language and support gentle repetition and dignity."
  },
  {
    "source_id": "alz_home_safety",
    "category": "HOME_SAFETY",
    "organization": "Alzheimer's Association",
    "source_type": "caregiver_safety_guidance",
    "title": "Alzheimer's and Dementia Home Safety Tips",
    "url_or_reference": "https://www.alz.org/help-support/caregiving/safety/home-safety",
    "research_use": "Frames home safety as a caregiver safety domain with multiple environmental risks and caregiver planning needs.",
    "boundary_implication": "Roboticxs must not claim home safety monitoring, fall detection, or surveillance capability in 67P."
  },
  {
    "source_id": "nhs_medicines_tips_for_carers",
    "category": "MEDICINES_SUPPORT",
    "organization": "National Health Service",
    "source_type": "official_health_service_guidance",
    "title": "Medicines: tips for carers",
    "url_or_reference": "https://www.nhs.uk/social-care-and-support/practical-tips-if-you-care-for-someone/medicines-tips-for-carers/",
    "research_use": "Distinguishes medicines organization and reminders from pharmacist/doctor decisions; warns about double doses, consent, crushing tablets, and pharmacist advice.",
    "boundary_implication": "Medication-adjacent reminders require caregiver confirmation; dosage, schedule changes, substitution, consent override, and administration decisions are blocked."
  },
  {
    "source_id": "medlineplus_medicines",
    "category": "MEDICATION_SAFETY",
    "organization": "National Library of Medicine",
    "source_type": "official_health_information",
    "title": "Medicines",
    "url_or_reference": "https://medlineplus.gov/medicines.html",
    "research_use": "States medicines have risks, interactions, and should be taken correctly; medical information is not a substitute for professional care.",
    "boundary_implication": "Roboticxs must not provide medication advice, dosage decisions, diagnosis, or treatment guidance."
  },
  {
    "source_id": "medlineplus_storing_medicines",
    "category": "MEDICATION_SAFETY",
    "organization": "National Library of Medicine",
    "source_type": "official_health_information",
    "title": "Storing your medicines",
    "url_or_reference": "https://medlineplus.gov/ency/patientinstructions/000534.htm",
    "research_use": "Supports safe storage, original containers, pharmacist/provider questions, and disposal guidance.",
    "boundary_implication": "Pillbox or storage checklists must be caregiver-approved and cannot become medication administration authority."
  },
  {
    "source_id": "who_assistive_technology",
    "category": "ASSISTIVE_TECHNOLOGY",
    "organization": "World Health Organization",
    "source_type": "official_fact_sheet",
    "title": "Assistive technology",
    "url_or_reference": "https://www.who.int/news-room/fact-sheets/detail/assistive-technology",
    "research_use": "Defines assistive products as supporting functioning in cognition, communication, hearing, mobility, self-care, and vision.",
    "boundary_implication": "Roboticxs may be framed as assistive routine support, not as medical care, surveillance, emergency response, or professional caregiving."
  }
]
```

## Caregiver Boundary Policy

```json caregiver-boundary-policy
{
  "caregiver_runtime_authorized": false,
  "telegram_relay_authorized": false,
  "guided_routine_packets_authorized": false,
  "medication_decision_authorized": false,
  "medical_advice_authorized": false,
  "diagnosis_authorized": false,
  "emergency_triage_authorized": false,
  "continuous_monitoring_authorized": false,
  "external_action_authorized": false,
  "sensitive_durable_memory_authorized": false,
  "human_supervision_required_for_sensitive_routines": true,
  "caregiver_confirmation_required_for_medication_adjacent_steps": true
}
```

## Boundary Category Registry

```json caregiver-boundary-category-registry
[
  {
    "category_id": "ALLOW_PREPARATION_ONLY",
    "description": "May prepare drafts, checklists, or summaries for human review in a future approved stage.",
    "allowed_effect": "draft_or_prepare_only",
    "forbidden_effect": "runtime_execution_or_external_action",
    "future_stage_requirement": "approved_scoped_build_before_runtime"
  },
  {
    "category_id": "ALLOW_ROUTINE_GUIDANCE_LATER",
    "description": "May become guided routine support only after future stage approval and tests.",
    "allowed_effect": "future_step_by_step_guidance",
    "forbidden_effect": "67P_runtime_guidance",
    "future_stage_requirement": "69P_guided_routine_packets_approval"
  },
  {
    "category_id": "ASK_CAREGIVER_CONFIRMATION",
    "description": "Requires caregiver confirmation before a future routine step, status, storage, or relay action.",
    "allowed_effect": "confirmation_request_design",
    "forbidden_effect": "silent_sensitive_action",
    "future_stage_requirement": "confirmation_ui_and_audit_design"
  },
  {
    "category_id": "REQUIRE_HUMAN_SUPERVISION",
    "description": "Requires a human caregiver or professional to supervise sensitive routine context.",
    "allowed_effect": "supervision_requirement_label",
    "forbidden_effect": "robot_as_supervisor",
    "future_stage_requirement": "caregiver_role_and_consent_spec"
  },
  {
    "category_id": "ESCALATE_TO_CAREGIVER",
    "description": "May suggest asking a caregiver in future approved flows.",
    "allowed_effect": "draft_escalation_prompt",
    "forbidden_effect": "automatic_alert_or_external_message",
    "future_stage_requirement": "68P_telegram_relay_approval"
  },
  {
    "category_id": "BLOCK_MEDICAL_DECISION",
    "description": "Medical, medication, diagnosis, treatment, dosage, or emergency triage decisions are blocked.",
    "allowed_effect": "refusal_and_human_or_clinician_direction",
    "forbidden_effect": "medical_or_medication_decision",
    "future_stage_requirement": "not_reopenable_in_roboticxs_v0"
  },
  {
    "category_id": "BLOCK_SURVEILLANCE",
    "description": "Hidden monitoring, continuous surveillance, and unverified safety claims are blocked.",
    "allowed_effect": "refusal_and_boundary_explanation",
    "forbidden_effect": "monitoring_surveillance_or_fall_detection_claim",
    "future_stage_requirement": "explicit_privacy_safety_stage_if_ever_reopened"
  },
  {
    "category_id": "BLOCK_EXTERNAL_ACTION",
    "description": "External messages, alerts, contacts, dispatches, or writes without approval are blocked.",
    "allowed_effect": "draft_only_or_refusal",
    "forbidden_effect": "external_action_without_approval_packet",
    "future_stage_requirement": "approval_packet_and_connector_authority"
  },
  {
    "category_id": "DEFER_TO_FUTURE_STAGE",
    "description": "Capability is acknowledged but remains unavailable until its named future stage.",
    "allowed_effect": "future_prerequisite_definition",
    "forbidden_effect": "implementation_in_67P",
    "future_stage_requirement": "named_future_stage_story_spec_tests_validation"
  }
]
```

## Caregiver Capability Boundary Map

```json caregiver-capability-boundary-map
[
  {
    "capability_id": "caregiver_approved_checklist",
    "display_name": "Caregiver-approved checklist",
    "boundary_category": "ALLOW_PREPARATION_ONLY",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": false,
    "authorized_in_67P": false,
    "future_stage": "69P",
    "blocked_reason": "67P defines boundary only.",
    "memory_boundary": "CURRENT_ROBOTICXS_MEMORY_FLOW_OR_FUTURE_CRITERIO_STORE_AFTER_CONFIRMATION",
    "external_action_allowed": false
  },
  {
    "capability_id": "hearing_aid_routine_prompt",
    "display_name": "Hearing aid routine prompt",
    "boundary_category": "ALLOW_ROUTINE_GUIDANCE_LATER",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": false,
    "authorized_in_67P": false,
    "future_stage": "69P",
    "blocked_reason": "Routine guidance is future-only.",
    "memory_boundary": "CAREGIVER_CONTEXT_FUTURE_SESSION_ONLY_BEFORE_67P_CLOSEOUT",
    "external_action_allowed": false
  },
  {
    "capability_id": "hydration_or_meal_routine_prompt",
    "display_name": "Hydration or meal routine prompt",
    "boundary_category": "ALLOW_ROUTINE_GUIDANCE_LATER",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": false,
    "authorized_in_67P": false,
    "future_stage": "69P",
    "blocked_reason": "Routine guidance is future-only.",
    "memory_boundary": "CAREGIVER_CONTEXT_FUTURE_SESSION_ONLY_BEFORE_67P_CLOSEOUT",
    "external_action_allowed": false
  },
  {
    "capability_id": "appointment_preparation_note",
    "display_name": "Appointment preparation note",
    "boundary_category": "ALLOW_PREPARATION_ONLY",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": false,
    "authorized_in_67P": false,
    "future_stage": "69P",
    "blocked_reason": "Preparation notes are not runtime caregiver behavior in 67P.",
    "memory_boundary": "CURRENT_ROBOTICXS_MEMORY_FLOW_AFTER_APPROVAL_FOR_LOW_RISK_CONTEXT",
    "external_action_allowed": false
  },
  {
    "capability_id": "family_visible_routine_summary",
    "display_name": "Family-visible routine summary",
    "boundary_category": "DEFER_TO_FUTURE_STAGE",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "68P",
    "blocked_reason": "Family visibility requires relay consent and privacy boundary.",
    "memory_boundary": "FUTURE_CRITERIO_STORE_OR_SESSION_ONLY",
    "external_action_allowed": false
  },
  {
    "capability_id": "step_by_step_routine_guidance",
    "display_name": "Step-by-step routine guidance",
    "boundary_category": "ALLOW_ROUTINE_GUIDANCE_LATER",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "69P",
    "blocked_reason": "Guided Routine Packets are future-only.",
    "memory_boundary": "FUTURE_CRITERIO_STORE_OR_SESSION_ONLY",
    "external_action_allowed": false
  },
  {
    "capability_id": "caregiver_handoff_draft",
    "display_name": "Caregiver handoff draft",
    "boundary_category": "ALLOW_PREPARATION_ONLY",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "68P",
    "blocked_reason": "Handoff is draft-only until relay approval.",
    "memory_boundary": "SESSION_ONLY_OR_DO_NOT_STORE_FOR_SENSITIVE_CONTEXT",
    "external_action_allowed": false
  },
  {
    "capability_id": "medication_adjacent_routine",
    "display_name": "Medication-adjacent routine",
    "boundary_category": "ASK_CAREGIVER_CONFIRMATION",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "69P",
    "blocked_reason": "Medication-adjacent support cannot become medication administration.",
    "memory_boundary": "MEDICATION_ADJACENT_ROUTINE_SESSION_ONLY_OR_FUTURE_CONFIRMED",
    "external_action_allowed": false
  },
  {
    "capability_id": "pillbox_checklist_step",
    "display_name": "Pillbox checklist step",
    "boundary_category": "ASK_CAREGIVER_CONFIRMATION",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "69P",
    "blocked_reason": "Pillbox support requires human confirmation and cannot decide medicines.",
    "memory_boundary": "MEDICATION_ADJACENT_ROUTINE_SESSION_ONLY_OR_FUTURE_CONFIRMED",
    "external_action_allowed": false
  },
  {
    "capability_id": "routine_schedule_change",
    "display_name": "Change to routine schedule",
    "boundary_category": "ASK_CAREGIVER_CONFIRMATION",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "69P",
    "blocked_reason": "Routine changes require caregiver confirmation.",
    "memory_boundary": "FUTURE_CRITERIO_STORE_WITH_CONFIRMATION",
    "external_action_allowed": false
  },
  {
    "capability_id": "store_caregiver_sensitive_context",
    "display_name": "Store caregiver-sensitive context",
    "boundary_category": "ASK_CAREGIVER_CONFIRMATION",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "66P2_OR_FUTURE_MEMORY_STAGE",
    "blocked_reason": "67P does not authorize durable sensitive caregiver memory.",
    "memory_boundary": "SESSION_ONLY_OR_DO_NOT_STORE",
    "external_action_allowed": false
  },
  {
    "capability_id": "contact_family_member",
    "display_name": "Contact family member",
    "boundary_category": "BLOCK_EXTERNAL_ACTION",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "68P",
    "blocked_reason": "No automatic external messages or relay in 67P.",
    "memory_boundary": "CONSENT_AND_RELATIONSHIP_BOUNDARY_REQUIRED",
    "external_action_allowed": false
  },
  {
    "capability_id": "escalate_concern_to_caregiver",
    "display_name": "Escalate concern to caregiver",
    "boundary_category": "ESCALATE_TO_CAREGIVER",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "68P",
    "blocked_reason": "67P may define escalation prompts only; no relay runtime.",
    "memory_boundary": "SESSION_ONLY_OR_DO_NOT_STORE_FOR_SENSITIVE_CONTEXT",
    "external_action_allowed": false
  },
  {
    "capability_id": "mark_routine_completed",
    "display_name": "Mark routine completed",
    "boundary_category": "ASK_CAREGIVER_CONFIRMATION",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "69P",
    "blocked_reason": "Completion state cannot become medical or supervision truth.",
    "memory_boundary": "ROUTINE_COMPLETION_STATE_FUTURE_ONLY",
    "external_action_allowed": false
  },
  {
    "capability_id": "medication_dosage_decision",
    "display_name": "Medication dosage decision",
    "boundary_category": "BLOCK_MEDICAL_DECISION",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "not_reopenable_in_roboticxs_v0",
    "blocked_reason": "Roboticxs must not decide medication dosage.",
    "memory_boundary": "DO_NOT_STORE_AS_ACTIONABLE_DECISION",
    "external_action_allowed": false
  },
  {
    "capability_id": "medication_substitution",
    "display_name": "Medication substitution",
    "boundary_category": "BLOCK_MEDICAL_DECISION",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "not_reopenable_in_roboticxs_v0",
    "blocked_reason": "Roboticxs must not substitute medicines.",
    "memory_boundary": "DO_NOT_STORE_AS_ACTIONABLE_DECISION",
    "external_action_allowed": false
  },
  {
    "capability_id": "medical_advice",
    "display_name": "Medical advice",
    "boundary_category": "BLOCK_MEDICAL_DECISION",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "not_reopenable_in_roboticxs_v0",
    "blocked_reason": "Roboticxs does not provide medical advice.",
    "memory_boundary": "DO_NOT_STORE_AS_ACTIONABLE_DECISION",
    "external_action_allowed": false
  },
  {
    "capability_id": "diagnosis",
    "display_name": "Diagnosis",
    "boundary_category": "BLOCK_MEDICAL_DECISION",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "not_reopenable_in_roboticxs_v0",
    "blocked_reason": "Roboticxs does not diagnose symptoms.",
    "memory_boundary": "DO_NOT_STORE_AS_ACTIONABLE_DECISION",
    "external_action_allowed": false
  },
  {
    "capability_id": "emergency_triage",
    "display_name": "Emergency triage",
    "boundary_category": "BLOCK_MEDICAL_DECISION",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "not_reopenable_in_roboticxs_v0",
    "blocked_reason": "Roboticxs does not provide emergency response or triage.",
    "memory_boundary": "DO_NOT_STORE_AS_ACTIONABLE_DECISION",
    "external_action_allowed": false
  },
  {
    "capability_id": "fall_detection_claim",
    "display_name": "Fall detection claim",
    "boundary_category": "BLOCK_SURVEILLANCE",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "explicit_privacy_safety_stage_if_ever_reopened",
    "blocked_reason": "No sensors, monitoring, or fall detection are authorized.",
    "memory_boundary": "DO_NOT_STORE_AS_DETECTED_EVENT",
    "external_action_allowed": false
  },
  {
    "capability_id": "ingestion_verification_as_clinical_truth",
    "display_name": "Medication ingestion verification as clinical truth",
    "boundary_category": "BLOCK_MEDICAL_DECISION",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "not_reopenable_in_roboticxs_v0",
    "blocked_reason": "Roboticxs cannot verify ingestion as medical truth.",
    "memory_boundary": "DO_NOT_STORE_AS_CLINICAL_FACT",
    "external_action_allowed": false
  },
  {
    "capability_id": "hidden_monitoring",
    "display_name": "Hidden monitoring",
    "boundary_category": "BLOCK_SURVEILLANCE",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "explicit_privacy_safety_stage_if_ever_reopened",
    "blocked_reason": "Hidden monitoring violates consent and dignity boundaries.",
    "memory_boundary": "DO_NOT_STORE_SURVEILLANCE_DATA",
    "external_action_allowed": false
  },
  {
    "capability_id": "continuous_surveillance",
    "display_name": "Continuous surveillance",
    "boundary_category": "BLOCK_SURVEILLANCE",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "explicit_privacy_safety_stage_if_ever_reopened",
    "blocked_reason": "Continuous surveillance is outside Roboticxs v0.",
    "memory_boundary": "DO_NOT_STORE_SURVEILLANCE_DATA",
    "external_action_allowed": false
  },
  {
    "capability_id": "automatic_family_alert_without_approval",
    "display_name": "Automatic family alert without approval",
    "boundary_category": "BLOCK_EXTERNAL_ACTION",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "68P",
    "blocked_reason": "Automatic alerts require future relay and approval-packet authority.",
    "memory_boundary": "CONSENT_AND_APPROVAL_REQUIRED",
    "external_action_allowed": false
  },
  {
    "capability_id": "external_action_without_approval_packet",
    "display_name": "External action without approval packet",
    "boundary_category": "BLOCK_EXTERNAL_ACTION",
    "requires_caregiver_confirmation": true,
    "requires_human_supervision": true,
    "authorized_in_67P": false,
    "future_stage": "not_reopenable_without_approval_packet_authority",
    "blocked_reason": "External action without approval packet is blocked.",
    "memory_boundary": "DO_NOT_STORE_AS_AUTHORIZED_ACTION",
    "external_action_allowed": false
  }
]
```

## Caregiver Memory Boundary Map

67P uses 66P2 as the governing memory architecture. It maps future caregiver memory classes without authorizing storage or runtime use.

```json caregiver-memory-boundary-map
[
  {
    "memory_class": "MEDICATION_ADJACENT_ROUTINE",
    "storage_lane": "SESSION_ONLY_OR_DO_NOT_STORE",
    "confirmation_required": true,
    "sensitive": true,
    "durable_storage_authorized_in_67P": false,
    "allowed_use_in_67P": false,
    "future_stage_requirement": "69P_and_future_memory_authority_confirmation",
    "deletion_export_requirement": "future_delete_export_revoke_required"
  },
  {
    "memory_class": "HEARING_AID_ROUTINE",
    "storage_lane": "SESSION_ONLY_OR_DO_NOT_STORE",
    "confirmation_required": true,
    "sensitive": false,
    "durable_storage_authorized_in_67P": false,
    "allowed_use_in_67P": false,
    "future_stage_requirement": "69P_guided_routine_boundary",
    "deletion_export_requirement": "future_delete_export_revoke_required"
  },
  {
    "memory_class": "FAMILY_SUPERVISION_NOTE",
    "storage_lane": "SESSION_ONLY_OR_DO_NOT_STORE",
    "confirmation_required": true,
    "sensitive": true,
    "durable_storage_authorized_in_67P": false,
    "allowed_use_in_67P": false,
    "future_stage_requirement": "68P_relay_privacy_and_67P_boundary",
    "deletion_export_requirement": "future_delete_export_revoke_required"
  },
  {
    "memory_class": "ROUTINE_COMPLETION_STATE",
    "storage_lane": "SESSION_ONLY_OR_DO_NOT_STORE",
    "confirmation_required": true,
    "sensitive": true,
    "durable_storage_authorized_in_67P": false,
    "allowed_use_in_67P": false,
    "future_stage_requirement": "69P_completion_state_semantics",
    "deletion_export_requirement": "future_delete_export_revoke_required"
  },
  {
    "memory_class": "SENSITIVE_HEALTH_CONTEXT",
    "storage_lane": "SESSION_ONLY_OR_DO_NOT_STORE",
    "confirmation_required": true,
    "sensitive": true,
    "durable_storage_authorized_in_67P": false,
    "allowed_use_in_67P": false,
    "future_stage_requirement": "future_sensitive_memory_authority_stage",
    "deletion_export_requirement": "block_or_explicit_future_delete_export_revoke_required"
  },
  {
    "memory_class": "ESCALATION_PREFERENCE",
    "storage_lane": "SESSION_ONLY_OR_DO_NOT_STORE",
    "confirmation_required": true,
    "sensitive": true,
    "durable_storage_authorized_in_67P": false,
    "allowed_use_in_67P": false,
    "future_stage_requirement": "68P_relay_approval_and_contact_consent",
    "deletion_export_requirement": "future_delete_export_revoke_required"
  },
  {
    "memory_class": "NEVER_STORE_CAREGIVER_DATA",
    "storage_lane": "SESSION_ONLY_OR_DO_NOT_STORE",
    "confirmation_required": false,
    "sensitive": true,
    "durable_storage_authorized_in_67P": false,
    "allowed_use_in_67P": false,
    "future_stage_requirement": "not_reopenable_for_durable_storage",
    "deletion_export_requirement": "discard_and_do_not_use_for_decisions"
  }
]
```

## Future Stage Gates

```json future-stage-gates
[
  {
    "stage_id": "68P_CAREGIVER_TELEGRAM_GROUP_RELAY",
    "stage_name": "Caregiver Telegram Group Relay v0",
    "prerequisites_from_67P": ["consent_boundary", "privacy_boundary", "no_automatic_alerts", "approval_packet_required", "sensitive_memory_not_silent"],
    "authorized_by_67P": false,
    "required_future_approval": ["story_approval", "technical_spec_approval", "relay_privacy_tests", "external_action_authority_review"],
    "forbidden_until_stage_approval": ["telegram_group_relay_runtime", "automatic_family_alerts", "private_sensitive_data_sharing", "external_messages"]
  },
  {
    "stage_id": "69P_GUIDED_ROUTINE_PACKETS",
    "stage_name": "Guided Routine Packets v0",
    "prerequisites_from_67P": ["routine_guidance_boundary", "caregiver_confirmation_model", "human_supervision_rule", "non_medical_copy"],
    "authorized_by_67P": false,
    "required_future_approval": ["story_approval", "technical_spec_approval", "routine_packet_tests", "medication_adjacent_refusal_tests"],
    "forbidden_until_stage_approval": ["guided_routine_runtime", "pillbox_workflow", "routine_completion_state_runtime", "medical_or_medication_decisions"]
  },
  {
    "stage_id": "71P_VOICE_INTAKE_FOR_CAREGIVER_ROUTINES",
    "stage_name": "Voice Intake for Caregiver Routines",
    "prerequisites_from_67P": ["voice_privacy_boundary", "caregiver_consent", "sensitive_context_handling", "no_medical_claims"],
    "authorized_by_67P": false,
    "required_future_approval": ["story_approval", "technical_spec_approval", "voice_privacy_tests", "sensitive_memory_tests"],
    "forbidden_until_stage_approval": ["voice_intake_runtime", "voice_storage", "clinical_transcription_claims", "caregiver_sensitive_memory_auto_save"]
  }
]
```

## Telegram Relay Boundary

Future Telegram caregiver relay may eventually support:

- Robbie of family member to Robbie of caregiver;
- family group summary;
- needs-attention prompt;
- caregiver confirmation request;
- routine status note.

67P does not implement relay. Future relay must not support automatic emergency claims, automatic medication confirmation, automatic external alerts, private sensitive data sharing without consent, or invisible monitoring.

## Guided Routine Packet Boundary

Future Guided Routine Packets may eventually support caregiver-approved checklists and step-by-step routine guidance. They must remain non-clinical and require human confirmation for medication-adjacent or sensitive routine steps.

67P does not implement Guided Routine Packets.

## Non-Claims

```text
Roboticxs does not provide medical advice.
Roboticxs does not decide medication dosage or schedule.
Roboticxs does not verify medication ingestion as clinical fact.
Roboticxs does not replace family supervision or professional caregiving.
Roboticxs does not provide emergency response or triage.
Roboticxs does not continuously monitor the person.
Roboticxs does not contact family members automatically.
Roboticxs does not store sensitive caregiver context durably in 67P.
```

## Non-Authorization

67P does not authorize caregiver runtime behavior, Telegram group relay, Guided Routine Packets, medication reminders, pillbox execution, voice, sensors, continuous monitoring, emergency dispatch, external messaging, caregiver memory storage, connector retrieval, browser/email/WhatsApp, CRM, lead-gen, pipeline, handoff, or external writes.

## Closeout State

After 67P closeout, Caregiver Mode remains non-runtime but clearly bounded. Stage 68P may become next eligible for story drafting only.
