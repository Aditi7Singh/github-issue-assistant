import os
import time
import httpx
from typing import Dict, Any, Optional, Tuple
from fastapi import HTTPException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GitHubClient:
    """Client for interacting with the GitHub API."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        # Add GitHub token if available (for higher rate limits)
        if token := os.getenv("GITHUB_TOKEN"):
            self.headers["Authorization"] = f"Bearer {token}"
        # Simple in-memory TTL cache
        self._cache: dict[Tuple[str, str, int], Dict[str, Any]] = {}
        self._cache_expiry: dict[Tuple[str, str, int], float] = {}
        self.ttl_seconds: int = int(os.getenv("GITHUB_CACHE_TTL", "300"))  # default 5 minutes

    def _cache_get(self, owner: str, repo: str, issue_number: int) -> Optional[Dict[str, Any]]:
        key = (owner, repo, issue_number)
        now = time.time()
        if key in self._cache and self._cache_expiry.get(key, 0) > now:
            return self._cache[key]
        # purge expired
        if key in self._cache:
            self._cache.pop(key, None)
            self._cache_expiry.pop(key, None)
        return None

    def _cache_set(self, owner: str, repo: str, issue_number: int, value: Dict[str, Any]):
        key = (owner, repo, issue_number)
        self._cache[key] = value
        self._cache_expiry[key] = time.time() + self.ttl_seconds
    
    async def get_issue(self, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
        """Fetch a specific issue from a GitHub repository."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Issue #{issue_number} not found in {owner}/{repo} or repository is private"
                    )
                elif e.response.status_code == 403:
                    # Handle rate limiting
                    rate_limit_remaining = e.response.headers.get('X-RateLimit-Remaining', 'unknown')
                    if rate_limit_remaining == '0':
                        reset_time = e.response.headers.get('X-RateLimit-Reset', 'unknown')
                        raise HTTPException(
                            status_code=429,
                            detail={
                                "message": "GitHub API rate limit exceeded",
                                "reset_time": reset_time,
                                "docs": "https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting"
                            }
                        )
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"GitHub API error: {str(e)}"
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to connect to GitHub API: {str(e)}"
                )
    
    async def get_issue_comments(self, owner: str, repo: str, issue_number: int) -> list[Dict[str, Any]]:
        """Fetch comments for a specific issue."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return []  # No comments found
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Failed to fetch comments: {str(e)}"
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to connect to GitHub API: {str(e)}"
                )
    
    async def get_issue_data(self, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
        """Fetch both issue and its comments."""
        # Try cache first
        cached = self._cache_get(owner, repo, issue_number)
        if cached is not None:
            return cached

        issue = await self.get_issue(owner, repo, issue_number)
        comments = await self.get_issue_comments(owner, repo, issue_number)
        result = {"issue": issue, "comments": comments}
        self._cache_set(owner, repo, issue_number, result)
        return result

# Singleton instance
github_client = GitHubClient()
