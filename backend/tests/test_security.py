import os
import re
import pytest


def test_env_in_root_and_frontend_gitignore():
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    root_gitignore = os.path.join(root_dir, ".gitignore")
    frontend_gitignore = os.path.join(root_dir, "frontend", ".gitignore")

    assert os.path.exists(root_gitignore), "Root .gitignore must exist"
    with open(root_gitignore, "r", encoding="utf-8") as f:
        root_content = f.read().splitlines()
    assert ".env" in root_content, ".env must be ignored in root .gitignore"

    assert os.path.exists(frontend_gitignore), "Frontend .gitignore must exist"
    with open(frontend_gitignore, "r", encoding="utf-8") as f:
        frontend_content = f.read().splitlines()
    assert ".env" in frontend_content, ".env must be ignored in frontend .gitignore"


def test_frontend_has_no_openrouter_api_key():
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    frontend_dir = os.path.join(root_dir, "frontend", "src")

    for root, _, files in os.walk(frontend_dir):
        for file in files:
            if file.endswith((".js", ".jsx", ".ts", ".tsx", ".html", ".css")):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                assert "OPENROUTER_API_KEY" not in content, f"Frontend file {file} must not reference OPENROUTER_API_KEY"
                assert "sk-or-v1-" not in content, f"Frontend file {file} must not contain API key secrets"


def test_no_secrets_in_tracked_git_files():
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    backend_src = os.path.join(root_dir, "backend", "app")

    secret_pattern = re.compile(r"sk-or-v1-[a-f0-9]{32,}", re.IGNORECASE)

    for root, _, files in os.walk(backend_src):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                match = secret_pattern.search(content)
                assert match is None, f"Found hardcoded API key secret in {file_path}"


def test_env_example_has_no_real_secret():
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    backend_env_example = os.path.join(root_dir, "backend", ".env.example")

    with open(backend_env_example, "r", encoding="utf-8") as f:
        content = f.read()

    assert "sk-or-v1-" not in content, "backend/.env.example must not contain real API keys"
    assert "OPENROUTER_API_KEY=your_openrouter_api_key_here" in content


def test_activity_log_does_not_leak_secrets(test_db):
    from app.agent.nodes import (
        validate_issue_node,
        load_appliance_context_node,
        evaluate_evidence_node,
        finalize_result_node,
    )

    state = {
        "issue_id": 1,
        "appliance_id": 1,
        "activity_log": [],
        "errors": [],
    }

    # Verify log messages never include API keys or raw tokens
    for node_fn in [validate_issue_node]:
        res = node_fn(state, test_db)
        for log_entry in res.get("activity_log", []):
            assert "sk-or-" not in log_entry
            assert "Bearer" not in log_entry
            assert "password" not in log_entry.lower()
