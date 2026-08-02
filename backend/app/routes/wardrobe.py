from fastapi import APIRouter, HTTPException
from bson import ObjectId
from bson.errors import InvalidId

from app.database.mongodb import wardrobe_collection
from app.database.models import WardrobeItemOut

router = APIRouter(prefix="/wardrobe", tags=["wardrobe"])

def _doc_to_out(doc) -> WardrobeItemOut:
    return WardrobeItemOut(
        id=str(doc["_id"]),
        source_image=doc["source_image"],
        segmentation_path=doc["segmentation_path"],
        area_ratio=doc.get("area_ratio"),
        category=doc.get("category"),
        type=doc.get("type"),
        style=doc.get("style"),
        season=doc.get("season"),
        pattern=doc.get("pattern"),
        color=doc.get("color"),
        tags=doc.get("tags", []),
        confidence_scores=doc.get("confidence_scores", {}),
        uploaded_at=doc["uploaded_at"],
    )

@router.get("/", response_model=list[WardrobeItemOut])
async def list_items():
    items = []
    async for doc in wardrobe_collection.find():
        items.append(_doc_to_out(doc))
    return items

@router.get("/{item_id}", response_model=WardrobeItemOut)
async def get_item(item_id: str):
    try:
        object_id = ObjectId(item_id)
    except InvalidId:
        raise HTTPException(status_code=404, detail="Item not found")

    doc = await wardrobe_collection.find_one({"_id": object_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Item not found")

    return _doc_to_out(doc)