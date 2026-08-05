import asyncio
import json
import httpx
from app.services.vector.qdrant_service import qdrant_service

async def main():
    async with httpx.AsyncClient() as client:
        payload = {
            "session_id": "test_smart_casual_123",
            "message": "A smart-casual, professional look featuring a crisp white button-down shirt and dark tailored trousers."
        }
        print("Sending request for smart-casual...")
        res = await client.post("http://localhost:8000/api/v1/chat", json=payload, timeout=30.0)
        print("Murree Response:")
        try:
            print(json.dumps(res.json(), indent=2))
        except:
            print(res.text)

if __name__ == "__main__":
    asyncio.run(main())
