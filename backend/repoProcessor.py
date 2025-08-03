# repo_processor.py

import os
import subprocess
import uuid
import glob
import shutil

from fastapi import HTTPException

# Define a base directory for storing cloned repositories
# It's a good practice to use a dedicated directory for this.
REPOS_DIR = "./cloned_repos"
os.makedirs(REPOS_DIR, exist_ok=True)


def create_tree_structure(startpath: str, repo_name: str) -> str:
    """
    Generates a string representing the file and folder tree structure.

    Args:
        startpath: The path to the root directory to start the tree from.
        repo_name: The name of the repository (to be excluded from paths).

    Returns:
        A multiline string of the tree structure.
    """
    tree_lines = []
    tree_lines.append(f"Repository: {repo_name}")
    tree_lines.append("=" * 40)
    
    for root, dirs, files in os.walk(startpath):
        # Skip .git directory
        if '.git' in root:
            continue
            
        # Calculate relative path from the repository root
        rel_path = os.path.relpath(root, startpath)
        
        # Skip the root directory itself
        if rel_path == '.':
            rel_path = ''
            level = 0
        else:
            level = rel_path.count(os.sep) + 1
            
        # Add directory line
        if rel_path:
            indent = '|   ' * (level - 1)
            tree_lines.append(f'{indent}|-- {os.path.basename(root)}/')
            
        # Add files
        subindent = '|   ' * level
        for f in files:
            if rel_path:
                file_path = os.path.join(rel_path, f).replace('\\', '/')
            else:
                file_path = f
            tree_lines.append(f'{subindent}|-- {f}  (path: {file_path})')
            
    return '\n'.join(tree_lines)


def process_repository(repo_url: str):
    """
    Clones a Git repository, creates a file tree structure,
    finds the README, and saves the combined content to a file.

    Args:
        repo_url: The URL of the Git repository to clone.

    Returns:
        A dictionary containing the processing results.
        
    Raises:
        HTTPException: If an error occurs during cloning or processing.
    """
    # Extract a meaningful name from the repository URL and add a unique ID
    repo_name = os.path.basename(repo_url).removesuffix('.git')
    unique_id = str(uuid.uuid4())[:8] # Use a shorter unique ID for readability
    repo_dir_name = f"{repo_name}-{unique_id}"
    target_dir = os.path.join(REPOS_DIR, repo_dir_name)

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
            shutil.rmtree(target_dir)
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to clone repository", "error": e.stderr}
        )
    except FileNotFoundError:
        print("Error: 'git' command not found. Please ensure Git is installed and in your system's PATH.")
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        raise HTTPException(
            status_code=500,
            detail={"message": "Git command not found. Please install Git.", "err": True}
        )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        raise HTTPException(
            status_code=500,
            detail={"message": f"An unexpected error occurred: {e}", "err": True}
        )

    # After successful cloning, create the tree structure
    tree_structure = create_tree_structure(target_dir, repo_name)
    print("Generated tree structure")

    # Define the path for the tree structure file
    tree_file_path = os.path.join(os.path.dirname(__file__), "tree_structure.txt")

    # Read README.md content if available
    readme_content = ""
    readme_patterns = ["README.md", "readme.md", "README.txt", "readme.txt"]
    
    found_readme = False
    for pattern in readme_patterns:
        readme_path_candidates = glob.glob(os.path.join(target_dir, pattern))
        if readme_path_candidates:
            actual_readme_path = readme_path_candidates[0]
            try:
                with open(actual_readme_path, "r", encoding="utf-8") as f:
                    readme_content = f.read()
                print(f"Found and read {os.path.basename(actual_readme_path)}")
                found_readme = True
                break
            except Exception as e:
                print(f"Could not read README file at {actual_readme_path}: {e}")

    # Append the tree structure and then the README content to the file
    with open(tree_file_path, "w", encoding="utf-8") as f:
        f.write("IMPORTANT: When creating workspaces, use file paths relative to the repository root.\n")
        f.write("Do NOT include the repository folder name in the paths.\n")
        f.write("For example, use '01_hello/test.py' NOT 'tiny_python_projects-abc123/01_hello/test.py'\n\n")
        
        f.write("Repository Tree Structure:\n")
        f.write("--------------------------\n")
        f.write(tree_structure)
        
        if found_readme:
            f.write("\n\n")
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
        "tree_file": tree_file_path,
        "err": False
    }