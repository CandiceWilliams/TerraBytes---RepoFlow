# smartChunking.py

import os
import json
import google.generativeai as genai
import time
from llama_index.core import Document, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss
from llama_index.embeddings.gemini import GeminiEmbedding

# Configure the Gemini API key.
API_KEY = "AIzaSyDAkKSlkPXRva8ywSZKOUt0zpxReHKTweo"
try:
    genai.configure(api_key=API_KEY)
except KeyError:
    print("FATAL ERROR: 'GOOGLE_API_KEY' environment variable not set.")
    print("Please set it before running the script.")
    pass

# Initialize the Gemini model globally
CHUNK_MODEL = genai.GenerativeModel('gemini-2.5-flash-lite')

# Prompt for the LLM
SMART_CHUNKING_PROMPT = """
You are an AI assistant tasked with preparing code for vector-based retrieval. I will give you the contents of a source code file. Your job is to:

Divide the code into meaningful chunks. A chunk should ideally represent a logical unit like a class, function, component, or configuration block. If the file is large or complex, break it down further as necessary.
For each chunk, return the following information in strict JSON format. No text outside the JSON block. Use this schema:
{
  "file": "<full relative file path>",
  "chunk": <chunk_number_starting_from_1>,
  "name": "<function/class/component/section name, or 'misc' if unknown>",
  "description": "<detailed description of what this chunk does and how it fits into the project.>",
  "code": "<exact code snippet>",
  "keywords": ["<keyword1>", "<keyword2>"]
}
Your output must only be JSON — one object per chunk. No prose or markdown.
"""


def smart_chunking(repo_path: str, file_paths: list[str], vector_db_dir: str):
    """
    Chunks code files using an LLM and stores them in a FAISS vector database.
    """
    print("Starting smart code chunking process.")
    print(f"Repository path: {repo_path}")
    print(f"Files to process: {file_paths}")
    
    all_documents = []

    # Ensure vector DB directory
    os.makedirs(vector_db_dir, exist_ok=True)
    print(f"Vector database will be saved to: {vector_db_dir}")

    # Initialize FAISS vector store
    dimension = 768
    faiss_index = faiss.IndexFlatL2(dimension)
    vector_store = FaissVectorStore(faiss_index=faiss_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Fallback parser
    fallback_parser = SimpleNodeParser.from_defaults(chunk_size=1024, chunk_overlap=20)

    for idx, file_path in enumerate(file_paths, start=1):
        print(f"[{idx}/{len(file_paths)}] Processing file: {file_path}")

        # Build the full path - file_path is already relative to the repo
        full_path = os.path.join(repo_path, file_path)
        full_path = os.path.normpath(full_path)
        
        print(f"  Full path: {full_path}")
        print(f"  File exists: {os.path.exists(full_path)}")
        print(f"  Is file: {os.path.isfile(full_path)}")

        # Skip invalid files
        if not os.path.exists(full_path):
            print(f"  Warning: File does not exist, skipping: {full_path}")
            continue
            
        if not os.path.isfile(full_path):
            print(f"  Warning: Path is not a file (might be directory), skipping: {full_path}")
            continue

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"  Successfully read file: {len(content)} characters")

            # Use the original file_path for the LLM and document metadata
            llm_input = f"{SMART_CHUNKING_PROMPT}\n\nFile Path: {file_path}\n\nCode:\n{content}"
            
            response = None
            for attempt in range(1, 4):
                try:
                    print(f"  Attempting LLM call for {file_path} (Attempt {attempt}/3)")
                    response = CHUNK_MODEL.generate_content(
                        llm_input.strip(),
                        generation_config={"response_mime_type": "application/json"}
                    )
                    print(f"  LLM call successful")
                    break
                except Exception as e:
                    print(f"  LLM call failed (Attempt {attempt}): {e}")
                    time.sleep(5)
            
            if response is None:
                # Fallback parser
                print(f"  Using fallback parser for {file_path}.")
                nodes = fallback_parser.get_nodes_from_documents(
                    [Document(text=content, doc_id=file_path)]
                )
                for c, node in enumerate(nodes, start=1):
                    all_documents.append(Document(
                        text=node.get_content(),
                        doc_id=f"{file_path}#misc-{c}",
                        extra_info={"name": "misc", "chunk": c, "file": file_path}
                    ))
                continue

            # Parse JSON and build docs
            try:
                # Clean up the response text - remove markdown code blocks if present
                cleaned_text = response.text.strip()
                if cleaned_text.startswith('```json'):
                    cleaned_text = cleaned_text[7:]  # Remove ```json
                if cleaned_text.startswith('```'):
                    cleaned_text = cleaned_text[3:]  # Remove ```
                if cleaned_text.endswith('```'):
                    cleaned_text = cleaned_text[:-3]  # Remove trailing ```
                cleaned_text = cleaned_text.strip()
                
                # Try to parse as JSON array first, then as single object
                try:
                    chunks = json.loads(cleaned_text)
                except json.JSONDecodeError:
                    # Maybe it's multiple JSON objects on separate lines
                    chunks = []
                    for line in cleaned_text.split('\n'):
                        line = line.strip()
                        if line and line.startswith('{'):
                            try:
                                chunks.append(json.loads(line))
                            except:
                                pass
                
                if not isinstance(chunks, list):
                    chunks = [chunks]  # Wrap single object in list
                    
                print(f"  Created {len(chunks)} chunks from LLM response")
                
                for chunk in chunks:
                    doc = Document(
                        text=chunk['code'],
                        doc_id=f"{file_path}#chunk-{chunk['chunk']}",
                        extra_info={
                            "file": file_path,
                            "name": chunk.get('name', 'misc'),
                            "description": chunk.get('description', ''),
                            "keywords": chunk.get('keywords', [])
                        }
                    )
                    all_documents.append(doc)
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"  Error parsing LLM response as JSON: {e}")
                print(f"  Response text: {response.text[:200]}...")
                # Fall back to simple parsing
                nodes = fallback_parser.get_nodes_from_documents(
                    [Document(text=content, doc_id=file_path)]
                )
                for c, node in enumerate(nodes, start=1):
                    all_documents.append(Document(
                        text=node.get_content(),
                        doc_id=f"{file_path}#misc-{c}",
                        extra_info={"name": "misc", "chunk": c, "file": file_path}
                    ))

        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
            import traceback
            traceback.print_exc()

    # Persist index if documents exist
    if all_documents:
        print(f"\nIndexing {len(all_documents)} documents...")
        try:
            index = VectorStoreIndex.from_documents(
                all_documents,
                storage_context=storage_context,
                embed_model=GeminiEmbedding(api_key=API_KEY)
            )
            print("Vector index created successfully")
            
            # Persist the storage context
            storage_context.persist(persist_dir=vector_db_dir)
            print(f"Vector database persisted to: {vector_db_dir}")
            
            # Verify the files were created
            faiss_path = os.path.join(vector_db_dir, "default__vector_store.json")
            if os.path.exists(faiss_path):
                print(f"  Vector store file created: {faiss_path}")
            
            # Also save the raw faiss index
            faiss_index_path = os.path.join(vector_db_dir, "faiss_index.bin")
            faiss.write_index(vector_store._faiss_index, faiss_index_path)
            print(f"  FAISS index saved to: {faiss_index_path}")
            
        except Exception as e:
            print(f"Error creating vector index: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\nNo documents were processed. Vector database not created.")
        # Create an empty FAISS index file to prevent errors
        faiss_index_path = os.path.join(vector_db_dir, "faiss_index.bin")
        empty_index = faiss.IndexFlatL2(768)
        faiss.write_index(empty_index, faiss_index_path)
        print(f"  Created empty FAISS index at: {faiss_index_path}")

    return