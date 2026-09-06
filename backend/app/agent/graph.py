"""
LangGraph StateGraph for HomeRepair AI diagnostic agent.

Workflow:
  START
  → validate_issue          (hard stop on missing issue/appliance)
  → load_appliance_context
  → retrieve_memories
  → check_history_match     ← NEW: deterministic similarity check
  → decide_investigation_mode ← NEW: HISTORICAL_MATCH / FRESH / REINVESTIGATION / INSUFFICIENT
      ↓ HISTORICAL_MATCH → historical_match_finalize → END
      ↓ INSUFFICIENT_DATA → insufficient_data_finalize → END
      ↓ FRESH / REINVESTIGATION → continue
  → analyze_history
  → analyze_symptoms
  → analyze_warranty
  → analyze_repairs
  → [conditional] manual_lookup  (only when error codes detected in symptoms)
  → generate_hypotheses
  → evaluate_evidence
  → [conditional] llm_synthesis  (only when evidence is sufficient)
  → store_memory
  → finalize_result
  → END
"""
from functools import partial
from typing import Callable, Dict, Literal

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from app.agent.state import AgentState
from app.agent.nodes import (
    validate_issue_node,
    load_appliance_context_node,
    retrieve_memories_node,
    check_history_match_node,
    decide_investigation_mode_node,
    select_diagnostic_tools_node,
    analyze_history_node,
    analyze_symptoms_node,
    analyze_warranty_node,
    analyze_repairs_node,
    manual_lookup_node,
    generate_hypotheses_node,
    evaluate_evidence_node,
    llm_synthesis_node,
    historical_match_finalize_node,
    insufficient_data_finalize_node,
    store_memory_node,
    finalize_result_node,
)


# ---------------------------------------------------------------------------
# Conditional edge functions
# ---------------------------------------------------------------------------

def _route_after_validate(state: AgentState) -> Literal["load_appliance_context", "finalize_result"]:
    """If validation produced a final_result (error), jump straight to END."""
    if state.get("final_result"):
        return "finalize_result"
    return "load_appliance_context"


def _route_after_decide_mode(
    state: AgentState,
) -> Literal[
    "historical_match_finalize",
    "insufficient_data_finalize",
    "select_diagnostic_tools",
]:
    """
    Route based on the analysis_mode decided by decide_investigation_mode_node:
    - HISTORICAL_MATCH   → skip tools, finalize from history
    - INSUFFICIENT_DATA  → skip tools, ask targeted questions
    - FRESH / REINVESTIGATION → run select_diagnostic_tools
    """
    mode = state.get("analysis_mode", "fresh_investigation")
    if mode == "historical_match":
        return "historical_match_finalize"
    if mode == "insufficient_data":
        return "insufficient_data_finalize"
    return "select_diagnostic_tools"


def _route_after_repairs(state: AgentState) -> Literal["manual_lookup", "generate_hypotheses"]:
    """Only run manual lookup if the issue symptoms contain error codes."""
    if state.get("_has_error_codes"):
        return "manual_lookup"
    return "generate_hypotheses"


def _route_after_evidence(state: AgentState) -> Literal["llm_synthesis", "store_memory"]:
    """Only call LLM when there is enough evidence."""
    if state.get("_evidence_sufficient"):
        return "llm_synthesis"
    return "store_memory"


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------

def _bind_db(node_fn: Callable, db: Session) -> Callable:
    """Bind a database session to a node function."""
    return partial(node_fn, db=db)


def compile_agent(db: Session) -> StateGraph:
    """
    Build and compile the LangGraph StateGraph with db session bound to each node.
    Returns the compiled graph object ready for invocation.
    """
    builder = StateGraph(AgentState)

    # Register nodes (each receives state + db via partial)
    builder.add_node("validate_issue", _bind_db(validate_issue_node, db))
    builder.add_node("load_appliance_context", _bind_db(load_appliance_context_node, db))
    builder.add_node("retrieve_memories", _bind_db(retrieve_memories_node, db))
    builder.add_node("check_history_match", _bind_db(check_history_match_node, db))
    builder.add_node("decide_investigation_mode", _bind_db(decide_investigation_mode_node, db))
    builder.add_node("select_diagnostic_tools", _bind_db(select_diagnostic_tools_node, db))
    builder.add_node("historical_match_finalize", _bind_db(historical_match_finalize_node, db))
    builder.add_node("insufficient_data_finalize", _bind_db(insufficient_data_finalize_node, db))
    builder.add_node("analyze_history", _bind_db(analyze_history_node, db))
    builder.add_node("analyze_symptoms", _bind_db(analyze_symptoms_node, db))
    builder.add_node("analyze_warranty", _bind_db(analyze_warranty_node, db))
    builder.add_node("analyze_repairs", _bind_db(analyze_repairs_node, db))
    builder.add_node("manual_lookup", _bind_db(manual_lookup_node, db))
    builder.add_node("generate_hypotheses", _bind_db(generate_hypotheses_node, db))
    builder.add_node("evaluate_evidence", _bind_db(evaluate_evidence_node, db))
    builder.add_node("llm_synthesis", _bind_db(llm_synthesis_node, db))
    builder.add_node("store_memory", _bind_db(store_memory_node, db))
    builder.add_node("finalize_result", _bind_db(finalize_result_node, db))

    # Entry point
    builder.set_entry_point("validate_issue")

    # validate_issue → conditional (error abort or continue)
    builder.add_conditional_edges(
        "validate_issue",
        _route_after_validate,
        {
            "load_appliance_context": "load_appliance_context",
            "finalize_result": "finalize_result",
        },
    )

    # Linear: load context → retrieve memories → check match → decide mode
    builder.add_edge("load_appliance_context", "retrieve_memories")
    builder.add_edge("retrieve_memories", "check_history_match")
    builder.add_edge("check_history_match", "decide_investigation_mode")

    # decide_mode → conditional (historical / insufficient / continue)
    builder.add_conditional_edges(
        "decide_investigation_mode",
        _route_after_decide_mode,
        {
            "historical_match_finalize": "historical_match_finalize",
            "insufficient_data_finalize": "insufficient_data_finalize",
            "select_diagnostic_tools": "select_diagnostic_tools",
        },
    )

    # Short-circuit paths → END
    builder.add_edge("historical_match_finalize", END)
    builder.add_edge("insufficient_data_finalize", END)

    # Full tool analysis path
    builder.add_edge("select_diagnostic_tools", "analyze_history")
    builder.add_edge("analyze_history", "analyze_symptoms")
    builder.add_edge("analyze_symptoms", "analyze_warranty")
    builder.add_edge("analyze_warranty", "analyze_repairs")

    # Conditional: manual lookup only when error codes detected
    builder.add_conditional_edges(
        "analyze_repairs",
        _route_after_repairs,
        {
            "manual_lookup": "manual_lookup",
            "generate_hypotheses": "generate_hypotheses",
        },
    )

    builder.add_edge("manual_lookup", "generate_hypotheses")
    builder.add_edge("generate_hypotheses", "evaluate_evidence")

    # Conditional: LLM only when evidence is sufficient
    builder.add_conditional_edges(
        "evaluate_evidence",
        _route_after_evidence,
        {
            "llm_synthesis": "llm_synthesis",
            "store_memory": "store_memory",
        },
    )

    builder.add_edge("llm_synthesis", "store_memory")
    builder.add_edge("store_memory", "finalize_result")
    builder.add_edge("finalize_result", END)

    return builder.compile()


def run_agent(issue_id: int, db: Session) -> Dict:
    """
    Entry point: compile the agent graph for this db session and invoke it.
    Returns the final_result dict from the agent state.
    """
    graph = compile_agent(db)

    initial_state: AgentState = {
        "issue_id": issue_id,
        "appliance_id": 0,
        "activity_log": [],
        "errors": [],
        "_has_error_codes": False,
        "_evidence_sufficient": False,
        "_should_store_memory": False,
        "_skip_full_investigation": False,
        "analysis_mode": "fresh_investigation",
    }

    final_state = graph.invoke(initial_state)
    return final_state.get("final_result") or {}
