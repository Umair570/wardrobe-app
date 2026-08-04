import sys, asyncio
sys.path.insert(0, 'backend')

async def main():
    print('')
    print('=== WARDROBE PLATFORM - LIVE DB SYNC CHECK ===')
    print('')

    from app.core.config import settings
    print('[1] CONFIG')
    print('    Supabase: ' + settings.supabase_url[:50])
    print('    MongoDB:  ' + settings.mongodb_uri[:50])
    print('    Qdrant:   ' + settings.qdrant_url[:50])
    print('    Embedding model: ' + settings.embedding_model)
    print('    STATUS: OK')
    print('')

    from app.services.storage.supabase import supabase_storage
    from app.constants.storage_paths import ALL_BUCKETS
    print('[2] SUPABASE STORAGE')
    buckets = [b.name for b in supabase_storage.client.storage.list_buckets()]
    missing = [b for b in ALL_BUCKETS if b not in buckets]
    print('    Buckets found:   ' + str(buckets))
    print('    Missing:         ' + (str(missing) if missing else 'NONE'))
    print('    STATUS: ALL 4 BUCKETS EXIST' if not missing else '    STATUS: MISSING BUCKETS')
    print('')

    from app.database.mongodb import db, wardrobe_collection, ingestion_jobs_collection
    print('[3] MONGODB ATLAS')
    await db.command('ping')
    wi = await wardrobe_collection.count_documents({})
    ij = await ingestion_jobs_collection.count_documents({})
    print('    Ping:                OK')
    print('    wardrobe_items:      ' + str(wi) + ' docs')
    print('    ingestion_jobs:      ' + str(ij) + ' docs')
    print('    STATUS: CONNECTED')
    print('')

    from app.services.vector.qdrant_service import qdrant_service
    print('[4] QDRANT VECTOR DB')
    info = qdrant_service.collection_info()
    cname = str(info.get('collection', 'N/A'))
    points = str(info.get('points_count', 0))
    status = str(info.get('status', 'N/A'))
    print('    Collection:   ' + cname)
    print('    Points count: ' + points)
    print('    Status:       ' + status)
    print('    STATUS: CONNECTED')
    print('')

    print('[5] CROSS-REFERENCE (MongoDB vs Qdrant)')
    mongo_count = await wardrobe_collection.count_documents({})
    qdrant_count = info.get('points_count', 0)
    print('    MongoDB wardrobe_items: ' + str(mongo_count))
    print('    Qdrant points:          ' + str(qdrant_count))
    if mongo_count == 0 and qdrant_count == 0:
        print('    RESULT: BOTH EMPTY - fresh setup, no uploads yet, CONSISTENT')
    elif mongo_count == qdrant_count:
        print('    RESULT: PERFECTLY IN SYNC')
    else:
        diff = mongo_count - qdrant_count
        print('    RESULT: WARNING - ' + str(diff) + ' items in MongoDB not yet indexed in Qdrant')
    print('')
    print('=== CHECK COMPLETE ===')
    print('')

asyncio.run(main())
