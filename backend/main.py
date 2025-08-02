# main.py

import os
import json
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import the necessary functions from the separate files
from repoProcessor import process_repository
from gemini import stageOne

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
# It's a good practice to use a dedicated directory for this.
REPOS_DIR = "./cloned_repos"
os.makedirs(REPOS_DIR, exist_ok=True)


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


@app.post("/api/receive-repo")
async def receive_repo(request_body: RepoUrlRequest, background_tasks: BackgroundTasks):
    """
    Receives a GitHub repository URL, clones it, and processes its contents.
    The LLM analysis is run as a background task after a success message is sent.
    """
    repo_url = request_body.repoUrl.strip()

    if not repo_url:
        raise HTTPException(
            status_code=400,
            detail={"message": "Missing 'repoUrl' in request body", "err": True}
        )
    
    # Call the function from the separate file to handle all the processing
    result = process_repository(repo_url)

    # After the file is created, add the LLM call as a background task.
    # The stageOne function now needs the file path as an argument.
    background_tasks.add_task(stageOne, result['tree_file'])

    # Return the immediate success message to the client
    return {
        "message": "Repository cloned and tree structure generated! LLM analysis is running in the background.",
        "repo_path": result['repo_path'],
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
    workspace_file_path = "workspace.json"
    
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
async def select_workspace(workspace_data: WorkspaceRequest):
    """
    Receives a single workspace object from the frontend.
    """
    # For now, we'll just return a success message and the received data.
    # Future logic to process this selected workspace would go here.
    return {
        "message": "Workspace received successfully!",
        "workspace_data": workspace_data,
        "err": False
    }


# A simple example route to test that the API is working
@app.get("/")
def read_root():
    """A simple root endpoint to show the API is running."""
    return {"message": "Hello from the RepoFlow API!"}
