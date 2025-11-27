import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from .models import IssueAnalysis, IssueType

# Load environment variables
load_dotenv()

class LLMAnalyzer:
    """Handles LLM-based analysis of GitHub issues."""
    
    SYSTEM_PROMPT = """
    You are an expert GitHub issue analyst. Your task is to analyze GitHub issues and provide structured insights.
    
    For each issue, analyze the title, description, and comments to understand:
    1. What the issue is about
    2. Whether it's a bug, feature request, documentation issue, question, or other
    3. Its priority level (1-5, with 5 being most critical)
    4. Relevant GitHub labels that should be applied
    5. If it's a bug, the potential impact on users
    
    Your response MUST be a valid JSON object with the following structure (field names must match exactly):
    {
        "summary": "A one-sentence summary of the user's problem or request.",
        "type": "Classify as: bug, feature_request, documentation, question, or other.",
        "priority_score": "A score from 1 (low) to 5 (critical), with a brief justification.",
        "suggested_labels": ["label1", "label2", "label3"],
        "potential_impact": "Brief sentence on potential user impact if this is a bug."
    }
    
    Guidelines:
    - Be concise but thorough in your analysis
    - For bugs, consider the severity and potential impact on users
    - For feature requests, consider the potential value to users
    - Use existing GitHub label conventions when possible
    - If information is missing or unclear, make reasonable assumptions and note them
    """
    
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.openai_client = None
        self.gemini = None
        
        if self.provider == "openai":
            from openai import AsyncOpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            self.openai_client = AsyncOpenAI(api_key=api_key)
        elif self.provider == "gemini":
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is not set")
            genai.configure(api_key=api_key)
            self.gemini = genai
        else:
            raise ValueError("Unsupported LLM_PROVIDER. Use 'openai' or 'gemini'.")
    
    def _format_issue_data(self, issue_data: Dict[str, Any]) -> str:
        """Format issue data for the LLM prompt."""
        issue = issue_data["issue"]
        comments = issue_data["comments"]
        
        # Format comments
        comments_text = ""
        if comments:
            comments_text = "\n\nComments:\n"
            for i, comment in enumerate(comments, 1):
                comments_text += f"\n--- Comment {i} by {comment['user']['login']} ---\n{comment['body']}\n"
        
        # Format the full prompt
        prompt = f"""
# GitHub Issue Analysis

## Issue: #{issue['number']} - {issue['title']}

**State:** {'Open' if issue['state'] == 'open' else 'Closed'}
**Created by:** {issue['user']['login']}
**Created at:** {issue['created_at']}
**Updated at:** {issue['updated_at']}

## Description
{issue.get('body', 'No description provided.')}
{comments_text}

## Your Analysis
Please analyze this issue and provide the requested JSON response.
"""
        return prompt.strip()
    
    async def analyze_issue(self, issue_data: Dict[str, Any]) -> IssueAnalysis:
        """Analyze a GitHub issue using the LLM."""
        # Format the prompt
        user_prompt = self._format_issue_data(issue_data)
        
        try:
            if self.provider == "openai":
                response = await self.openai_client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content
            else:
                # Gemini JSON response
                model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
                model = self.gemini.GenerativeModel(model_name)
                result = model.generate_content(
                    [
                        {"text": self.SYSTEM_PROMPT},
                        {"text": user_prompt}
                    ]
                )
                # The response may contain JSON in text
                content = result.text

            parsed = json.loads(content)
            # Normalize 'type' value
            parsed_type = str(parsed.get("type", "other")).strip().lower().replace(" ", "_")
            if parsed_type not in {t.value for t in IssueType}:
                parsed_type = "other"
            
            # Ensure priority_score is string
            prio = parsed.get("priority_score", "1")
            if not isinstance(prio, str):
                prio = str(prio)

            return IssueAnalysis(
                summary=parsed.get("summary", ""),
                type=IssueType(parsed_type),
                priority_score=prio,
                suggested_labels=parsed.get("suggested_labels", [])[:5],
                potential_impact=parsed.get("potential_impact", "")
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response: {str(e)}")
        except Exception as e:
            raise Exception(f"Error during LLM analysis: {str(e)}")

# Singleton instance
try:
    llm_analyzer = LLMAnalyzer()
except Exception as _e:
    # Allow API to start without LLM so /health works; /analyze will report unavailable
    llm_analyzer = None
