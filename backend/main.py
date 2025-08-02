from typing import Union
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


@app.get("/api/recieve-repo")
def read_root(url: str = None):
    # Expecting a query parameter 'url'
    if not url:
        return JSONResponse(status_code=400, content={"message": "Missing 'url' query parameter", "error": False})
    # Here you can process the URL as needed
    return {"received_url": url}