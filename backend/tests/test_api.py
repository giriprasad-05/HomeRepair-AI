import pytest
from datetime import date
from unittest.mock import patch, MagicMock


def test_api_appliances_crud(client):
    # 1. Create Appliance
    payload = {
        "name": "Kitchen Fridge",
        "brand": "Samsung",
        "model_number": "RF28R7351SR",
        "category": "refrigerator",
        "location": "Kitchen",
        "notes": "Main family fridge",
    }
    resp = client.post("/api/appliances", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] is not None
    assert data["brand"] == "Samsung"
    appliance_id = data["id"]

    # 2. Get list of active appliances
    resp = client.get("/api/appliances")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 3. Get single appliance
    resp = client.get(f"/api/appliances/{appliance_id}")
    assert resp.status_code == 200
    assert resp.json()["model_number"] == "RF28R7351SR"

    # 4. Update appliance
    resp = client.put(f"/api/appliances/{appliance_id}", json={"location": "Garage"})
    assert resp.status_code == 200
    assert resp.json()["location"] == "Garage"

    # 5. Soft delete appliance
    resp = client.delete(f"/api/appliances/{appliance_id}")
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    # Verify excluded from active list
    resp = client.get("/api/appliances")
    assert not any(a["id"] == appliance_id for a in resp.json())


def test_api_issues_symptoms_repairs(client):
    # Create Appliance
    app_resp = client.post("/api/appliances", json={
        "name": "Washer",
        "brand": "LG",
        "category": "washing_machine",
    })
    app_id = app_resp.json()["id"]

    # Create Issue
    issue_resp = client.post(f"/api/appliances/{app_id}/issues", json={
        "title": "Spin Vibration",
        "description": "Drum shaking",
        "severity": "high",
    })
    assert issue_resp.status_code == 201
    issue_id = issue_resp.json()["id"]

    # List Issues for Appliance
    list_resp = client.get(f"/api/appliances/{app_id}/issues")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # Add Symptom to Issue
    sym_resp = client.post(f"/api/issues/{issue_id}/symptoms", json={
        "name": "Error Code",
        "value": "UE",
    })
    assert sym_resp.status_code == 201
    assert sym_resp.json()["value"] == "UE"

    # Get Issue Symptoms
    sym_list = client.get(f"/api/issues/{issue_id}/symptoms")
    assert sym_list.status_code == 200
    assert len(sym_list.json()) == 1

    # Add Repair to Appliance
    rep_resp = client.post(f"/api/appliances/{app_id}/repairs", json={
        "repair_type": "Clean Pump",
        "service_cost": 75.0,
        "outcome": "Successful",
    })
    assert rep_resp.status_code == 201
    assert rep_resp.json()["service_cost"] == 75.0

    # Get Appliance Repairs
    rep_list = client.get(f"/api/appliances/{app_id}/repairs")
    assert rep_list.status_code == 200
    assert len(rep_list.json()) == 1


def test_api_agent_investigate_endpoint(client):
    # Setup appliance and issue
    app_resp = client.post("/api/appliances", json={
        "name": "Washer",
        "brand": "LG",
        "category": "washing_machine",
    })
    app_id = app_resp.json()["id"]

    issue_resp = client.post(f"/api/appliances/{app_id}/issues", json={
        "title": "Washer making a loud spin noise",
        "severity": "medium",
    })
    issue_id = issue_resp.json()["id"]

    client.post(f"/api/issues/{issue_id}/symptoms", json={
        "name": "Noise",
        "value": "Rattling",
    })

    # Mock get_llm
    with patch("app.agent.nodes.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = '{"summary": "Rattling noise in washer.", "likely_causes": [{"cause": "Loose belt", "reason": "Rattling detected", "confidence": "high"}], "evidence": [{"observation": "Rattling", "supports": "Loose belt"}], "recommended_next_step": "Tighten belt", "service_recommendation": "Check drive belt", "warranty_recommendation": "N/A"}'
        mock_get_llm.return_value = mock_llm

        resp = client.post(f"/api/agent/investigate/{issue_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["issue_id"] == str(issue_id)
        assert data["analysis_status"] == "completed"
        assert len(data["likely_causes"]) >= 1
        assert len(data["activity_log"]) >= 1
        assert data["recommended_next_step"] == "Tighten belt"


def test_api_agent_investigate_nonexistent_issue(client):
    resp = client.post("/api/agent/investigate/99999")
    assert resp.status_code == 404
