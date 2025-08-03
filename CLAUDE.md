# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RepoFlow is a dual-stack application that allows non-coders to interact with open-source repositories through a Codex-style assistant. The system clones repositories, analyzes their structure using an LLM, and generates clickable UI tasks for users to perform code modifications without direct coding.

## Architecture

**Backend (Python/FastAPI):**
- `backend/main.py` - FastAPI application entry point with CORS and API endpoints
- `backend/core/` - Core business logic (config, database, RAG engine, security)
- `backend/models/` - Pydantic models for API requests/responses  
- `backend/routers/` - API route handlers organized by functionality
- `backend/schemas/` - Database schemas and data structures
- `backend/repoProcessor.py` - Repository cloning and tree structure generation
- `backend/gemini.py` - Gemini API integration for LLM analysis
- `backend/smartChunking.py` - Document chunking for RAG vector database

**Frontend (React/Vite):**
- `client/src/App.jsx` - Main React application component
- `client/src/ChatPage.jsx` - RAG-powered chat interface
- `client/src/WorkSpace.jsx` - Workspace selection and management
- `client/src/RepoLink.jsx` - Repository URL input component

## Development Commands

### Backend
```bash
cd backend
uvicorn main:app --reload  # Start development server
```

### Frontend  
```bash
cd client
npm run dev     # Start development server (Vite)
npm run build   # Production build
npm run lint    # ESLint code checking
```

## Key Technical Details

**RAG System:**
- Uses LlamaIndex with FAISS vector store for document retrieval
- Gemini embeddings for text vectorization
- Smart chunking processes repository files into searchable chunks
- Global `RAG_QUERY_ENGINE` loaded into memory for chat responses

**Repository Processing Flow:**
1. Clone repository to `backend/cloned_repos/`
2. Generate tree structure using `repoProcessor.py`
3. LLM analyzes structure and creates workspaces in `workspace.json`
4. User selects workspace triggering smart chunking
5. FAISS index built for RAG-powered chat

**API Endpoints:**
- `POST /api/receive-repo` - Clone and process repository
- `POST /api/get-workspaces` - Retrieve available workspaces
- `POST /api/select-workspace` - Initialize RAG for selected files
- `POST /api/chat` - RAG-powered chat queries
- `GET /api/check-workspaces` - Check workspace processing status
- `GET /api/check-rag-ready` - Check RAG system readiness

**Environment Requirements:**
- Python 3.13+ with FastAPI, LlamaIndex, and Gemini AI
- Node.js with React, Vite, and Bootstrap
- Google API key for Gemini (currently hardcoded in main.py:24)

## Repository Context

The `backend/cloned_repos/` directory contains multiple copies of tiny_python_projects for testing. The main codebase focuses on making repository interaction accessible through natural language and UI-driven workflows rather than direct code editing.