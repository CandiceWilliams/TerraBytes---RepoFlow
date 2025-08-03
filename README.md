# RepoFlow - Repository Analysis Assistant

RepoFlow is a dual-stack application that allows non-coders to interact with open-source repositories through a Codex-style assistant. The system clones repositories, analyzes their structure using an LLM, and generates clickable UI tasks for users to perform code modifications without direct coding.

## Prerequisites

- **Python 3.13+**
- **Node.js 18+**
- **Git**
- **Google API Key** (for Gemini AI)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd TerraBytes---RepoFlow
```

### 2. Get Google API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create a new API key
3. Copy the API key for the next step

### 3. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the `backend/` directory:

```bash
# backend/.env
GOOGLE_API_KEY=your_actual_api_key_here
```

**⚠️ Important:** Replace `your_actual_api_key_here` with your actual Google API key.

### 5. Frontend Setup

```bash
cd ../client

# Install dependencies
npm install
```

## Running the Application

### Start Backend Server

```bash
cd backend
# Make sure virtual environment is activated
uvicorn main:app --reload
```

Backend will run on: `http://localhost:8000`

### Start Frontend Server

```bash
cd client
npm run dev
```

Frontend will run on: `http://localhost:5173`

## Usage

1. **Open** `http://localhost:5173` in your browser
2. **Enter** a GitHub repository URL
3. **Wait** for the system to clone and analyze the repository
4. **Select** a workspace to begin RAG-powered chat
5. **Chat** with the repository using natural language

## API Endpoints

- `POST /api/receive-repo` - Clone and process repository
- `POST /api/get-workspaces` - Retrieve available workspaces  
- `POST /api/select-workspace` - Initialize RAG for selected files
- `POST /api/chat` - RAG-powered chat queries
- `GET /api/check-workspaces` - Check workspace processing status
- `GET /api/check-rag-ready` - Check RAG system readiness

## Backend File Structure

```
backend/
├── core/               # Core business logic (config, database, RAG engine, security)
├── models/             # Pydantic models for API requests/responses  
├── routers/            # API route handlers organized by functionality
├── schemas/            # Database schemas and data structures
├── main.py             # FastAPI application entry point with CORS and API endpoints
├── repoProcessor.py    # Repository cloning and tree structure generation
├── gemini.py           # Gemini API integration for LLM analysis
├── smartChunking.py    # Document chunking for RAG vector database
├── requirements.txt    # Python dependencies
└── pyproject.toml      # Project configuration
```

## Frontend File Structure

```
client/
├── src/
│   ├── App.jsx         # Main React application component
│   ├── ChatPage.jsx    # RAG-powered chat interface
│   ├── WorkSpace.jsx   # Workspace selection and management
│   └── RepoLink.jsx    # Repository URL input component
├── package.json        # Node.js dependencies
└── vite.config.js      # Vite configuration
```

## Troubleshooting

### Common Issues

**1. "GOOGLE_API_KEY not found" error:**
- Ensure `.env` file exists in `backend/` directory
- Verify API key is correct and active

**2. "Module not found" errors:**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

**3. "Port already in use" errors:**
- Backend: Change port with `uvicorn main:app --reload --port 8001`
- Frontend: Vite will automatically suggest alternative ports

**4. Frontend can't connect to backend:**
- Ensure backend is running on `http://localhost:8000`
- Check CORS settings in `main.py`

### Clean Restart

If you encounter persistent issues:

```bash
# Backend
cd backend
rm -rf venv
rm -rf cloned_repos
rm -rf vector_db_chunks
rm workspace.json tree_structure.txt
python -m venv venv
# Activate venv and reinstall requirements

# Frontend  
cd client
rm -rf node_modules
npm install
```

## Development Notes

- **Temporary files** (`cloned_repos/`, `vector_db_chunks/`, etc.) are automatically cleaned up when the backend stops
- **API key** is currently hardcoded in `main.py:29` - this will be moved to environment variables
- **Vector database** is rebuilt each time you select a new workspace
- `__init__.py` files make folders into Python packages for easier imports

## Architecture

**Backend:** Python/FastAPI with LlamaIndex RAG system  
**Frontend:** React/Vite with Bootstrap UI  
**AI:** Google Gemini for embeddings and chat responses  
**Vector Store:** FAISS for document similarity search

---

For issues or questions, please check the troubleshooting section above or contact the development team.