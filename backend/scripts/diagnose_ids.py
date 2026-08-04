"""
Quick diagnostic: shows exactly what IDs MongoDB has vs what Qdrant has.
Run from backend/:  python scripts/diagnose_ids.py
"""
import sys, os, asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.mongodb import wardrobe_collection
from app.services.vector.qdrant_service import qdrant_service

async def diagnose():
    print("=" * 60)
    print("STEP 1 — MongoDB _ids")
    print("=" * 60)
    mongo_ids = set()
    async for doc in wardrobe_collection.find({}, {"_id": 1, "user_id": 1}):
        raw = str(doc["_id"])
        mongo_ids.add(raw)
        print(f"  mongo _id: {raw}  user: {doc.get('user_id','?')[:12]}...")

    print(f"\nTotal MongoDB items: {len(mongo_ids)}\n")

    print("=" * 60)
    print("STEP 2 — Qdrant mongo_ids (all points in collection)")
    print("=" * 60)
    if not qdrant_service.available:
        print("ERROR: Qdrant not available!")
        return

    loop = asyncio.get_running_loop()
    import functools
    scroll_res, _ = await loop.run_in_executor(
        None,
        functools.partial(
            qdrant_service.client.scroll,
            collection_name=qdrant_service.collection_name,
            limit=200,
            with_payload=True,
        )
    )

    qdrant_mongo_ids = set()
    for r in scroll_res:
        mid = r.payload.get("mongo_id", "MISSING")
        user = r.payload.get("user_id", "?")[:12]
        qdrant_mongo_ids.add(mid)
        match = "[OK]" if mid in mongo_ids else "[STALE - not in MongoDB]"
        print(f"  qdrant mongo_id: {mid}  user: {user}...  {match}")

    print(f"\nTotal Qdrant points: {len(qdrant_mongo_ids)}")

    stale = qdrant_mongo_ids - mongo_ids
    missing_from_qdrant = mongo_ids - qdrant_mongo_ids

    print("\n" + "=" * 60)
    print("STEP 3 — Match Analysis")
    print("=" * 60)
    print(f"  ✅ Matching IDs: {len(mongo_ids & qdrant_mongo_ids)}")
    print(f"  ❌ Stale Qdrant points (no MongoDB doc): {len(stale)}")
    for s in stale:
        print(f"     → {s}")
    print(f"  ⚠️  MongoDB items missing from Qdrant: {len(missing_from_qdrant)}")
    for m in missing_from_qdrant:
        print(f"     → {m}")

asyncio.run(diagnose())
