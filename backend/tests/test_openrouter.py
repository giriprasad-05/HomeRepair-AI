import os
import pytest
from unittest.mock import patch, MagicMock

from app.agent.llm import get_llm
from app.agent.nodes import llm_synthesis_node
from app.agent.state import AgentState


def test_openrouter_config_loaded_from_env():
    # Verify get_llm reads directly from os.getenv
    with patch.dict(os.environ, {
        "OPENROUTER_API_KEY": "test-key-abc",
        "OPENROUTER_MODEL": "test-model-xyz",
        "OPENROUTER_BASE_URL": "https://test.openrouter.ai/api/v1",
    }):
        llm = get_llm()
        assert llm.model_name == "test-model-xyz"
        assert llm.openai_api_key.get_secret_value() == "test-key-abc"
        assert "test.openrouter.ai" in str(llm.openai_api_base)


def test_openrouter_missing_api_key_raises_error():
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "", "OPENROUTER_MODEL": "some-model"}):
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY environment variable is not set"):
            get_llm()


def test_openrouter_missing_model_raises_error():
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "some-key", "OPENROUTER_MODEL": ""}):
        with pytest.raises(ValueError, match="OPENROUTER_MODEL environment variable is not set"):
            get_llm()


def test_no_hardcoded_keys_or_models_in_llm_source():
    llm_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "agent", "llm.py")
    with open(llm_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Ensure no sk-or or raw model strings are hardcoded in llm.py
    assert "sk-or-v1-" not in content
    assert "nvidia/" not in content
    assert "anthropic/" not in content
    assert "openai/" not in content


def test_llm_synthesis_api_failure_handling(test_db):
    state: AgentState = {
        "issue_id": 1,
        "appliance_id": 1,
        "issue_context": {"title": "Noise", "symptoms": []},
        "appliance_context": {"brand": "LG"},
        "hypotheses": [],
        "evidence": {},
        "errors": [],
        "activity_log": [],
    }

    with patch("app.agent.nodes.get_llm", side_effect=Exception("OpenRouter 503 Service Unavailable")):
        res = llm_synthesis_node(state, test_db)
        assert res["recommendation"] is not None
        assert "error" in res["recommendation"]
        assert any("503" in e for e in res["errors"])
        # Should not crash the agent


def test_llm_synthesis_malformed_json_handling(test_db):
    state: AgentState = {
        "issue_id": 1,
        "appliance_id": 1,
        "issue_context": {"title": "Noise", "symptoms": []},
        "appliance_context": {"brand": "LG"},
        "hypotheses": [],
        "evidence": {},
        "errors": [],
        "activity_log": [],
    }

    with patch("app.agent.nodes.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        # Non-JSON content returned by LLM
        mock_llm.invoke.return_value.content = "Here is what you should do: check the drum and call support."
        mock_get_llm.return_value = mock_llm

        res = llm_synthesis_node(state, test_db)
        assert res["recommendation"] is not None
        assert "error" in res["recommendation"]
        assert any("Failed to parse LLM JSON" in e for e in res["errors"])
