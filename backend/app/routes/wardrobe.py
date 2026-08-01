from fastapi import APIRouter, HTTPException
from bson import ObjectId
from bson.errors import InvalidId

from app.database.mongodb import wardrobe_collection
from app.database.models import WardrobeItemOut

router = APIRouter(prefix="/wardrobe", tags=["wardrobe"])

@router.get("/", response_model=list[WardrobeItemOut])
async def list_items():
    items = []
    async for doc in wardrobe_collection.find():
        items.append(WardrobeItemOut(
            id=str(doc["_id"]),
            image_path=doc["image_path"],
            category=doc.get("category"),
            color=doc.get("color"),
            uploaded_at=doc["uploaded_at"],
        ))
    return items

@router.get("/{item_id}", response_model=WardrobeItemOut)
async def get_item(item_id: str):
    try:
        object_id = ObjectId(item_id)
    except InvalidId:
        raise HTTPException(status_code=404, detail="Item not found") 
    doc = await wardrobe_collection.find_one({"_id": ObjectId(item_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Item not found")
    return WardrobeItemOut(
        id=str(doc["_id"]),
        image_path=doc["image_path"],
        category=doc.get("category"),
        color=doc.get("color"),
        uploaded_at=doc["uploaded_at"],
    )