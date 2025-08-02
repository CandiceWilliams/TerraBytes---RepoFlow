# main.py

import os
import subprocess
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
# Define a function to create the tree structure
# ----------------------------------------------------
def create_tree_structure(startpath: str) -> str:
    """
    Generates a string representing the file and folder tree structure.
    
    Args:
        startpath: The path to the root directory to start the tree from.
        
    Returns:
        A multiline string of the tree structure.
    """
    tree_lines = []
    # os.walk will generate the file names in a directory tree
    for root, dirs, files in os.walk(startpath):
        # Calculate the level of the current directory in the tree
        level = root.replace(startpath, '').count(os.sep)
        # Use a prefix of a vertical line and spaces for indentation
        indent = '|   ' * level
        # Append the current directory's name to the list
        tree_lines.append(f'{indent}|-- {os.path.basename(root)}/')
        # Use another prefix for files to make them look nice
        subindent = '|   ' * (level + 1)
        # Append all the files in the current directory to the list
        for f in files:
            tree_lines.append(f'{subindent}|-- {f}')
    
    return '\n'.join(tree_lines)


# ----------------------------------------------------
# Define the Pydantic model and the API endpoint
# ----------------------------------------------------
class RepoUrlRequest(BaseModel):
    repoUrl: str

@app.post("/api/receive-repo")
async def receive_repo(request_body: RepoUrlRequest):
    # Access the URL using dot notation, e.g., request_body.repoUrl
    repo_url = request_body.repoUrl
    
    # Simple validation check for an empty URL.
    if not repo_url:
        raise HTTPException(
            status_code=400,
            detail={"message": "Missing 'repoUrl' in request body", "err": True}
        )

    # Generate a unique directory name for the cloned repository
    unique_dir_name = str(uuid.uuid4())
    target_dir = os.path.join(REPOS_DIR, unique_dir_name)
    
    # Clone the repository using subprocess
    try:
        print(f"Cloning {repo_url} into {target_dir}...")
        subprocess.run(
            ['git', 'clone', repo_url, target_dir],
            capture_output=True,
            text=True,
            check=True
        )
        print("Cloning successful!")
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        if os.path.exists(target_dir):
            os.rmdir(target_dir) # This will fail if not empty, which is fine
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to clone repository", "error": e.stderr}
        )

    # After successful cloning, create the tree structure
    tree_structure = create_tree_structure(target_dir)
    print("Generated tree structure:")
    print(tree_structure)

    # Return the tree structure and the repository path in the response
    return {
        "message": "Repository cloned and tree structure generated!", 
        "repo_path": target_dir,
        "tree_structure": tree_structure,
        "err": False
    }

# A simple example route to test that the API is working
@app.get("/")
def read_root():
    """A simple root endpoint to show the API is running."""
    return {"message": "Hello from the RepoFlow API!"}

# To run this file with uvicorn:
# uvicorn main:app --reload
