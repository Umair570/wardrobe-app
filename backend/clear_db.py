import asyncio
from app.database.mongodb import wardrobe_collection, saved_looks_collection, chat_sessions_collection, chat_messages_collection

async def main():
    res = await wardrobe_collection.delete_many({})
    print(f"Deleted {res.deleted_count} wardrobe items.")
    await saved_looks_collection.delete_many({})
    await chat_sessions_collection.delete_many({})
    await chat_messages_collection.delete_many({})
    print("Database cleared of all mock data.")

if __name__ == "__main__":
    asyncio.run(main())
