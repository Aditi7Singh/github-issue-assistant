import streamlit as st
import requests
import json
import os
from typing import Optional
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="GitHub Issue Assistant",
    page_icon="🐙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        max-width: 1200px;
        padding: 2rem;
    }
    .stTextInput>div>div>input {
        font-family: monospace;
    }
    .stButton>button {
        background-color: #238636;
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #2ea043;
    }
    .result-box {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1.5rem;
        margin-top: 1rem;
        background-color: #f9f9f9;
    }
    .priority-high {
        color: #d73a49;
        font-weight: bold;
    }
    .priority-medium {
        color: #e36209;
        font-weight: bold;
    }
    .priority-low {
        color: #0366d6;
        font-weight: bold;
    }
    .tag {
        display: inline-block;
        background-color: #ddf4ff;
        color: #0969da;
        padding: 0.2rem 0.5rem;
        border-radius: 2em;
        font-size: 0.8rem;
        margin: 0.2rem;
        white-space: nowrap;
    }
    .bug-tag { background-color: #ffdce0; color: #d73a49; }
    .feature-tag { background-color: #d1f7c4; color: #1a7f37; }
    .docs-tag { background-color: #d4c5f9; color: #8250df; }
    .question-tag { background-color: #d4e6ff; color: #0969da; }
    .other-tag { background-color: #d8d8d8; color: #4f4f4f; }
    </style>
""", unsafe_allow_html=True)

# App title and description
st.title("🐙 GitHub Issue Assistant")
st.markdown("""
    Analyze GitHub issues with AI to get structured insights, priority scores, and suggested labels.
    This tool helps developers and maintainers quickly understand and triage GitHub issues.
""")

# Sidebar with instructions and examples
with st.sidebar:
    st.header("How to Use")
    st.markdown("""
    1. Enter a GitHub repository URL (e.g., `https://github.com/facebook/react`)
    2. Enter an issue number
    3. Click "Analyze Issue"
    4. View the AI-powered analysis
    
    ### Example Repositories
    - [facebook/react](https://github.com/facebook/react) (try issue #1)
    - [tensorflow/tensorflow](https://github.com/tensorflow/tensorflow)
    - [microsoft/vscode](https://github.com/microsoft/vscode)
    
    ### What's Analyzed
    - Issue type (bug, feature request, etc.)
    - Priority score (1-5)
    - Suggested labels
    - Potential impact (for bugs)
    - Summary of the issue
    """)
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    Built with ❤️ for the Seedling Labs internship application.
    
    **Tech Stack:**
    - Backend: FastAPI
    - Frontend: Streamlit
    - AI: OpenAI GPT-4
    - Hosting: Local (for now)
    """)

# API configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def get_priority_class(score: int) -> str:
    """Get CSS class for priority score."""
    if score >= 4:
        return "priority-high"
    elif score >= 3:
        return "priority-medium"
    return "priority-low"

def get_issue_type_tag(issue_type: str) -> str:
    """Get CSS class for issue type tag."""
    type_classes = {
        "bug": "bug-tag",
        "feature_request": "feature-tag",
        "documentation": "docs-tag",
        "question": "question-tag",
    }
    return type_classes.get(issue_type, "other-tag")

def analyze_issue(repo_url: str, issue_number: int) -> Optional[dict]:
    """Call the backend API to analyze a GitHub issue."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyze",
            json={
                "repo_url": repo_url,
                "issue_number": issue_number
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                st.error(f"Error: {error_data.get('detail', str(e))}")
            except ValueError:
                st.error(f"Error: {e.response.text or str(e)}")
        else:
            st.error(f"Failed to connect to the API: {str(e)}")
        return None

def display_analysis(result: dict):
    """Display the analysis results in a user-friendly way."""
    with st.container():
        st.markdown("### 📊 Analysis Results")
        
        # Issue type and priority in columns
        col1, col2 = st.columns(2)
        
        with col1:
            issue_type = result.get("type", "other").replace("_", " ").title()
            tag_class = get_issue_type_tag(result.get("type", ""))
            st.markdown(f"**Type:** <span class='tag {tag_class}'>{issue_type}</span>", unsafe_allow_html=True)
        
        with col2:
            prio_str = str(result.get("priority_score", "1"))
            # Extract leading digit as score if present
            try:
                prio_num = int(prio_str.strip()[0]) if prio_str.strip()[0].isdigit() else 1
            except Exception:
                prio_num = 1
            priority_class = get_priority_class(prio_num)
            st.markdown(f"**Priority:** <span class='{priority_class}'>{prio_str}</span>", unsafe_allow_html=True)
        
        # Suggested labels
        st.markdown("**Suggested Labels:**")
        label_cols = st.columns(4)
        for i, label in enumerate(result.get("suggested_labels", [])[:4]):
            with label_cols[i % 4]:
                st.markdown(f"<span class='tag'>{label}</span>", unsafe_allow_html=True)
        
        # Summary and impact
        st.markdown("**Summary:**")
        st.info(result.get("summary", "No summary available."))
        
        if result.get("potential_impact"):
            st.markdown("**Potential Impact:**")
            st.warning(result["potential_impact"])
        
        # Raw JSON toggle
        with st.expander("View Raw JSON"):
            st.json(result)
            if st.button("Copy JSON to Clipboard"):
                st.code(json.dumps(result, indent=2), language="json")
                st.success("JSON copied. Select and copy from the code block if auto-copy isn't supported.")

def main():
    """Main application function."""
    # Input form
    with st.form("issue_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            repo_url = st.text_input(
                "GitHub Repository URL",
                placeholder="https://github.com/owner/repo",
                help="Full URL of the GitHub repository"
            )
        
        with col2:
            issue_number = st.number_input(
                "Issue Number",
                min_value=1,
                step=1,
                help="GitHub issue number"
            )
        
        analyze_clicked = st.form_submit_button("🔍 Analyze Issue")
    
    # Handle form submission
    if analyze_clicked:
        if not repo_url or not issue_number:
            st.warning("Please provide both a repository URL and an issue number.")
            return
        
        with st.spinner("🔍 Analyzing issue... This may take a moment..."):
            result = analyze_issue(repo_url, int(issue_number))
            
            if result:
                # Display the analysis
                display_analysis(result)
                
                # Add a success message
                st.success("✅ Analysis complete!")
                
                # Add a link to the actual GitHub issue
                repo_path = "/".join(repo_url.rstrip("/").split("/")[-2:])
                issue_url = f"https://github.com/{repo_path}/issues/{issue_number}"
                st.markdown(f"🔗 [View on GitHub]({issue_url})")

if __name__ == "__main__":
    main()
