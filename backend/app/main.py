import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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

# Locate ml/outputs directory (prefers backend/ml/outputs if populated, falls back to repo root ml/outputs)
b_ml_out = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml", "outputs"))
r_ml_out = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml", "outputs"))

if os.path.exists(b_ml_out) and os.listdir(b_ml_out):
    ml_outputs_dir = b_ml_out
elif os.path.exists(r_ml_out) and os.listdir(r_ml_out):
    ml_outputs_dir = r_ml_out
else:
    ml_outputs_dir = b_ml_out

os.makedirs(ml_outputs_dir, exist_ok=True)
app.mount("/ml/outputs", StaticFiles(directory=ml_outputs_dir), name="ml_outputs")




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