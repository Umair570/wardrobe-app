"""
Script to dynamically backfill all existing MongoDB wardrobe items into Qdrant.
Reads the image URL, buffers the image, runs it through the FashionCLIP local model,
and upserts the 512-dim embedding to Qdrant.
"""

import sys
import os
import io
import asyncio
import httpx
from PIL import Image

# Ensure backend root is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.mongodb import wardrobe_collection
from app.services.vector.qdrant_service import qdrant_service
from app.services.embedding.model_registry import embedding_service


async def sync():
    if not qdrant_service.available:
        print("ERROR: Qdrant service is not available. Check your QDRANT_URL and API keys.")
        return

    if not embedding_service.is_available():
        print("ERROR: Embedding model not available. Ensure models are downloaded.")
        return
        
    print(f"Connected to Qdrant collection: {qdrant_service.collection_name}")
    print(f"Using Embedding Model: {embedding_service.active_key}")

    items_cursor = wardrobe_collection.find({})
    items = await items_cursor.to_list(length=None)
    
    print(f"Found {len(items)} items in MongoDB.")
    if len(items) == 0:
        print("No items to sync.")
        return
    
    success_count = 0
    fail_count = 0

    async with httpx.AsyncClient() as client:
        for doc in items:
            item_id = str(doc["_id"])
            user_id = doc.get("user_id", "unknown")
            
            image_url = doc.get("image_url") or (doc.get("source", {}) or {}).get("image_url")
            
            if not image_url:
                print(f"Skipping {item_id}: No image_url found.")
                fail_count += 1
                continue
                
            print(f"Processing {item_id} from {image_url} ...")
            try:
                # Handle possible localhost relative URLs vs full Supabase URLs
                if image_url.startswith("/"):
                    # Assuming local development URL prefix
                    image_url = "http://127.0.0.1:8000" + image_url

                resp = await client.get(image_url, timeout=20.0)
                if not resp.is_success:
                    print(f"  [X] Failed to download image (HTTP {resp.status_code})")
                    fail_count += 1
                    continue
                    
                image = Image.open(io.BytesIO(resp.content)).convert("RGB")
                
                # Model inference - 512 dimensions for FashionCLIP
                vector = embedding_service.embed_image(image)
                
                if not vector:
                    print("  [X] Failed to extract embedding.")
                    fail_count += 1
                    continue
                    
                # Create Payload matching the app's standard format
                payload = {
                    "category": doc.get("garment", {}).get("category") or doc.get("category"),
                    "type":     doc.get("garment", {}).get("type") or doc.get("type"),
                    "color":    doc.get("garment", {}).get("color") or doc.get("color"),
                    "style":    doc.get("garment", {}).get("style") or doc.get("style"),
                    "season":   doc.get("garment", {}).get("season") or doc.get("season"),
                    "pattern":  doc.get("garment", {}).get("pattern") or doc.get("pattern"),
                    "tags":     doc.get("garment", {}).get("tags") or doc.get("tags", []),
                }
                
                await qdrant_service.upsert_item_vector(
                    item_id=item_id,
                    vector=vector,
                    user_id=user_id,
                    payload=payload
                )
                print(f"  [+] Synced item {item_id} successfully.")
                success_count += 1
                
            except Exception as e:
                print(f"  [X] Exception on {item_id}: {e}")
                fail_count += 1

    print(f"\n--- Sync Complete ---")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")

if __name__ == "__main__":
    asyncio.run(sync())
