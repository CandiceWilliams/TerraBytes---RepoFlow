# main.py

import os
import json
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import the necessary functions from the separate files
from repoProcessor import process_repository
from gemini import stageOne
from smartChunking import smart_chunking

# Initialize the FastAPI application
app = FastAPI(
    title="RepoFlow Backend",
    description="Backend API for the RepoFlow project."
)

# Define the allowed origins for CORS.
# For production, replace "*" with your specific frontend URL.
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "*"
]

# Add the CORS middleware.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define a base directory for storing cloned repositories
# We use an absolute path to avoid issues with the current working directory.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPOS_DIR = os.path.join(BASE_DIR, "cloned_repos")
os.makedirs(REPOS_DIR, exist_ok=True)

# Global variable to store the path of the most recently cloned repository
LATEST_REPO_PATH = None


# ----------------------------------------------------
# Pydantic models for request bodies
# ----------------------------------------------------
class RepoUrlRequest(BaseModel):
    """Defines the expected structure of the incoming request body for cloning a repository."""
    repoUrl: str

class WorkspaceRequest(BaseModel):
    """Defines the expected structure of a single workspace object."""
    name: str
    description: str
    fileStructure: list[str]
    returnPrompt: str
    assumptions: str

class QueryRequest(BaseModel):
    """Defines the expected structure for a user query."""
    query: str


@app.post("/api/receive-repo")
async def receive_repo(request_body: RepoUrlRequest, background_tasks: BackgroundTasks):
    """
    Receives a GitHub repository URL, clones it, and processes its contents.
    The LLM analysis is run as a background task after a success message is sent.
    """
    global LATEST_REPO_PATH
    repo_url = request_body.repoUrl.strip()

    if not repo_url:
        raise HTTPException(
            status_code=400,
            detail={"message": "Missing 'repoUrl' in request body", "err": True}
        )
    
    # Call the function from the separate file to handle all the processing
    result = process_repository(repo_url)
    
    # Store the correct repo path in the global variable for later use
    # Ensure the path is always absolute to prevent future issues
    LATEST_REPO_PATH = os.path.abspath(result['repo_path'])

    # After the file is created, add the LLM call as a background task.
    workspace_file_path = os.path.join(BASE_DIR, "workspace.json")
    background_tasks.add_task(stageOne, result['tree_file'], workspace_file_path)

    # Return the immediate success message to the client
    return {
        "message": "Repository cloned and tree structure generated! LLM analysis is running in the background.",
        "repo_path": LATEST_REPO_PATH,
        "tree_structure": result['tree_structure'],
        "tree_file": result['tree_file'],
        "err": False
    }


# ----------------------------------------------------
# New API endpoint to get the list of workspaces
# ----------------------------------------------------
@app.post("/api/get-workspaces")
async def get_workspaces():
    """
    Reads the 'workspace.json' file, converts it into a list of objects, and returns it.
    """
    workspace_file_path = os.path.join(BASE_DIR, "workspace.json")
    
    if not os.path.exists(workspace_file_path):
        raise HTTPException(
            status_code=404,
            detail={"message": "Workspace file not found. Please process a repository first.", "err": True}
        )
    
    try:
        with open(workspace_file_path, "r", encoding="utf-8") as f:
            workspaces = json.load(f)
        return workspaces
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail={"message": "Could not decode workspace.json. The file is malformed.", "err": True}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"An unexpected error occurred while reading the workspace file: {e}", "err": True}
        )

# ----------------------------------------------------
# New API endpoint to receive a selected workspace
# ----------------------------------------------------
@app.post("/api/select-workspace")
async def select_workspace(workspace_data: WorkspaceRequest, background_tasks: BackgroundTasks):
    """
    Receives a single workspace object from the frontend and triggers the
    smart chunking process for the files in that workspace.
    """
    global LATEST_REPO_PATH

    if LATEST_REPO_PATH is None:
        raise HTTPException(
            status_code=400,
            detail={"message": "No cloned repository path found. Please clone a repo first.", "err": True}
        )
    
    # Use the stored absolute path directly
    repo_dir = LATEST_REPO_PATH

    # Get the file paths from the received workspace data
    file_paths_to_chunk = workspace_data.fileStructure
    
    print(f"Selected repo directory for chunking: {repo_dir}")
    
    # Add a print statement to show the exact full path being checked
    for file_path in file_paths_to_chunk:
        full_path = os.path.join(repo_dir, file_path)
        print(f"DEBUG: Checking path: {full_path}")
        
    print(f"Files to chunk: {file_paths_to_chunk}")

    # Start the smart chunking process as a background task
    # Define the absolute path for the vector database file
    db_file_path = os.path.join(BASE_DIR, "chunks.vector")
    
    # Pass the new db_file_path argument to the smart_chunking function
    background_tasks.add_task(smart_chunking, repo_dir, file_paths_to_chunk, db_file_path)

    return {
        "message": "Workspace received successfully. Smart chunking process has been initiated in the background!",
        "workspace_data": workspace_data,
        "err": False
    }

# ----------------------------------------------------
# New API endpoint to check if the workspace file is ready
# ----------------------------------------------------
@app.get("/api/check-workspaces")
def check_workspaces():
    """
    Checks if the workspace.json file exists and is ready for use.
    """
    workspace_file_path = os.path.join(BASE_DIR, "workspace.json")
    is_ready = os.path.exists(workspace_file_path)

    # We also check if the file is non-empty to ensure it's not a partial write
    if is_ready:
        is_ready = os.path.getsize(workspace_file_path) > 0
    
    return {"isReady": is_ready}

# A simple example route to test that the API is working
@app.get("/")
def read_root():
    """A simple root endpoint to show the API is running."""
    return {"message": "Hello from the RepoFlow API!"}
