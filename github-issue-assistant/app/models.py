from enum import Enum
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any

class IssueType(str, Enum):
    """Type of GitHub issue."""
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    DOCUMENTATION = "documentation"
    QUESTION = "question"
    OTHER = "other"

class IssueAnalysis(BaseModel):
    """Analysis results for a GitHub issue."""
    summary: str = Field(..., description="A one-sentence summary of the user's problem or request.")
    type: IssueType = Field(..., description="Classified type of the issue.")
    priority_score: str = Field(
        ..., 
        description="A score from 1 (low) to 5 (critical), with a brief justification."
    )
    suggested_labels: List[str] = Field(..., min_items=1, max_items=5, description="List of suggested GitHub labels.")
    potential_impact: str = Field(..., description="Brief sentence on potential user impact if this is a bug.")

class GitHubIssueRequest(BaseModel):
    """Request model for analyzing a GitHub issue."""
    repo_url: str = Field(..., description="GitHub repository URL (e.g., https://github.com/facebook/react)")
    issue_number: int = Field(..., gt=0, description="GitHub issue number")

class GitHubIssueResponse(BaseModel):
    """Response model for GitHub issue data."""
    issue: Dict[str, Any]
    comments: List[Dict[str, Any]]

class ErrorResponse(BaseModel):
    """Standard error response model."""
    detail: str
    error_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class HealthCheck(BaseModel):
    """Health check response model."""
    status: str
    version: str
    uptime: Optional[float] = None
    dependencies: Optional[Dict[str, str]] = None
