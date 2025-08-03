# main.py

import os
import json
import time
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import the necessary functions from the separate files
from repoProcessor import process_repository
from gemini import stageOne
from smartChunking import smart_chunking

# Import LlamaIndex components for RAG
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss
from llama_index.embeddings.gemini import GeminiEmbedding
import google.generativeai as genai
import numpy as np # Import numpy for loading binary faiss file

# Configure the Gemini API key for the RAG query engine
API_KEY = "AIzaSyDAkKSlkPXRva8ywSZKOUt0zpxReHKTweo"
try:
    genai.configure(api_key=API_KEY)
except KeyError:
    print("FATAL ERROR: 'GOOGLE_API_KEY' environment variable not set.")
    print("Please set it before running the script.")
    pass

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
# Define the directory for the vector database
VECTOR_DB_DIR = os.path.join(BASE_DIR, "vector_db_chunks")

# Global variable to hold the RAG query engine instance.
# This will be loaded once after the vector DB is ready.
RAG_QUERY_ENGINE = None

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

# ----------------------------------------------------
# New function to load the RAG model as a background task
# ----------------------------------------------------
async def _load_rag_model():
    """
    Background task to load the RAG model and store it in a global variable.
    This prevents reloading the index for every chat request.
    """
    global RAG_QUERY_ENGINE
    
    index_store_path = os.path.join(VECTOR_DB_DIR, "index_store.json")

    # Wait for the index store file to be created by smart_chunking
    while not os.path.exists(index_store_path):
        print("Waiting for FAISS index file to be created...")
        time.sleep(2) # Poll every 2 seconds

    try:
        print("Loading RAG model into memory...")
        # Re-initialize the embedding model (if not globally available and configured)
        embed_model = GeminiEmbedding(api_key=API_KEY)
        
        # Create a storage context and load from the persisted directory
        storage_context = StorageContext.from_defaults(persist_dir=VECTOR_DB_DIR)
        
        # Load the index from storage
        index = load_index_from_storage(storage_context=storage_context, embed_model=embed_model)
        
        # Create a query engine and store it globally
        RAG_QUERY_ENGINE = index.as_query_engine(similarity_top_k=3)
        print("RAG query engine is ready!")

    except Exception as e:
        print(f"FATAL ERROR: Could not load RAG model. Details: {e}")
        # In a real-world app, you might want to log this or notify an admin.
        RAG_QUERY_ENGINE = None

# ----------------------------------------------------
# Wrapper function to process and load RAG model sequentially
# ----------------------------------------------------
async def _process_and_load_rag(repo_dir: str, file_paths_to_chunk: list[str], vector_db_dir: str):
    """
    Sequentially runs smart_chunking and then loads the RAG model.
    """
    print(f"DEBUG: Starting smart chunking process for directory: {repo_dir}")
    print(f"DEBUG: Vector DB directory is: {vector_db_dir}")

    # Ensure the vector DB directory exists
    os.makedirs(vector_db_dir, exist_ok=True)
    
    # First, run the smart chunking process
    smart_chunking(repo_dir, file_paths_to_chunk, vector_db_dir)
    
    print("DEBUG: Smart chunking process completed. Checking for FAISS index file...")
    faiss_index_path = os.path.join(vector_db_dir, "faiss_index.bin")
    if os.path.exists(faiss_index_path):
        print(f"DEBUG: FAISS index file found at {faiss_index_path}. Proceeding to load model.")
    else:
        print(f"ERROR: FAISS index file not found at {faiss_index_path} after smart chunking. The smart chunking function may have failed.")
    
    # Then, load the RAG model into memory
    await _load_rag_model()


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

    # Start the new wrapper function as a background task
    # This will run smart_chunking and then load the RAG model sequentially
    background_tasks.add_task(_process_and_load_rag, repo_dir, file_paths_to_chunk, VECTOR_DB_DIR)

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

@app.get("/api/check-rag-ready")
def check_rag_ready():
    """
    Checks if the FAISS vector database directory exists and is ready for use.
    """
    # The RAG query engine is ready if it's not None
    is_ready = RAG_QUERY_ENGINE is not None
    return {"isReady": is_ready}


@app.post("/api/chat")
async def chat_with_rag(request_body: QueryRequest):
    """
    Receives a user query and uses the RAG model to generate a response.
    """
    global RAG_QUERY_ENGINE

    user_query = request_body.query.strip()

    if not user_query:
        raise HTTPException(
            status_code=400,
            detail={"message": "Missing 'query' in request body", "err": True}
        )

    # Check if the RAG query engine is ready and loaded in memory
    if RAG_QUERY_ENGINE is None:
        raise HTTPException(
            status_code=400,
            detail={"message": "RAG model not ready. Please select a workspace and wait for processing.", "err": True}
        )

    try:
        # Query the RAG model using the pre-loaded engine
        response = RAG_QUERY_ENGINE.query(user_query)
        
        return {
            "message": "Query processed successfully",
            "response": str(response),
            "err": False
        }

    except Exception as e:
        print(f"Error during RAG chat: {e}")
        raise HTTPException(
            status_code=500,
            detail={"message": f"An error occurred during chat processing: {e}", "err": True}
        )


# A simple example route to test that the API is working
@app.get("/")
def read_root():
    """A simple root endpoint to show the API is running."""
    return {"message": "Hello from the RepoFlow API!"}
