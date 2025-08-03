# main.py

import os
import json
import time
import shutil
import atexit
from llama_index.llms.gemini import Gemini
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import the necessary functions from the separate files
from repoProcessor import process_repository
from gemini import stageOne
from smartChunking import smart_chunking

# Import LlamaIndex components for RAG
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage, Settings
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.gemini import Gemini

# Configure the Gemini API key for the RAG query engine
API_KEY = "AIzaSyDAkKSlkPXRva8ywSZKOUt0zpxReHKTweo"

# Initialize the FastAPI application
app = FastAPI(
    title="RepoFlow Backend",
    description="Backend API for the RepoFlow project."
)

# Define the allowed origins for CORS.
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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPOS_DIR = os.path.join(BASE_DIR, "cloned_repos")
os.makedirs(REPOS_DIR, exist_ok=True)

# Cleanup function to remove repositories when app shuts down
def cleanup_repos():
    if os.path.exists(REPOS_DIR):
        shutil.rmtree(REPOS_DIR, ignore_errors=True)
    vector_db_dir = os.path.join(BASE_DIR, "vector_db_chunks")
    if os.path.exists(vector_db_dir):
        shutil.rmtree(vector_db_dir, ignore_errors=True)
    workspace_file = os.path.join(BASE_DIR, "workspace.json")
    if os.path.exists(workspace_file):
        os.remove(workspace_file)
    tree_file = os.path.join(BASE_DIR, "tree_structure.txt")
    if os.path.exists(tree_file):
        os.remove(tree_file)

# Register cleanup function to run on exit
atexit.register(cleanup_repos)

# Global variables
LATEST_REPO_PATH = None
VECTOR_DB_DIR = os.path.join(BASE_DIR, "vector_db_chunks")
RAG_QUERY_ENGINE = None

# Pydantic models for request bodies
class RepoUrlRequest(BaseModel):
    repoUrl: str

class WorkspaceRequest(BaseModel):
    name: str
    description: str
    fileStructure: list[str]
    returnPrompt: str
    assumptions: str

class QueryRequest(BaseModel):
    query: str

async def _load_rag_model():
    """
    Background task to load the RAG model and store it in a global variable.
    """
    global RAG_QUERY_ENGINE
    
    docstore_path = os.path.join(VECTOR_DB_DIR, "docstore.json")

    # Check if required files exist
    if not os.path.exists(docstore_path):
        print(f"ERROR: docstore.json is missing at {docstore_path}")
        return

    try:
        print("Loading RAG model into memory...")
        
        # Initialize the embedding model and LLM
        embed_model = GeminiEmbedding(api_key=API_KEY)
        llm = Gemini(api_key=API_KEY)
        
        # Set them as defaults in Settings
        Settings.embed_model = embed_model
        Settings.llm = llm
        
        # Check for FAISS index file with correct extension (.bin)
        faiss_index_file = os.path.join(VECTOR_DB_DIR, "faiss_index.bin")  # Changed from .faiss to .bin
        if os.path.exists(faiss_index_file):
            print(f"Loading existing FAISS index from: {faiss_index_file}")
            loaded_faiss_index = faiss.read_index(faiss_index_file)
            vector_store = FaissVectorStore(faiss_index=loaded_faiss_index)
        else:
            print("FAISS index file not found, creating new one...")
            faiss_index = faiss.IndexFlatL2(768)
            vector_store = FaissVectorStore(faiss_index=faiss_index)

        # Create a storage context
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store,
            persist_dir=VECTOR_DB_DIR
        )
        
        # Load the index from storage
        print("Loading index from storage...")
        index = load_index_from_storage(storage_context=storage_context)
        
        # Create a query engine with better error handling
        print("Creating query engine...")
        RAG_QUERY_ENGINE = index.as_query_engine(
            similarity_top_k=3,
            llm=llm,
            response_mode="compact"  # Add response mode for better handling
        )
        print("RAG query engine is ready!")

    except Exception as e:
        print(f"FATAL ERROR: Could not load RAG model. Details: {e}")
        import traceback
        traceback.print_exc()
        RAG_QUERY_ENGINE = None



# Wrapper function to process and load RAG model sequentially
async def _process_and_load_rag(repo_dir: str, file_paths_to_chunk: list[str], vector_db_dir: str):
    """
    Sequentially runs smart_chunking and then loads the RAG model.
    """
    try:
        print(f"DEBUG: Starting smart chunking process for directory: {repo_dir}")
        print(f"DEBUG: Vector DB directory is: {vector_db_dir}")

        # Ensure the vector DB directory exists
        os.makedirs(vector_db_dir, exist_ok=True)
        
        # First, run the smart chunking process
        print("DEBUG: Calling smart_chunking function...")
        smart_chunking(repo_dir, file_paths_to_chunk, vector_db_dir)
        
        print("DEBUG: Smart chunking process completed. Checking for required files...")
        docstore_path = os.path.join(vector_db_dir, "docstore.json")
        if os.path.exists(docstore_path):
            print(f"DEBUG: Essential files found. Proceeding to load model.")
            # Then, load the RAG model into memory
            print("DEBUG: Loading RAG model...")
            await _load_rag_model()
            print("DEBUG: RAG processing pipeline completed successfully!")
        else:
            print(f"ERROR: Essential files not found after smart chunking. The smart chunking function may have failed.")
            return
        
    except Exception as e:
        print(f"FATAL ERROR in _process_and_load_rag: {e}")
        import traceback
        traceback.print_exc()

@app.post("/api/receive-repo")
async def receive_repo(request_body: RepoUrlRequest, background_tasks: BackgroundTasks):
    """
    Receives a GitHub repository URL, clones it, and processes its contents.
    """
    global LATEST_REPO_PATH, RAG_QUERY_ENGINE
    repo_url = request_body.repoUrl.strip()

    if not repo_url:
        raise HTTPException(
            status_code=400,
            detail={"message": "Missing 'repoUrl' in request body", "err": True}
        )
    
    # Clean up old data before processing new repository
    print("Cleaning up old data...")
    
    # Clear the RAG query engine from memory
    RAG_QUERY_ENGINE = None
    
    # Remove old vector database
    if os.path.exists(VECTOR_DB_DIR):
        shutil.rmtree(VECTOR_DB_DIR)
        print(f"Cleared old vector database: {VECTOR_DB_DIR}")
    
    # Remove old workspace file
    workspace_file_path = os.path.join(BASE_DIR, "workspace.json")
    if os.path.exists(workspace_file_path):
        os.remove(workspace_file_path)
        print(f"Removed old workspace file: {workspace_file_path}")
    
    # Remove old tree structure file
    tree_file_path = os.path.join(BASE_DIR, "tree_structure.txt")
    if os.path.exists(tree_file_path):
        os.remove(tree_file_path)
        print(f"Removed old tree structure file: {tree_file_path}")
    
    print("Cleanup complete. Processing new repository...")
    
    # Call the function from the separate file to handle all the processing
    result = process_repository(repo_url)
    
    # Store the correct repo path in the global variable for later use
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
    
    repo_dir = LATEST_REPO_PATH
    file_paths_to_chunk = workspace_data.fileStructure
    
    print(f"Selected repo directory for chunking: {repo_dir}")
    print(f"Workspace name: {workspace_data.name}")
    print(f"Files to chunk: {file_paths_to_chunk}")
    
    # Check if the repository directory exists
    if not os.path.exists(repo_dir):
        print(f"ERROR: Repository directory does not exist: {repo_dir}")
        raise HTTPException(
            status_code=400,
            detail={"message": f"Repository directory not found: {repo_dir}", "err": True}
        )
    
    # Validate that files exist
    valid_files = []
    invalid_files = []
    for file_path in file_paths_to_chunk:
        full_path = os.path.join(repo_dir, file_path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            valid_files.append(file_path)
        else:
            invalid_files.append(file_path)
            print(f"WARNING: File not found: {full_path}")
    
    if not valid_files:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "No valid files found in the workspace. All specified files are missing.",
                "invalid_files": invalid_files,
                "err": True
            }
        )
    
    print(f"Valid files to process: {valid_files}")
    
    # Start the processing as a background task with only valid files
    background_tasks.add_task(_process_and_load_rag, repo_dir, valid_files, VECTOR_DB_DIR)

    return {
        "message": "Workspace received successfully. Smart chunking process has been initiated in the background!",
        "workspace_data": workspace_data,
        "valid_files": valid_files,
        "invalid_files": invalid_files,
        "err": False
    }

@app.get("/api/check-workspaces")
def check_workspaces():
    """
    Checks if the workspace.json file exists and is ready for use.
    """
    workspace_file_path = os.path.join(BASE_DIR, "workspace.json")
    is_ready = os.path.exists(workspace_file_path)

    if is_ready:
        is_ready = os.path.getsize(workspace_file_path) > 0
    
    return {"isReady": is_ready}

@app.get("/api/check-rag-ready")
def check_rag_ready():
    """
    Checks if the vector database files exist and the RAG query engine is ready.
    """
    # Check if the required files exist
    docstore_path = os.path.join(VECTOR_DB_DIR, "docstore.json")
    faiss_index_file = os.path.join(VECTOR_DB_DIR, "faiss_index.faiss")
    
    # At minimum we need docstore.json to exist
    essential_files_exist = os.path.exists(docstore_path)
    
    # The RAG query engine is ready if it's not None AND essential files exist
    is_ready = RAG_QUERY_ENGINE is not None and essential_files_exist
    
    return {
        "isReady": is_ready,
        "essentialFilesExist": essential_files_exist,
        "queryEngineLoaded": RAG_QUERY_ENGINE is not None,
        "docstoreExists": os.path.exists(docstore_path),
        "faissIndexExists": os.path.exists(faiss_index_file)
    }

@app.get("/api/check-rag-ready")
def check_rag_ready():
    """
    Checks if the vector database files exist and the RAG query engine is ready.
    """
    # Check if the required files exist
    docstore_path = os.path.join(VECTOR_DB_DIR, "docstore.json")
    faiss_index_file = os.path.join(VECTOR_DB_DIR, "faiss_index.bin")  # Changed from .faiss to .bin
    
    # At minimum we need docstore.json to exist
    essential_files_exist = os.path.exists(docstore_path)
    
    # The RAG query engine is ready if it's not None AND essential files exist
    is_ready = RAG_QUERY_ENGINE is not None and essential_files_exist
    
    return {
        "isReady": is_ready,
        "essentialFilesExist": essential_files_exist,
        "queryEngineLoaded": RAG_QUERY_ENGINE is not None,
        "docstoreExists": os.path.exists(docstore_path),
        "faissIndexExists": os.path.exists(faiss_index_file)
    }


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
        print(f"Processing query: {user_query}")
        
        # Query the RAG model using the pre-loaded engine
        response = RAG_QUERY_ENGINE.query(user_query)
        
        print(f"RAG response generated successfully: {str(response)[:100]}...")  # Log first 100 chars
        
        return {
            "message": "Query processed successfully",
            "response": str(response),
            "err": False
        }

    except Exception as e:
        print(f"Error during RAG chat: {str(e)}")
        import traceback
        traceback.print_exc()  # This will show the full error stack
        
        raise HTTPException(
            status_code=500,
            detail={"message": f"An error occurred during chat processing: {str(e)}", "err": True}
        )



@app.get("/api/debug-rag")
def debug_rag():
    """
    Debug endpoint to check RAG system status in detail.
    """
    global RAG_QUERY_ENGINE
    
    debug_info = {
        "query_engine_status": "loaded" if RAG_QUERY_ENGINE is not None else "not_loaded",
        "vector_db_dir": VECTOR_DB_DIR,
        "vector_db_exists": os.path.exists(VECTOR_DB_DIR),
        "files_in_vector_db": [],
        "api_key_set": bool(API_KEY),
        "latest_repo_path": LATEST_REPO_PATH
    }
    
    # List files in vector DB directory
    if os.path.exists(VECTOR_DB_DIR):
        debug_info["files_in_vector_db"] = os.listdir(VECTOR_DB_DIR)
    
    # Check specific files
    required_files = ["docstore.json", "index_store.json", "faiss_index.bin"]
    for file in required_files:
        file_path = os.path.join(VECTOR_DB_DIR, file)
        debug_info[f"{file}_exists"] = os.path.exists(file_path)
        if os.path.exists(file_path):
            debug_info[f"{file}_size"] = os.path.getsize(file_path)
    
    # Test a simple query if engine is loaded
    if RAG_QUERY_ENGINE is not None:
        try:
            test_response = RAG_QUERY_ENGINE.query("Hello")
            debug_info["test_query_success"] = True
            debug_info["test_response"] = str(test_response)[:200]
        except Exception as e:
            debug_info["test_query_success"] = False
            debug_info["test_query_error"] = str(e)
    
    return debug_info


@app.get("/")
def read_root():
    """A simple root endpoint to show the API is running."""
    return {"message": "Hello from the RepoFlow API!"}