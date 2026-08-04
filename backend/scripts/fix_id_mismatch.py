"""
Migration script: Fix the ID mismatch between Qdrant and MongoDB.

The old ingest pipeline used uuid4().hex as the Qdrant ID but allowed
MongoDB to auto-generate its own ObjectId. This script:
  1. Iterates all existing MongoDB items.
  2. Checks whether their _id (ObjectId) is in Qdrant (it's not — the uuid4 is).
  3. Creates a new doc with _id = uuid4 hex that MATCHES the existing Qdrant point.
  4. Deletes the old ObjectId doc.

If there is no matching Qdrant point, the item gets a fresh uuid4 _id and is
re-embedded + re-upserted into Qdrant.

Run from wardrobe-app/backend:
    python scripts/fix_id_mismatch.py
"""

import sys
import os
import io
import asyncio
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bson import ObjectId
from app.database.mongodb import wardrobe_collection
from app.services.vector.qdrant_service import qdrant_service

async def is_valid_object_id(s: str) -> bool:
    try:
        ObjectId(s)
        return True
    except Exception:
        return False

async def migrate():
    print("=== Starting ID mismatch migration ===\n")

    if not qdrant_service.available:
        print("WARNING: Qdrant not available. Items will only get new string _ids in MongoDB without re-embedding.")

    cursor = wardrobe_collection.find({})
    items = await cursor.to_list(length=None)
    print(f"Found {len(items)} total items in MongoDB.\n")

    fixed = 0
    skipped = 0

    for doc in items:
        raw_id = doc["_id"]
        id_str = str(raw_id)

        # Skip items already using a uuid hex string (not an ObjectId)
        try:
            ObjectId(id_str)
            is_obj_id = True
        except Exception:
            is_obj_id = False

        if not is_obj_id:
            print(f"  [OK] Item {id_str[:12]}... already has string _id. Skipping.")
            skipped += 1
            continue

        # This is an old ObjectId doc. Assign a new string ID.
        new_id = uuid.uuid4().hex
        print(f"  [MIGRATING] ObjectId {id_str} → new string id {new_id}")

        # Create new doc with string _id
        new_doc = {k: v for k, v in doc.items() if k != "_id"}
        new_doc["_id"] = new_id

        try:
            await wardrobe_collection.insert_one(new_doc)
            await wardrobe_collection.delete_one({"_id": raw_id})
            print(f"    [+] Replaced MongoDB doc. New _id = {new_id}")

            # Now re-embed and upsert into Qdrant so the IDs actually match
            if qdrant_service.available:
                import httpx
                from PIL import Image
                from app.services.embedding.model_registry import embedding_service

                source = doc.get("source") or {}
                image_url = doc.get("image_url") or source.get("image_url") or ""
                if image_url and embedding_service.is_available():
                    try:
                        async with httpx.AsyncClient() as client:
                            resp = await client.get(image_url, timeout=20.0)
                            if resp.is_success:
                                img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                                vector = embedding_service.embed_image(img)
                                if vector:
                                    garment = doc.get("garment") or {}
                                    payload = {
                                        "category": doc.get("category") or garment.get("category"),
                                        "type": doc.get("type") or garment.get("type"),
                                        "color": doc.get("color") or garment.get("color"),
                                        "style": doc.get("style") or garment.get("style"),
                                        "season": doc.get("season") or garment.get("season"),
                                        "pattern": doc.get("pattern") or garment.get("pattern"),
                                        "tags": doc.get("tags") or garment.get("tags") or [],
                                    }
                                    await qdrant_service.upsert_item_vector(
                                        item_id=new_id,
                                        vector=vector,
                                        user_id=doc.get("user_id", "unknown"),
                                        payload=payload,
                                    )
                                    print(f"    [+] Re-upserted into Qdrant with new_id={new_id}")
                                else:
                                    print(f"    [!] Embedding returned empty vector for {new_id}")
                            else:
                                print(f"    [!] Could not download image (HTTP {resp.status_code}) for {new_id}")
                    except Exception as e:
                        print(f"    [!] Re-embedding failed: {e}")
                else:
                    print(f"    [!] No image_url or embedding service unavailable — Qdrant NOT updated for {new_id}")

            fixed += 1

        except Exception as e:
            print(f"    [X] Failed to migrate {id_str}: {e}")

    print(f"\n=== Migration complete: {fixed} fixed, {skipped} already OK ===")

if __name__ == "__main__":
    asyncio.run(migrate())
