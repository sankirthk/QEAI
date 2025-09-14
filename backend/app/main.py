from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.routers import pipeline

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://192.168.137.1:3000",
    "https://192.168.137.1:3000",
    # add your phone's origin if needed
]

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API routes ---
app.include_router(pipeline.router, prefix="/api", tags=["pipeline"])

@app.get("/api/health")
def health():
    return {"status": "ok"}

# --- Static frontend (CRA build) ---
static_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../frontend/build")
)

if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=os.path.join(static_dir, "static")), name="static")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """
        Catch-all route for React Router.
        Always return index.html for unknown paths (except /api/*).
        """
        return FileResponse(os.path.join(static_dir, "index.html"))
else:
    print(f"[WARN] Frontend build directory not found: {static_dir}")
