"""Memory Agent — LangGraph Node

Responsibilities:
  1. Retrieve past successful campaigns for the current user/company.
  2. Extract 'winning' angles, hooks, and psychological patterns.
  3. Inform the Research and Strategy phases of what has worked before.

Reads from state:  user_id, company_id
Writes to state:   memory
"""

import os
import sys
from typing import Dict, List, Any

# Ensure project root is on path for helper imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.logger import logger
from agents.shared.state import AdGenState
from api.services.db_mongo_service import get_all_documents, get_all_feedback


async def run_memory(state: AdGenState) -> dict:
    """
    LangGraph node for the Memory Agent.
    Retrieves and summarizes past successful campaigns.
    """
    logger.info("🧠 [Memory Agent] Starting...")
    user_id = state.get("user_id")
    company_id = state.get("company_id") or "default_company"
    
    if not user_id:
        logger.warning("   ⚠️ No user_id found in state. Skipping memory retrieval.")
        return {"memory": {}}

    try:
        from api.services.memory_service import get_company_memory
        
        # 1. Fetch long-term memory for this company
        company_memory = await get_company_memory(company_id)
        
        # 2. Fetch past successful campaigns from main DB for additional context
        campaigns = await get_all_documents("campaigns", limit=5, user_id=user_id)
        all_feedback = await get_all_feedback(limit=50)
        user_feedback = [f for f in all_feedback if f.get("user_id") == user_id]
        success_campaign_ids = [f.get("campaign_id") for f in user_feedback if f.get("rating", 0) >= 4]
        successful_campaigns = [c for c in campaigns if c.get("campaign_id") in success_campaign_ids]
        
        # 3. Summarize the 'Success DNA'
        memories = []
        for camp in successful_campaigns:
            # Extract key attributes that led to success
            psych = camp.get("campaign_psychology", {})
            blueprint = camp.get("pattern_blueprint", {})
            
            memories.append({
                "campaign_id": camp.get("campaign_id"),
                "product": camp.get("product_name"),
                "platform": camp.get("platform"),
                "angle": blueprint.get("angle"),
                "hook_style": psych.get("hook_style"),
                "performance_rating": next((f.get("rating") for f in user_feedback if f.get("campaign_id") == camp.get("campaign_id")), 4)
            })
            
        logger.info(f"   ✅ Retrieved {len(memories)} successful campaigns and {company_id} LTM.")
        
        return {
            "memory": {
                "successful_past_campaigns": memories,
                "preferred_styles": list(set([m["hook_style"] for m in memories if m.get("hook_style")])),
                "preferred_angles": list(set([m["angle"] for m in memories if m.get("angle")])),
                "company_ltm": company_memory,
                "summary_prompt": f"User has previously succeeded with {', '.join(list(set([m['angle'] for m in memories if m.get('angle')])))[:100]} angles. Company LTM version: v{company_memory.get('version', 0)}"
            }
        }
    except Exception as e:
        logger.error(f"   ❌ Memory retrieval failed: {e}")
        return {"memory": {}, "errors": [f"MemoryAgent error: {e}"]}
