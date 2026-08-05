import asyncio
import json
from app.services.retrieval.retrieval import retrieve_wardrobe_for_query
from app.services.stylist.stylist_service import generate_outfit_recommendation
from app.core.config import settings

async def main():
    user_id = "test_user_id_does_not_matter_because_auth_is_bypassed_if_we_mock"
    # Actually, retrieve_wardrobe_for_query uses current_user.id. Let's just find out what Qdrant returns.
    print(f"USING PROVIDER: {settings.llm_provider}")
    print(f"USING OUT API: {settings.active_llm_base_url}")
    print(f"HTTT INFO: config.py score_threshold={settings.qdrant_score_threshold}")
    
    # We will just test the LLM _expand_query because it might be returning weird things
    from app.services.retrieval.retrieval import _expand_query
    q1 = "A smart-casual, professional look featuring a crisp white button-down shirt and dark tailored trousers."
    expanded1 = await _expand_query(q1)
    print("EXPANDED 1:", expanded1)

    q2 = "I want a cozy outfit for lounging at a coffee shop on a chilly Sunday"
    expanded2 = await _expand_query(q2)
    print("EXPANDED 2:", expanded2)
    
    q3 = "What should I wear on a trip to Antarctica today"
    expanded3 = await _expand_query(q3)
    print("EXPANDED 3:", expanded3)

if __name__ == "__main__":
    asyncio.run(main())
