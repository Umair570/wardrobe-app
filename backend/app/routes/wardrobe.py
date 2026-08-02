from fastapi import APIRouter, HTTPException
from bson import ObjectId
from bson.errors import InvalidId

from app.database.mongodb import wardrobe_collection
from app.database.models import WardrobeItemOut

router = APIRouter(prefix="/wardrobe", tags=["wardrobe"])


def _doc_to_out(doc) -> WardrobeItemOut:
    return WardrobeItemOut(
        id=str(doc["_id"]),
        source_image=doc.get("source_image", ""),
        segmentation_path=doc.get("segmentation_path", ""),
        area_ratio=doc.get("area_ratio"),
        category=doc.get("category"),
        type=doc.get("type"),
        style=doc.get("style"),
        season=doc.get("season"),
        pattern=doc.get("pattern"),
        color=doc.get("color"),
        tags=doc.get("tags", []),
        confidence_scores=doc.get("confidence_scores", {}),
        uploaded_at=doc.get("uploaded_at"),
    )


@router.get("/", response_model=list[WardrobeItemOut])
async def list_items():
    items = []
    skipped = 0
    async for doc in wardrobe_collection.find():
        try:
            items.append(_doc_to_out(doc))
        except Exception as err:
            # One malformed document used to 500 the entire endpoint, which
            # meant EVERY item vanished from the wardrobe, not just the bad
            # one. Skip and log instead so the rest still render.
            skipped += 1
            print(f"[wardrobe] Skipping malformed doc {doc.get('_id')}: {err}")
    if skipped:
        print(f"[wardrobe] list_items: skipped {skipped} malformed document(s).")
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


@router.delete("/{item_id}")
async def delete_item(item_id: str):
    try:
        object_id = ObjectId(item_id)
    except InvalidId:
        raise HTTPException(status_code=404, detail="Item not found")

    result = await wardrobe_collection.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"ok": True}