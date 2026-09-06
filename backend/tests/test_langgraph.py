import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from app.models.enums import ApplianceCategory, IssueSeverity, IssueStatus
from app.models.appliance import Appliance
from app.models.issue import IssueReport
from app.models.symptom import Symptom
from app.agent.graph import compile_agent, run_agent
from app.agent.nodes import (
    validate_issue_node,
    load_appliance_context_node,
    evaluate_evidence_node,
    finalize_result_node,
)


def test_validate_issue_node_missing_issue(test_db):
    state = {"issue_id": 9999}
    result = validate_issue_node(state, test_db)
    assert "errors" in result
    assert len(result["errors"]) > 0
    assert "final_result" in result


def test_langgraph_insufficient_evidence_routing(test_db):
    # Appliance with issue but ZERO symptoms
    app = Appliance(name="AC", brand="Daikin", category=ApplianceCategory.AIR_CONDITIONER)
    test_db.add(app)
    test_db.commit()

    iss = IssueReport(appliance_id=app.id, title="Vague noise", description="None", severity=IssueSeverity.LOW)
    test_db.add(iss)
    test_db.commit()

    # When run through agent, insufficient evidence should route safely
    # and return status "insufficient_data" without failing or calling LLM
    result = run_agent(iss.id, test_db)
    assert result["analysis_status"] == "insufficient_data"
    assert "uncertainty" in result
    assert "symptoms have been recorded" in result["uncertainty"].lower() or "insufficient" in result["summary"].lower()


def test_langgraph_error_code_conditional_routing(test_db):
    app = Appliance(name="Washer", brand="LG", category=ApplianceCategory.WASHING_MACHINE)
    test_db.add(app)
    test_db.commit()

    iss = IssueReport(appliance_id=app.id, title="Spin problem", severity=IssueSeverity.HIGH)
    test_db.add(iss)
    test_db.flush()

    s = Symptom(issue_id=iss.id, name="Error Code", value="UE")
    test_db.add(s)
    test_db.commit()
    test_db.refresh(iss)

    # Mock get_llm to avoid external API calls during graph structure test
    with patch("app.agent.nodes.get_llm") as mock_get_llm:
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value.content = '{"summary": "Unbalanced load detected.", "likely_causes": [{"cause": "Unbalanced drum", "reason": "Code UE", "confidence": "high"}], "evidence": [{"observation": "Error code UE", "supports": "Unbalanced drum"}], "recommended_next_step": "Redistribute load", "service_recommendation": "N/A", "warranty_recommendation": "N/A"}'
        mock_get_llm.return_value = mock_llm_instance

        result = run_agent(iss.id, test_db)
        assert result["analysis_status"] == "completed"
        # Verify manual lookup was logged in activity_log
        assert any("manual error code lookup" in log.lower() for log in result["activity_log"])


def test_langgraph_resilience_to_tool_failure(test_db):
    app = Appliance(name="Washer", brand="LG", category=ApplianceCategory.WASHING_MACHINE)
    test_db.add(app)
    test_db.commit()

    iss = IssueReport(appliance_id=app.id, title="Spin problem", severity=IssueSeverity.HIGH)
    test_db.add(iss)
    test_db.flush()
    s = Symptom(issue_id=iss.id, name="Vibration", value="High")
    test_db.add(s)
    test_db.commit()
    test_db.refresh(iss)

    # Simulate tool error in get_appliance_history
    with patch("app.agent.nodes.get_appliance_history", side_effect=RuntimeError("Tool database failure")):
        with patch("app.agent.nodes.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value.content = '{"summary": "Vibration check.", "likely_causes": [], "evidence": [], "recommended_next_step": "Check level", "service_recommendation": "N/A", "warranty_recommendation": "N/A"}'
            mock_get_llm.return_value = mock_llm

            # Graph must complete gracefully without unhandled exception
            result = run_agent(iss.id, test_db)
            assert result is not None
            assert any("Tool database failure" in e for e in result["errors"])
