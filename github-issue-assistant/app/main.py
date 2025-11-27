from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, Field, ValidationError
from typing import List, Optional, Dict, Any
import os
import httpx
from dotenv import load_dotenv
from enum import Enum
import time
import json

# Import local modules
from .github_client import github_client
from .llm_analyzer import llm_analyzer
from .models import (
    IssueAnalysis, 
    GitHubIssueRequest, 
    GitHubIssueResponse,
    ErrorResponse,
    HealthCheck
)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="GitHub Issue Assistant API",
    description="API for analyzing GitHub issues using AI",
    version="1.0.0",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Application metadata
APP_VERSION = "1.0.0"
START_TIME = time.time()

# Initialize LLM analyzer
try:
    llm_analyzer  # This will raise NameError if not initialized
except NameError:
    try:
        from .llm_analyzer import llm_analyzer
    except Exception as e:
        print(f"Warning: LLM Analyzer initialization failed: {str(e)}")
        llm_analyzer = None

# Utility functions
def extract_owner_repo(repo_url: str) -> tuple[str, str]:
    """Extract owner and repository name from GitHub URL."""
    try:
        # Remove trailing slash if exists
        repo_url = repo_url.rstrip('/')
        # Handle both https and http URLs
        if 'github.com' not in repo_url:
            raise ValueError("Invalid GitHub URL")
        
        # Split the URL and extract owner/repo
        parts = repo_url.split('github.com/')[-1].split('/')
        if len(parts) < 2:
            raise ValueError("Invalid GitHub repository URL format")
            
        owner, repo = parts[0], parts[1]
        return owner, repo
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                detail=f"Invalid GitHub repository URL: {str(e)}",
                error_type="invalid_url",
                metadata={"input": repo_url}
            ).dict()
        )

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail if isinstance(exc.detail, dict) else str(exc.detail),
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"An unexpected error occurred: {str(exc)}",
            "error_type": "internal_server_error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "error_type": "validation_error",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY
        }
    )

# API Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "GitHub Issue Assistant API",
        "version": APP_VERSION,
        "documentation": "/docs"
    }

@app.post(
    "/analyze", 
    response_model=IssueAnalysis,
    responses={
        200: {"model": IssueAnalysis, "description": "Analysis completed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid input"},
        404: {"model": ErrorResponse, "description": "Issue not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def analyze_issue(request: GitHubIssueRequest):
    """
    Analyze a GitHub issue using AI and return structured insights.
    
    - **repo_url**: Full GitHub repository URL (e.g., https://github.com/facebook/react)
    - **issue_number**: GitHub issue number (must be a positive integer)
    
    Returns a structured analysis including issue type, priority, suggested labels, and impact assessment.
    """
    try:
        # Extract owner and repo from URL
        owner, repo = extract_owner_repo(request.repo_url)
        
        # Fetch issue data from GitHub
        issue_data = await github_client.get_issue_data(owner, repo, request.issue_number)
        
        # Analyze with LLM
        if not llm_analyzer:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=ErrorResponse(
                    detail="LLM service is not available",
                    error_type="service_unavailable"
                ).dict()
            )
            
        analysis = await llm_analyzer.analyze_issue(issue_data)
        
        return analysis
        
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        # Log the error and return a 500 response
        print(f"Error analyzing issue: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                detail=f"An error occurred while processing your request: {str(e)}",
                error_type="analysis_error"
            ).dict()
        )

@app.get(
    "/health", 
    response_model=HealthCheck,
    tags=["System"]
)
async def health_check():
    """
    Health check endpoint.
    
    Returns the current health status of the API including version and uptime.
    """
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "uptime": time.time() - START_TIME,
        "dependencies": {
            "github_api": "operational" if github_client else "unavailable",
            "llm_service": "operational" if llm_analyzer else "unavailable"
        }
    }

# Run with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
