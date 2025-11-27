import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import IssueAnalysis, IssueType

client = TestClient(app)

class DummyAnalyzer:
    async def analyze_issue(self, issue_data):
        return IssueAnalysis(
            summary="Test summary",
            type=IssueType.BUG,
            priority_score="3 - medium impact",
            suggested_labels=["bug", "ui"],
            potential_impact="Some users affected"
        )

@pytest.fixture(autouse=True)
def patch_llm_analyzer(monkeypatch):
    from app import main as main_module
    main_module.llm_analyzer = DummyAnalyzer()


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"].startswith("GitHub Issue Assistant API")


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


def test_analyze_invalid_url():
    body = {"repo_url": "https://google.com/notgithub", "issue_number": 1}
    resp = client.post("/analyze", json=body)
    assert resp.status_code == 400


def test_analyze_success(monkeypatch):
    # Mock GitHub client methods to avoid network calls
    from app import main as main_module
    async def mock_get_issue_data(owner, repo, issue):
        return {
            "issue": {
                "number": issue,
                "title": "Sample title",
                "body": "Sample body",
                "user": {"login": "alice"},
                "state": "open",
                "created_at": "2024-01-01",
                "updated_at": "2024-01-02",
            },
            "comments": []
        }
    main_module.github_client.get_issue_data = mock_get_issue_data

    body = {"repo_url": "https://github.com/owner/repo", "issue_number": 42}
    resp = client.post("/analyze", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert set(["summary", "type", "priority_score", "suggested_labels", "potential_impact"]).issubset(data.keys())
    assert isinstance(data["priority_score"], str)
