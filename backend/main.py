from typing import Union
from fastapi import FastAPI, HTTPException
from fastapi import Request
from fastapi.responses import JSONResponse

# from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel



app = FastAPI(
     title="RepoFlow Backend",
    description="Backend API for the RepoFlow project."
)

origins = [
    "http://localhost",  # Default for local development
    "http://localhost:3000",  # Common port for React dev servers
    "http://localhost:5173",  # Common port for Vite dev servers
    "*" # For a permissive development environment, allows all origins
]

# Add the CORS middleware to the application.
# This middleware must be added before any other middleware or routes.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

class RepoUrlRequest(BaseModel):
    repoUrl: str

# 2. Update the endpoint to use the Pydantic model.
# FastAPI will now automatically parse the JSON body and validate it
# against the RepoUrlRequest model.
@app.post("/api/receive-repo")
async def receive_repo(request_body: RepoUrlRequest):
    # Access the URL using dot notation, e.g., request_body.repoUrl
    repo_url = request_body.repoUrl
    
    # Simple validation check for an empty URL.
    if not repo_url:
        # It's better to use HTTPException for a more standard response.
        raise HTTPException(
            status_code=400,
            detail={"err": True}
        )
    
    # If the URL is valid, proceed with your logic.
    print(f"Received repo URL: {repo_url}")
    return {"err": False}