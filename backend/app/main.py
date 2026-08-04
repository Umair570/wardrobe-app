import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.routes import upload, wardrobe, chatbot, visualization, ingest, benchmark, profile
from app.database.mongodb import init_db_indexes

app = FastAPI(title="AI Wardrobe & Stylist Platform API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

os.makedirs("static/generated", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ML Output static directory handler
R_ML_OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml", "outputs"))
os.makedirs(R_ML_OUT, exist_ok=True)


@app.get("/ml/outputs/{filename:path}")
async def get_ml_output(filename: str):
    candidate = os.path.abspath(os.path.join(R_ML_OUT, filename))
    if not candidate.startswith(R_ML_OUT):
        raise HTTPException(status_code=400, detail="Invalid file path.")
    if os.path.isfile(candidate):
        return FileResponse(candidate)
    raise HTTPException(status_code=404, detail=f"No ML output found for '{filename}'.")


# Register API Routers (supporting both root and /api/v1 prefix)
for prefix in ["", "/api/v1"]:
    app.include_router(upload.router, prefix=prefix)
    app.include_router(wardrobe.router, prefix=prefix)
    app.include_router(chatbot.router, prefix=prefix)
    app.include_router(visualization.router, prefix=prefix)
    app.include_router(ingest.router, prefix=prefix)
    app.include_router(benchmark.router, prefix=prefix)
    app.include_router(profile.router, prefix=prefix)


@app.get("/health")
async def health():
    from app.services.vector.qdrant_service import qdrant_service
    return {
        "status":  "ok",
        "service": "AI Wardrobe & Stylist Platform API",
        "version": "1.0.0",
        "qdrant":  qdrant_service.collection_info(),
    }


@app.on_event("startup")
async def startup_event():
    print("[main] Starting AI Wardrobe Platform API...")
    # Phase 3: Initialise MongoDB indexes (idempotent)
    await init_db_indexes()
    print("[main] MongoDB indexes ready.")
    import app.ml_loader
    print("[main] ML Loader pre-warmed successfully.")