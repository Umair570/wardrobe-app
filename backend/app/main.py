import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routes import upload, wardrobe, chatbot, visualization
from app.database.mongodb import settings

app = FastAPI(title="Wardrobe App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Two possible locations for ML cutouts depending on which working directory
# the segmentation pipeline was run from. Rather than copying files between
# them once at startup (which misses anything written after boot -- that was
# the cause of broken thumbnails for recently-uploaded items), we check both
# live on every request. Whichever one actually has the file wins.
B_ML_OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml", "outputs"))
R_ML_OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml", "outputs"))
os.makedirs(B_ML_OUT, exist_ok=True)
os.makedirs(R_ML_OUT, exist_ok=True)


@app.get("/ml/outputs/{filename:path}")
async def get_ml_output(filename: str):
    for directory in (B_ML_OUT, R_ML_OUT):
        candidate = os.path.abspath(os.path.join(directory, filename))
        # Guard against path traversal escaping the intended directory.
        if not candidate.startswith(directory):
            continue
        if os.path.isfile(candidate):
            return FileResponse(candidate)
    raise HTTPException(status_code=404, detail=f"No ML output found for '{filename}'.")


app.include_router(upload.router)
app.include_router(wardrobe.router)
app.include_router(chatbot.router)
app.include_router(visualization.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
async def load_ml_models():
    print("Loading ML models (segmentation + classification)...")
    import app.ml_loader
    print("ML models loaded successfully.")