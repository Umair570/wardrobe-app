from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import upload, wardrobe, chatbot, visualization

app = FastAPI(title="Wardrobe App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(wardrobe.router)
app.include_router(chatbot.router)
app.include_router(visualization.router)

@app.get("/health")
async def health():
    return {"status": "ok"}