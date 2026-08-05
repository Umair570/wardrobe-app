from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from bson.errors import InvalidId

from app.database.mongodb import wardrobe_collection
from app.database.models import WardrobeItemOut
from app.auth.dependencies import get_current_user
from app.core.security import UserContext

router = APIRouter(prefix="/wardrobe", tags=["wardrobe"])


def _doc_to_out(doc) -> WardrobeItemOut:
    garment = doc.get("garment") or {}
    source = doc.get("source") or {}
    segmentation = doc.get("segmentation") or {}

    raw_image_url = doc.get("image_url") or source.get("image_url") or doc.get("source_image") or ""
    image_url = str(raw_image_url).strip() if raw_image_url else ""
    
    seg_path = doc.get("segmentation_path") or segmentation.get("cutout_url") or image_url

    return WardrobeItemOut(
        id=str(doc["_id"]),
        user_id=doc.get("user_id"),
        image_url=image_url,
        segmentation_path=seg_path,
        area_ratio=doc.get("area_ratio"),
        category=doc.get("category") or garment.get("category"),
        type=doc.get("type") or garment.get("type"),
        style=doc.get("style") or garment.get("style"),
        season=doc.get("season") or garment.get("season"),
        pattern=doc.get("pattern") or garment.get("pattern"),
        color=doc.get("color") or garment.get("color"),
        tags=doc.get("tags") or garment.get("tags") or [],
        confidence_scores=doc.get("confidence_scores") or doc.get("confidence") or {},
        uploaded_at=doc.get("uploaded_at") or doc.get("created_at"),
    )


@router.get("/", response_model=list[WardrobeItemOut])
async def list_items(current_user: UserContext = Depends(get_current_user)):
    items = []
    skipped = 0
    # Match exclusively the authenticated user's items
    query = {"user_id": current_user.id}
    async for doc in wardrobe_collection.find(query):
        try:
            items.append(_doc_to_out(doc))
        except Exception as err:
            skipped += 1
            print(f"[wardrobe] Skipping malformed doc {doc.get('_id')}: {err}")
    if skipped:
        print(f"[wardrobe] list_items: skipped {skipped} malformed document(s).")
    return items


def _parse_item_id(item_id: str):
    """Returns a query dict that matches either a string _id or ObjectId _id."""
    try:
        return {"$or": [{"_id": item_id}, {"_id": ObjectId(item_id)}]}
    except (InvalidId, Exception):
        return {"_id": item_id}


@router.get("/{item_id}", response_model=WardrobeItemOut)
async def get_item(item_id: str, current_user: UserContext = Depends(get_current_user)):
    query = {**_parse_item_id(item_id), "user_id": current_user.id}
    doc = await wardrobe_collection.find_one(query)
    if not doc:
        raise HTTPException(status_code=404, detail="Item not found")

    return _doc_to_out(doc)


from app.services.vector.qdrant_service import qdrant_service, _to_qdrant_id
from app.core.config import settings

@router.delete("/{item_id}")
async def delete_item(item_id: str, current_user: UserContext = Depends(get_current_user)):
    # 1. Delete from MongoDB
    query = {**_parse_item_id(item_id), "user_id": current_user.id}
    result = await wardrobe_collection.delete_one(query)
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")

    # 2. Delete from Qdrant
    if qdrant_service.available:
        try:
            # Qdrant accepts valid UUIDs, but item_id is usually a hex string
            qdrant_id = _to_qdrant_id(item_id) if len(item_id) == 24 else item_id
            await qdrant_service._run_blocking(
                qdrant_service.client.delete,
                collection_name=settings.qdrant_collection,
                points_selector=[qdrant_id]
            )
        except Exception as e:
            print(f"[wardrobe] Note: Failed to delete Qdrant vector for {item_id}: {e}")

    return {"ok": True}
