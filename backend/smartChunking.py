# smartChunking.py

import os
import json
import google.generativeai as genai
import time
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss
from llama_index.embeddings.gemini import GeminiEmbedding

# Configure the Gemini API key.
# This assumes the API key is also available in this script's context.
API_KEY = "AIzaSyDAkKSlkPXRva8ywSZKOUt0zpxReHKTweo"
try:
    genai.configure(api_key=API_KEY)
except KeyError:
    print("FATAL ERROR: 'GOOGLE_API_KEY' environment variable not set.")
    print("Please set it before running the script.")
    pass

# Initialize the Gemini model globally
CHUNK_MODEL = genai.GenerativeModel('gemini-2.5-flash-lite')

# Define the prompt for the LLM to perform smart chunking
SMART_CHUNKING_PROMPT = """
You are an AI assistant tasked with preparing code for vector-based retrieval. I will give you the contents of a source code file. Your job is to:

Divide the code into meaningful chunks. A chunk should ideally represent a logical unit like a class, function, component, or configuration block. If the file is large or complex, break it down further as necessary.
For each chunk, return the following information in strict JSON format. No text outside the JSON block. Use this schema:
{
  "file": "<full relative file path>",
  "chunk": <chunk_number_starting_from_1>,
  "name": "<function/class/component/section name, or 'misc' if unknown>",
  "description": "<highly detailed description of what this chunk does and how it fits into the project. Use technical language, and include use cases or data flow if applicable.>",
  "code": "<exact code snippet with no modifications>",
  "keywords": ["<relevant>", "<terms>", "<from>", "<code>", "<or>", "<domain>"]}
Your output must only be JSON — one JSON object per chunk. No prose, markdown, or explanations outside the JSON.
Ensure that:
The "description" is deeply informative (e.g. how it's used, what modules it depends on).
The "keywords" help with semantic search.
The "code" block is unchanged and formatted exactly as-is.
If the file includes unrelated elements, group them under "name": "misc" but still describe them properly.
Avoid redundancy across chunks.
Assume this data will be stored in a vector DB and used later for retrieval-based reasoning by another LLM, which will ask questions to understand or extend the code.
"""

def smart_chunking(repo_path: str, file_paths: list[str], vector_db_dir: str):
    """
    Chunks code files using an LLM and stores them in a FAISS vector database.
    Includes a fallback for files that cannot be processed by the LLM.

    Args:
        repo_path: The absolute path to the cloned repository.
        file_paths: A list of file paths (relative to the repo root) to chunk.
        vector_db_dir: The absolute path to the directory where the vector database will be saved.
    """
    print("Starting smart code chunking process...")
    all_documents = []

    # Ensure the directory for the vector database exists
    os.makedirs(vector_db_dir, exist_ok=True)
    print(f"Vector database will be saved to: {vector_db_dir}")

    # Initialize FAISS and the vector store
    # The default Gemini embedding model has a dimension of 768.
    d = 768
    faiss_index = faiss.IndexFlatL2(d)
    vector_store = FaissVectorStore(faiss_index=faiss_index)

    # Initialize a fallback simple node parser
    fallback_parser = SimpleNodeParser.from_defaults(chunk_size=1024, chunk_overlap=20)

    for i, file_path in enumerate(file_paths):
        print(f"[{i+1}/{len(file_paths)}] Processing file: {file_path}")

        # Extract the base name of the repository from repo_path
        repo_name = os.path.basename(repo_path)

        # CORRECTED: Normalize the file_path if it contains a duplicate repo_name
        corrected_file_path = file_path
        if file_path.startswith(repo_name + os.sep):
            corrected_file_path = file_path[len(repo_name + os.sep):]
            print(f"DEBUG: Corrected file path from '{file_path}' to '{corrected_file_path}'")

        full_path = os.path.join(repo_path, corrected_file_path)

        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            print(f"Warning: File not found or is a directory, skipping: {full_path}")
            print(f"DEBUG: repo_path: {repo_path}")
            print(f"DEBUG: original file_path from workspace: {file_path}")
            print(f"DEBUG: attempted full_path: {full_path}")
            continue

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            llm_input = f"{SMART_CHUNKING_PROMPT}\n\nFile Path: {corrected_file_path}\n\nCode:\n{file_content}" # Use corrected path for LLM prompt
            
            chunks = []
            max_retries = 3
            retries = 0
            response = None
            
            while retries < max_retries:
                try:
                    # Attempt to use the LLM for smart chunking
                    print(f"Attempting LLM call for {corrected_file_path} (Attempt {retries + 1}/{max_retries})...")
                    response = CHUNK_MODEL.generate_content(
                        llm_input.strip(),
                        generation_config={"response_mime_type": "application/json"}
                    )
                    # If successful, break the retry loop
                    break
                except Exception as e:
                    print(f"LLM generation failed for {corrected_file_path} on attempt {retries + 1}: {e}")
                    retries += 1
                    if retries < max_retries:
                        print("Waiting for 10 seconds before retrying...")
                        time.sleep(10)
                    else:
                        print(f"Max retries ({max_retries}) exceeded for {corrected_file_path}. Falling back to simple chunking.")
                        break

            if response and response.text.strip():
                try:
                    json_output = response.text
                    chunks = json.loads(json_output)
                    print(f"Successfully smart-chunked file: {corrected_file_path}")
                except json.JSONDecodeError as e:
                    print(f"JSONDecodeError: LLM output for {corrected_file_path} is not valid JSON: {e}")
                    print("Falling back to simple chunking...")
                except Exception as e:
                    print(f"An unexpected error occurred during JSON parsing: {e}")
                    print("Falling back to simple chunking...")
            else:
                print(f"Warning: LLM returned an empty response for {corrected_file_path} after all retries. Falling back to simple chunking.")

            if not chunks:
                # Fallback to simple chunking if LLM-based chunking fails
                documents = fallback_parser.get_nodes_from_documents([Document(text=file_content, metadata={"file": corrected_file_path, "source": "fallback"})])
                for doc in documents:
                    all_documents.append(doc)
                print(f"Successfully performed simple chunking on {corrected_file_path}")
            else:
                # Handle cases where the LLM returns a single object instead of a list
                if isinstance(chunks, dict):
                    chunks = [chunks]

                # Process the chunks from the LLM
                for chunk in chunks:
                    doc = Document(
                        text=chunk['code'],
                        metadata={
                            "file": chunk.get('file', corrected_file_path), # Use corrected path in metadata
                            "chunk": chunk.get('chunk', 1),
                            "name": chunk.get('name', 'misc'),
                            "description": chunk.get('description', 'No description provided by LLM.'),
                            "keywords": chunk.get('keywords', []),
                            "source": "llm"
                        }
                    )
                    all_documents.append(doc)

        except Exception as e:
            print(f"An unexpected error occurred while processing file {corrected_file_path}: {e}")
            continue

    print("Finished processing all specified files.")

    if all_documents:
        # Create a Gemini embedding model and pass the API key
        embed_model = GeminiEmbedding(api_key=API_KEY)

        # Initialize the StorageContext with the vector_store and persist_dir
        storage_context = StorageContext.from_defaults(vector_store=vector_store, persist_dir=vector_db_dir)

        # Create the index using the storage context and documents
        index = VectorStoreIndex.from_documents(
            all_documents,
            storage_context=storage_context,
            embed_model=embed_model
        )

        # The persist() method now knows where to save all the files
        index.storage_context.persist()
        
        print(f"Vector database created and saved to {vector_db_dir}")
        faiss_index_path = os.path.join(vector_db_dir, "faiss_index.bin")
        if os.path.exists(faiss_index_path):
            print(f"SUCCESS: Confirmed that faiss_index.bin exists at {faiss_index_path}")
        else:
            print(f"FAILURE: faiss_index.bin does not exist at {faiss_index_path}")

    else:
        print("No documents were processed. Vector database not created.")