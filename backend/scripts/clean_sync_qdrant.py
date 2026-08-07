"""
Clean Qdrant re-sync: deletes all existing points for the current user(s)
then re-syncs every MongoDB item using its _id as the Qdrant point ID.

Run from backend/:  python scripts/clean_sync_qdrant.py
"""
import sys, os, io, asyncio, functools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from PIL import Image
from app.database.mongodb import wardrobe_collection
from app.services.vector.qdrant_service import qdrant_service
from app.services.embedding.model_registry import embedding_service

async def clean_sync():
    if not qdrant_service.available:
        print("ERROR: Qdrant not available. Check QDRANT_URL and QDRANT_API_KEY in .env")
        return

    print(f"Connected to Qdrant collection: '{qdrant_service.collection_name}'")
    print(f"Embedding model: {embedding_service.active_key}\n")

    # Step 1: Wipe the entire collection by deleting all existing points
    loop = asyncio.get_running_loop()
    try:
        from qdrant_client.http import models as qmodels
        info = await loop.run_in_executor(
            None,
            functools.partial(qdrant_service.client.get_collection, qdrant_service.collection_name)
        )
        print(f"Current Qdrant points: {info.points_count}")
        print("Deleting all existing points...")
        await loop.run_in_executor(
            None,
            functools.partial(
                qdrant_service.client.delete_collection,
                qdrant_service.collection_name,
            )
        )
        # Recreate with the right dimensions
        from app.services.vector.collections import ensure_collection
        ensure_collection(qdrant_service.client, qdrant_service.collection_name)
        print("Collection wiped and recreated.\n")
    except Exception as e:
        print(f"WARNING during wipe: {e}\n")

    # Step 2: Load all MongoDB items
    items = await wardrobe_collection.find({}).to_list(length=None)
    print(f"Found {len(items)} items in MongoDB to sync.\n")

    ok = 0
    fail = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        for doc in items:
            item_id = str(doc["_id"])
            user_id = doc.get("user_id", "unknown")
            garment = doc.get("garment") or {}
            source = doc.get("source") or {}
            
            # Resolve image URL (original image for embedding)
            image_url = (
                doc.get("image_url")
                or source.get("image_url")
                or garment.get("image_url")
                or ""
            ).strip()

            print(f"Processing: {item_id[:12]}... | user: {user_id[:12]}...")

            if not image_url:
                print(f"  [!] No image_url — using zero vector fallback")
                # Upsert with a zero vector so the item at least gets a Qdrant point
                vector = [0.0] * 512
            else:
                try:
                    resp = await client.get(image_url)
                    if not resp.is_success:
                        print(f"  [!] HTTP {resp.status_code} downloading image. Skipping.")
                        fail += 1
                        continue
                    img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                    vector = embedding_service.embed_image(img)
                    if not vector:
                        print(f"  [!] Empty embedding returned. Skipping.")
                        fail += 1
                        continue
                    print(f"  [+] Embedded ({len(vector)} dims)")
                except Exception as e:
                    print(f"  [X] Embedding failed: {e}")
                    fail += 1
                    continue

            # Build payload from flat and nested schema
            payload = {
                "category": doc.get("category") or garment.get("category"),
                "type":     doc.get("type")     or garment.get("type"),
                "color":    doc.get("color")    or garment.get("color"),
                "style":    doc.get("style")    or garment.get("style"),
                "season":   doc.get("season")   or garment.get("season"),
                "pattern":  doc.get("pattern")  or garment.get("pattern"),
                "tags":     doc.get("tags")     or garment.get("tags") or [],
            }

            upserted = await qdrant_service.upsert_item_vector(
                item_id=item_id,
                vector=vector,
                user_id=user_id,
                payload=payload,
            )
            if upserted:
                print(f"  [OK] Synced to Qdrant with id={item_id[:12]}...")
                ok += 1
            else:
                print(f"  [FAIL] Qdrant upsert FAILED")
                fail += 1

    print(f"\n{'='*50}")
    print(f"Sync Complete --- {ok} synced, {fail} failed")
    print(f"{'='*50}")

asyncio.run(clean_sync())
