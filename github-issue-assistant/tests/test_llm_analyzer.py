import os
import json
import pytest
from types import SimpleNamespace

from app.llm_analyzer import LLMAnalyzer
from app.models import IssueType

@pytest.mark.asyncio
async def test_llm_analyzer_openai_mock(monkeypatch):
    # Set required env for OpenAI path
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

    # Prepare mock response content
    expected = {
        "summary": "User cannot log in due to 500 error",
        "type": "bug",
        "priority_score": "5 - critical authentication failure",
        "suggested_labels": ["bug", "authentication"],
        "potential_impact": "Users are locked out of the app"
    }

    class MockChoices:
        def __init__(self, content):
            self.message = SimpleNamespace(content=content)

    class MockResponse:
        def __init__(self, content):
            self.choices = [MockChoices(content)]

    async def mock_create(**kwargs):
        return MockResponse(json.dumps(expected))

    # Instantiate analyzer and patch client's create
    analyzer = LLMAnalyzer()
    analyzer.openai_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=mock_create)))

    # Run analysis
    issue_data = {
        "issue": {
            "number": 1,
            "title": "Login error",
            "body": "500 when logging in",
            "user": {"login": "alice"},
            "state": "open",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-02",
        },
        "comments": []
    }
    result = await analyzer.analyze_issue(issue_data)

    assert result.summary == expected["summary"]
    assert result.type == IssueType.BUG
    assert result.priority_score.startswith("5")
    assert "authentication" in result.suggested_labels

@pytest.mark.asyncio
async def test_llm_analyzer_handles_bad_json(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class MockChoices:
        def __init__(self, content):
            self.message = SimpleNamespace(content=content)

    class MockResponse:
        def __init__(self, content):
            self.choices = [MockChoices(content)]

    async def mock_create(**kwargs):
        # Not JSON
        return MockResponse("not-json")

    analyzer = LLMAnalyzer()
    analyzer.openai_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=mock_create)))

    with pytest.raises(ValueError):
        await analyzer.analyze_issue({
            "issue": {"number": 1, "title": "x", "body": "", "user": {"login": "u"}, "state": "open", "created_at": "", "updated_at": ""},
            "comments": []
        })
