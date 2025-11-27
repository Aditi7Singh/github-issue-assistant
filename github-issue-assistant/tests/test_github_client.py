import pytest
import httpx
from unittest.mock import patch
from app.github_client import GitHubClient
from fastapi import HTTPException

@pytest.fixture
def github_client():
    return GitHubClient()

@pytest.mark.asyncio
async def test_get_issue_success(github_client):
    """Test successful retrieval of a GitHub issue."""
    mock_response = {
        "number": 1,
        "title": "Test Issue",
        "body": "This is a test issue",
        "user": {"login": "testuser"},
        "state": "open"
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        class MockResp:
            def raise_for_status(self):
                return None
            def json(self):
                return mock_response
        mock_get.return_value = MockResp()
        issue = await github_client.get_issue("testowner", "testrepo", 1)
        assert issue == mock_response

@pytest.mark.asyncio
async def test_get_issue_not_found(github_client):
    """Test handling of a non-existent issue."""
    with patch('httpx.AsyncClient.get') as mock_get:
        request = httpx.Request("GET", "https://api.github.com/repos/owner/repo/issues/999")
        response = httpx.Response(404, request=request)
        class MockResp:
            def raise_for_status(self):
                raise httpx.HTTPStatusError("Not Found", request=request, response=response)
        mock_get.return_value = MockResp()
        with pytest.raises(HTTPException) as exc_info:
            await github_client.get_issue("owner", "repo", 999)
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()

@pytest.mark.asyncio
async def test_get_issue_rate_limit(github_client):
    """Test handling of GitHub API rate limiting."""
    response = httpx.Response(
        403,
        headers={
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "1625097600"
        }
    )
    
    with patch('httpx.AsyncClient.get') as mock_get:
        request = httpx.Request("GET", "https://api.github.com/repos/owner/repo/issues/1")
        class MockResp:
            def raise_for_status(self):
                raise httpx.HTTPStatusError("Rate limit exceeded", request=request, response=response)
        mock_get.return_value = MockResp()
        with pytest.raises(HTTPException) as exc_info:
            await github_client.get_issue("owner", "repo", 1)
        assert exc_info.value.status_code == 429
        assert "rate limit" in str(exc_info.value.detail).lower()

@pytest.mark.asyncio
async def test_get_issue_comments_success(github_client):
    """Test successful retrieval of issue comments."""
    mock_comments = [
        {"id": 1, "user": {"login": "user1"}, "body": "First comment"},
        {"id": 2, "user": {"login": "user2"}, "body": "Second comment"}
    ]
    
    with patch('httpx.AsyncClient.get') as mock_get:
        class MockResp:
            def raise_for_status(self):
                return None
            def json(self):
                return mock_comments
        mock_get.return_value = MockResp()
        comments = await github_client.get_issue_comments("testowner", "testrepo", 1)
        assert comments == mock_comments

@pytest.mark.asyncio
async def test_get_issue_data_success(github_client):
    """Test successful retrieval of both issue and its comments."""
    mock_issue = {"number": 1, "title": "Test Issue"}
    mock_comments = [{"id": 1, "body": "Test comment"}]
    
    with patch.object(github_client, 'get_issue', return_value=mock_issue) as mock_get_issue, \
         patch.object(github_client, 'get_issue_comments', return_value=mock_comments) as mock_get_comments:
        
        result = await github_client.get_issue_data("owner", "repo", 1)
        
        assert result == {"issue": mock_issue, "comments": mock_comments}
        mock_get_issue.assert_called_once_with("owner", "repo", 1)
        mock_get_comments.assert_called_once_with("owner", "repo", 1)
