# main.py

import os
import subprocess
import uuid
import glob # Import glob for pattern matching README files

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
    # and strip any leading/trailing whitespace
    repo_url = request_body.repoUrl.strip()

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
            # Attempt to remove the directory if it was partially created
            # This is robust for non-empty directories as well
            try:
                os.rmdir(target_dir)
            except OSError: # Directory might not be empty, so use rmtree
                import shutil
                shutil.rmtree(target_dir)
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to clone repository", "error": e.stderr}
        )
    except FileNotFoundError:
        print("Error: 'git' command not found. Please ensure Git is installed and in your system's PATH.")
        if os.path.exists(target_dir):
            try:
                os.rmdir(target_dir)
            except OSError:
                import shutil
                shutil.rmtree(target_dir)
        raise HTTPException(
            status_code=500,
            detail={"message": "Git command not found. Please install Git.", "err": True}
        )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if os.path.exists(target_dir):
            try:
                os.rmdir(target_dir)
            except OSError:
                import shutil
                shutil.rmtree(target_dir)
        raise HTTPException(
            status_code=500,
            detail={"message": f"An unexpected error occurred: {e}", "err": True}
        )


    # After successful cloning, create the tree structure
    tree_structure = create_tree_structure(target_dir)
    print("Generated tree structure:")
    print(tree_structure)

    # Define the path for the tree structure file
    # Ensure this path is within the unique_dir_name to keep things organized
    # For now, let's keep it next to the cloned repo, as per your original code's intent
    # but consider placing it *inside* the target_dir for better organization.
    # For this example, I'll keep your original `tree_file_path` logic.
    tree_file_path = os.path.join(os.path.dirname(__file__), "tree_structure.txt")

    # Read README.md content if available
    readme_content = ""
    # Common README file names (case-insensitive)
    readme_patterns = ["README.md", "readme.md", "README.txt", "readme.txt"]
    
    found_readme = False
    for pattern in readme_patterns:
        # Use glob.glob to find the file case-insensitively on case-sensitive file systems
        # and specifically within the target_dir
        readme_path_candidates = glob.glob(os.path.join(target_dir, pattern))
        if readme_path_candidates:
            # Take the first match
            actual_readme_path = readme_path_candidates[0] 
            try:
                with open(actual_readme_path, "r", encoding="utf-8") as f:
                    readme_content = f.read()
                print(f"Found and read {os.path.basename(actual_readme_path)}")
                found_readme = True
                break # Stop after finding the first README
            except Exception as e:
                print(f"Could not read README file at {actual_readme_path}: {e}")
    
    # Append the tree structure and then the README content to the file
    with open(tree_file_path, "w", encoding="utf-8") as f:
        f.write("Repository Tree Structure:\n")
        f.write("--------------------------\n")
        f.write(tree_structure)
        
        if found_readme:
            f.write("\n\n") # Add some separation
            f.write("README.md Content:\n")
            f.write("------------------\n")
            f.write(readme_content)
        else:
            f.write("\n\n")
            f.write("No README.md or similar file found in the repository root.\n")


    return {
        "message": "Repository cloned and tree structure generated!",
        "repo_path": target_dir,
        "tree_structure": tree_structure,
        "tree_file": tree_file_path, # Path to the generated tree_structure.txt
        "err": False
    }

# A simple example route to test that the API is working
@app.get("/")
def read_root():
    """A simple root endpoint to show the API is running."""
    return {"message": "Hello from the RepoFlow API!"}