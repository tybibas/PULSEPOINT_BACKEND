from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI(title="Sourcing Engine API")

# Allow CORS for local dashboard development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FTSE_FILE = "ftse_constituents.json"
QUEUE_FILE = "dashboard_queue.json"

@app.get("/")
def read_root():
    return {"status": "Sourcing Engine API is running"}

@app.get("/universe")
def get_universe():
    """
    Returns the full list of FTSE companies (The 'All' Pile).
    """
    if not os.path.exists(FTSE_FILE):
        return []
    try:
        with open(FTSE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/queue")
def get_queue():
    """
    Returns the list of triggered leads awaiting approval (The 'Triggered' Pile).
    """
    if not os.path.exists(QUEUE_FILE):
        return []
    try:
        with open(QUEUE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Run on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
