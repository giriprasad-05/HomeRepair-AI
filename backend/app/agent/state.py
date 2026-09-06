"""
AgentState definition for HomeRepair AI LangGraph agent.

All fields are typed. Optional fields may be None when not yet populated.
The state is passed through each node and returned with updates.
"""
from typing import Any, Dict, List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    # --- Input identifiers ---
    appliance_id: int
    issue_id: int

    # --- Loaded context (from DB) ---
    appliance_context: Optional[Dict[str, Any]]   # Appliance details
    issue_context: Optional[Dict[str, Any]]        # Issue + symptoms

    # --- History matching (deterministic — runs BEFORE any tool analysis) ---
    history_match: Optional[Dict[str, Any]]        # Result from HistoryMatchingService

    # --- Analysis mode (set by history match decision node) ---
    analysis_mode: str   # historical_match | fresh_investigation | reinvestigation_required | insufficient_data

    # --- Tool routing ---
    selected_tools: Optional[List[str]]            # Which diagnostic tools to run

    # --- Deterministic tool results ---
    history_analysis: Optional[Dict[str, Any]]     # appliance_history_tool result
    symptom_analysis: Optional[Dict[str, Any]]     # symptom_pattern_tool result
    warranty_analysis: Optional[Dict[str, Any]]    # warranty_tool result
    repair_analysis: Optional[Dict[str, Any]]      # repair_outcome_tool result
    manual_lookup: Optional[Dict[str, Any]]        # manual_lookup_tool result (conditional)

    # --- Long-term memory ---
    memories: Optional[List[Dict[str, Any]]]       # Relevant appliance memories

    # --- Agent reasoning (built from tool results — no LLM calculation) ---
    hypotheses: Optional[List[Dict[str, Any]]]     # Plausible causes with evidence
    evidence: Optional[Dict[str, Any]]             # Consolidated evidence summary
    uncertainty: Optional[str]                     # Uncertainty level or missing info

    # --- LLM output ---
    recommendation: Optional[str]                  # Parsed JSON recommendation

    # --- Observability (safe, high-level only — never chain-of-thought) ---
    activity_log: List[str]

    # --- Error tracking ---
    errors: List[str]

    # --- Final assembled response ---
    final_result: Optional[Dict[str, Any]]

    # --- Internal routing flags ---
    _has_error_codes: bool       # Whether symptoms contain error codes
    _evidence_sufficient: bool   # Whether enough evidence exists for LLM synthesis
    _should_store_memory: bool   # Whether meaningful memory was produced
    _skip_full_investigation: bool  # True when historical match is sufficient (no reinvestigation needed)
