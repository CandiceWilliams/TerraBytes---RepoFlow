# TerraBytes---RepoFlow

## What is RepoFlow?

RepoFlow is a Codex-style assistant designed to help non-coders interact with open-source projects. It uses an LLM to understand a project's codebase and generates button-based tasks for the user (e.g., “Add login page”, “Fix a bug”, “Connect database”).

The frontend displays these tasks as clickable options, and user actions are sent as structured JSON to the backend. The backend uses an LLM to generate the required code changes, which are then shown to the user for approval or directly applied to the repo.

The goal is to make contributing to or customizing software as simple as using a UI — no coding required.

## Dependencies

```python
"fastapi[all]>=0.116.1",
"langchain>=0.3.27",
"langchain-google-genai>=2.1.8",
"motor>=3.7.1",
"pymongo>=4.13.2",
"python-dotenv>=1.1.1",
"python-multipart>=0.0.20",
"uvicorn>=0.35.0"
```

## Backend File Structure Overview

```
backend/
├── core/         
├── db/             
├── models/        
├── routers/       
├── schemas/       
├── .env           
├── main.py
└── pyproject.toml
```

- **core** -  Configuration, Gemini API setup, RAG logic
- **db** - MongoDB Atlas connection and operations 
- **models** - Pydantic models for API requests/responses
- **routers** - API endpoints (FastAPI routers)
- **schemas** - Database schemas and data structures
- **.env** - Environment variables (API keys, DB connection)
- **main.py** - FastAPI app entry point
- **pyproject.toml** - Dependencies

## Notes for team members

- `__init__.py` is responsible for making a folder a *python package* which makes it easier to import the different files and functions that are defined within that folder.