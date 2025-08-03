# gemini_client.py

import os
import json
import google.generativeai as genai

# Configure the Gemini API key.
try:
    genai.configure(api_key="AIzaSyDAkKSlkPXRva8ywSZKOUt0zpxReHKTweo")
except KeyError:
    print("FATAL ERROR: 'GOOGLE_API_KEY' environment variable not set.")
    print("Please set it before running the script.")
    pass

# Initialize the Gemini model globally
model = genai.GenerativeModel('gemini-2.5-flash')

# Define the prompt as a constant within this file.
STAGE1_PROMPT = """
-You are an expert software architect. I will provide you with two pieces of information:
    1. The README file of a code repository.
    2. The file structure (tree view) of the entire project.

-Your job is to analyze this project and break it down into logical workspaces — each workspace represents an isolated or semi-isolated part of the codebase that a developer or user might want to explore, modify, or interact with separately. Workspaces can represent frontend, backend, auth systems, dashboards, admin panels, APIs, database layers, etc., but I am not giving you any categories — you must decide yourself based on the README and file structure.

Use the file names, folder naming conventions, and README content to infer purpose.
You may make assumptions if the project lacks clarity, but clearly list them in a assumptions field for each workspace.

Each workspace should contain:

A name: A short title to be used as a button label.

A description: A 1–2 sentence summary for users to understand what this part does.

The list of files associated with this workspace. **This list MUST ONLY contain file paths and NOT directory paths.**

A returnPrompt: A single-sentence identifier that can be used to pass back what workspace the user clicked.

Any assumptions you made about this workspace’s purpose or boundaries.

🛑 Limit the number of workspaces to a minimum of 2 and a maximum of 30. Try to manage workspaces smartly, having more workspaces but where each one is more focused to the core of the workspace is important. Keeping fewer files in the workspace makes the later process more efficient, so it's recommended to have specific workspaces but not so specific that they become useless. Try to hit that under 12 file mark for each workspace if you can't, you can go slightly up.
📦 Output must be a strict JSON array with no extra explanation outside the JSON.
Each object in the array must follow this structure:

{
  "name": "string",
  "description": "string",
  "fileStructure": ["path/file1", "folder/file2", ...],
  "returnPrompt": "string",
  "assumptions": "string"
}
Only return valid JSON. No markdown, no prose, no commentary — just the array.
"""


def stageOne(treeStructurePath: str, workspaceFilePath: str) -> str:
    """
    Generates content using an LLM by combining a prompt with the content of a
    tree structure/README file and stores the response as a JSON file.

    Args:
        treeStructurePath: The path to the file containing the
                           combined tree structure and README text.
        workspaceFilePath: The path where the output JSON file will be saved.

    Returns:
        A success message indicating the response has been saved.
    
    Raises:
        FileNotFoundError: If the treeStructurePath does not exist.
        IOError: If there's an issue reading/writing the file.
        Exception: For other errors during content generation.
    """
    separator = "#" * 50

    try:
        # Construct the full, absolute path to the tree structure file
        file_path = os.path.abspath(treeStructurePath)
        
        # Read the content of the file using the absolute path
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()

    except FileNotFoundError:
        print(f"Error: Tree structure file not found at {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
    except IOError as e:
        print(f"Error reading tree structure file {file_path}: {e}")
        raise IOError(f"Error reading file: {e}")
    
    llm1_input = f"""
        {STAGE1_PROMPT} 
        {separator}
        {file_content}
        {separator}
    """
    try:
        # Request a structured JSON response from the model
        response = model.generate_content(
            llm1_input.strip(),
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Extract the JSON text from the response
        json_output = response.text

        # Write the JSON output to the file using the provided path
        with open(workspaceFilePath, "w", encoding="utf-8") as json_file:
            # We use json.loads and json.dump to re-format it nicely
            parsed_json = json.loads(json_output)
            json.dump(parsed_json, json_file, indent=2)
        
        print(f"\nLLM Analysis Result saved to {workspaceFilePath}")
        return f"LLM analysis completed. The response has been saved to {workspaceFilePath}."
        
    except Exception as e:
        print(f"Error generating content or saving file: {e}")
        return f"LLM content generation failed: {e}"
