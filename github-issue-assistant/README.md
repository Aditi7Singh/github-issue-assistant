# 🐙 GitHub Issue Assistant

An AI-powered tool that analyzes GitHub issues and provides structured insights to help developers and maintainers prioritize and triage issues more effectively.

## ✨ Features

- **AI-Powered Analysis**: Uses OpenAI's GPT-4 to analyze GitHub issues
- **Structured Output**: Provides consistent, structured information about each issue
- **Priority Scoring**: Rates issues from 1 (low) to 5 (critical)
- **Label Suggestions**: Recommends relevant GitHub labels
- **Impact Assessment**: Highlights potential user impact for bugs
- **Modern Web Interface**: Clean, responsive UI built with Streamlit
- **RESTful API**: Built with FastAPI for easy integration with other tools

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- [Poetry](https://python-poetry.org/) (recommended) or pip
- OpenAI API key (get one [here](https://platform.openai.com/)) or Google Gemini API key (get one [here](https://ai.google.dev/))
- (Optional) GitHub Personal Access Token (for higher rate limits)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/github-issue-analyzer.git
   cd github-issue-analyzer
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and configure your LLM provider:
   ```
   # Provider: openai | gemini
   LLM_PROVIDER=openai

   # OpenAI settings (if LLM_PROVIDER=openai)
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini

   # Gemini settings (if LLM_PROVIDER=gemini)
   # GEMINI_API_KEY=your_gemini_api_key_here
   # GEMINI_MODEL=gemini-1.5-flash

   # Optional but recommended to avoid rate limits
   # GITHUB_TOKEN=your_github_token_here
   # Cache TTL (seconds)
   GITHUB_CACHE_TTL=300
   ```

3. **Install dependencies**
   
   Using Poetry (recommended):
   ```bash
   poetry install
   ```
   
   Or using pip:
   ```bash
   pip install -r requirements.txt
   ```

## 🏃 Running the Application

### Backend API Server

```bash
# Using Poetry
poetry run uvicorn app.main:app --reload

# Or with Python directly
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend (Streamlit)

In a new terminal window:

```bash
# Using Poetry
poetry run streamlit run frontend/streamlit_app.py

# Or with Python directly
streamlit run frontend/streamlit_app.py
```

Open your browser to `http://localhost:8501`

## 🛠️ API Documentation

Once the backend is running, you can access:

- **Interactive API Docs**: `http://localhost:8000/docs`
- **Alternative Docs**: `http://localhost:8000/redoc`

### Example API Request

```bash
curl -X 'POST' \
  'http://localhost:8000/analyze' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "repo_url": "https://github.com/facebook/react",
    "issue_number": 1
  }'
```

### Response JSON Schema (exact)
```json
{
  "summary": "A one-sentence summary of the user's problem or request.",
  "type": "Classify as: bug, feature_request, documentation, question, or other.",
  "priority_score": "A score from 1 (low) to 5 (critical), with a brief justification.",
  "suggested_labels": ["Array of 2-3 relevant GitHub labels like 'bug', 'UI', 'authentication'"],
  "potential_impact": "Brief sentence on potential user impact if this is a bug."
}
```

## 🧪 Testing

Run the test suite with:

```bash
# Using Poetry
poetry run pytest -v

# Or with Python directly
pytest -v
```

Run a specific test file:
```bash
pytest -q tests/test_api.py
```

## 🏗️ Project Structure

```
github-issue-assistant/
├── .env.example             # Example environment variables
├── .gitignore               # Git ignore file
├── poetry.lock              # Poetry lock file
├── pyproject.toml           # Project dependencies
├── README.md                # This file
│
├── app/                     # Backend application
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── github_client.py     # GitHub API client
│   ├── llm_analyzer.py      # LLM integration
│   └── models.py            # Pydantic models
│
├── frontend/                # Streamlit frontend
│   └── streamlit_app.py     # Streamlit application
│
└── tests/                   # Test files
    └── test_github_client.py
    └── test_llm_analyzer.py
```

## 📦 Caching
- The GitHub client uses an in-memory TTL cache to reduce API calls and mitigate rate limiting.
- Configure via `GITHUB_CACHE_TTL` (default 300 seconds).

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [Streamlit](https://streamlit.io/)
- Powered by [OpenAI](https://openai.com/)
- Inspired by the need for better issue triage in open source projects

## 📬 Contact

For any questions or feedback, please open an issue on GitHub.

## ☁️ Deployment

### Docker (Local or Any Docker Host)
Build and run the API server:
```bash
docker build -t gh-issue-assistant .
docker run -p 8000:8000 --env-file .env gh-issue-assistant
```
Open http://localhost:8000/docs

For the Streamlit frontend (optional), run locally:
```bash
streamlit run frontend/streamlit_app.py
```

### Render.com (Docker)
- Create a new Web Service
- Select your GitHub repo
- Environment: Docker
- Build Command: (leave empty, Dockerfile used)
- Start Command: (use Dockerfile CMD)
- Add Environment Variables from `.env`
- Expose port 8000

### Railway.app
1. Create a new project and select your GitHub repo.
2. Add a service from Dockerfile.
3. Add environment variables from `.env`.
4. Set PORT to 8000 if required.

Once deployed, set `API_BASE_URL` in the frontend environment (or `.streamlit/secrets.toml`) to the deployed API URL.
