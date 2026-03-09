"""
Long-Term Memory (LTM) Service for Spectra AI.

Uses a SEPARATE MongoDB database (ai_ad_memory) to store per-company
learned preferences. Implements:
  - Temporary memory with repetition counting
  - Confidence-gated LTM updates
  - Memory versioning for rollbacks
  - Multi-tenant isolation via company_id
"""

import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv(override=True)

LTM_MONGODB_URL = os.getenv("LTM_MONGODB_URL")
if not LTM_MONGODB_URL:
    raise ValueError("LTM_MONGODB_URL not found in environment")

LTM_DB_NAME = "ai_ad_memory"

# ── Repetition threshold before promoting to LTM ──
REPETITION_THRESHOLD = 2
CONFIDENCE_THRESHOLD = 0.7
SIMILARITY_THRESHOLD = 0.8  # Not used directly in LLM logic but conceptually


class LTMDatabase:
    """Singleton holder for the LTM MongoDB connection."""
    client: AsyncIOMotorClient = None
    db = None


ltm = LTMDatabase()


async def connect_to_ltm():
    """Initialize the LTM MongoDB connection with resilience."""
    try:
        # Lower timeout and fail fast
        ltm.client = AsyncIOMotorClient(LTM_MONGODB_URL, serverSelectionTimeoutMS=5000)
        ltm.db = ltm.client[LTM_DB_NAME]
        
        # Verify connection
        await ltm.client.admin.command('ping')

        # Create indexes for fast lookups
        await ltm.db.company_memory.create_index("company_id", unique=True)
        await ltm.db.temporary_memory.create_index([("company_id", 1), ("agent", 1), ("suggestion", 1)])
        await ltm.db.feedback_history.create_index([("company_id", 1), ("created_at", -1)])

        print(f"✅ Connected to LTM Database: {LTM_MONGODB_URL[:30]}...")
    except Exception as e:
        print(f"❌ LTM Connection Failed: {e}")
        ltm.client = None
        ltm.db = None


async def close_ltm_connection():
    """Close the LTM MongoDB connection."""
    if ltm.client:
        ltm.client.close()
        print("Closed LTM connection")


# ═══════════════════════════════════════════
# COMPANY MEMORY CRUD
# ═══════════════════════════════════════════

async def get_company_memory(company_id: str) -> dict:
    """
    Retrieve the long-term memory for a company.
    Returns an empty structure if no memory exists yet.
    """
    if ltm.db is None:
        return {
            "company_id": company_id,
            "research_memory": {},
            "strategy_memory": {},
            "creative_memory": {},
            "production_memory": {},
            "version": 0,
        }
    doc = await ltm.db.company_memory.find_one({"company_id": company_id})

    if doc:
        doc["_id"] = str(doc["_id"])
        return doc

    # Return empty memory skeleton
    return {
        "company_id": company_id,
        "research_memory": {},
        "strategy_memory": {},
        "creative_memory": {},
        "production_memory": {},
        "version": 0,
    }


async def update_company_memory(company_id: str, agent: str, updates: dict):
    """
    Update long-term memory for a specific agent.
    Increments version and merges new preferences.
    """
    memory_key = f"{agent}_memory"

    # Get current memory
    current = await get_company_memory(company_id)
    current_agent_memory = current.get(memory_key, {})

    # Merge updates into current memory
    current_agent_memory.update(updates)

    # Upsert with version increment
    await ltm.db.company_memory.update_one(
        {"company_id": company_id},
        {
            "$set": {
                memory_key: current_agent_memory,
                "updated_at": datetime.utcnow().isoformat(),
            },
            "$inc": {"version": 1},
            "$setOnInsert": {
                "company_id": company_id,
                "created_at": datetime.utcnow().isoformat(),
            }
        },
        upsert=True,
    )

    new_version = current.get("version", 0) + 1
    print(f"   LTM updated for {company_id}/{agent} -> v{new_version}")
    return new_version


# ═══════════════════════════════════════════
# SEMANTIC MATCHING
# ═══════════════════════════════════════════

async def find_semantic_match(new_suggestion: str, existing_suggestions: list[str]) -> str:
    """
    Compare a new suggestion with a list of existing suggestions using LLM.
    Returns the matching suggestion string if a semantic match is found, else None.
    """
    if not existing_suggestions:
        return None

    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    import json

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        print("⚠️ OPENROUTER_API_KEY not found, skipping semantic match")
        return None

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        openai_api_key=openrouter_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0,
    )

    system_prompt = """You are a feedback classifier. Your task is to determine if a NEW suggestion means the SAME thing as any of the PREVIOUS suggestions in a list.
Even if wording is different, if the intent and specific action are identical, they match.
Return a JSON object with:
- "match": true/false
- "matched_suggestion": "the item from the list that matched" or null
"""

    prompt = f"""NEW Suggestion: "{new_suggestion}"
PREVIOUS Suggestions: {json.dumps(existing_suggestions)}

Does the new suggestion mean effectively the same thing as any item in the list?"""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ])
        
        # Extract JSON from response
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        
        data = json.loads(content)
        if data.get("match") and data.get("matched_suggestion") in existing_suggestions:
            print(f"   Semantic match found: '{new_suggestion}' == '{data['matched_suggestion']}'")
            return data["matched_suggestion"]
    except Exception as e:
        print(f"   Semantic matching error: {e}")
    
    return None


# ═══════════════════════════════════════════
# TEMPORARY MEMORY (feedback counting)
# ═══════════════════════════════════════════

async def record_temporary_feedback(company_id: str, agent: str, suggestion: str):
    """
    Record a piece of feedback in temporary memory.
    1. Checks for semantic matching with existing suggestions.
    2. Increments count of existing OR creates new entry.
    Returns the new count and the (potentially updated) suggestion string.
    """
    # Fetch all suggestions for this company/agent to check semantic similarity
    existing_docs = await get_pending_suggestions(company_id, agent)
    existing_suggestions = [d["suggestion"] for d in existing_docs]
    
    # Check if this new suggestion is semantically same as an existing one
    matched_suggestion = await find_semantic_match(suggestion, existing_suggestions)
    
    # Use the matched suggestion if found, otherwise use the new one
    target_suggestion = matched_suggestion if matched_suggestion else suggestion

    result = await ltm.db.temporary_memory.find_one_and_update(
        {"company_id": company_id, "agent": agent, "suggestion": target_suggestion},
        {
            "$inc": {"count": 1},
            "$set": {"last_seen": datetime.utcnow().isoformat()},
            "$setOnInsert": {
                "company_id": company_id,
                "agent": agent,
                "suggestion": target_suggestion,
                "created_at": datetime.utcnow().isoformat(),
            }
        },
        upsert=True,
        return_document=True,
    )

    count = result.get("count", 1)
    print(f"   Temp memory: {company_id}/{agent} '{target_suggestion[:40]}...' count={count}")
    return count, target_suggestion


async def get_pending_suggestions(company_id: str, agent: str = None):
    """Fetch all pending temporary memory for a company (optionally filtered by agent)."""
    query = {"company_id": company_id}
    if agent:
        query["agent"] = agent

    docs = []
    async for doc in ltm.db.temporary_memory.find(query):
        doc["_id"] = str(doc["_id"])
        docs.append(doc)
    return docs


async def clear_temporary_feedback(company_id: str, agent: str, suggestion: str):
    """Remove a temporary memory entry after it has been promoted to LTM."""
    await ltm.db.temporary_memory.delete_one(
        {"company_id": company_id, "agent": agent, "suggestion": suggestion}
    )


# ═══════════════════════════════════════════
# FEEDBACK HISTORY
# ═══════════════════════════════════════════

async def save_feedback_to_history(company_id: str, feedback_data: dict):
    """
    Save raw feedback to the feedback_history collection for auditing.
    """
    feedback_data["company_id"] = company_id
    feedback_data["created_at"] = datetime.utcnow().isoformat()
    result = await ltm.db.feedback_history.insert_one(feedback_data)
    return str(result.inserted_id)


# ═══════════════════════════════════════════
# PROCESS STRUCTURED FEEDBACK (full pipeline)
# ═══════════════════════════════════════════

async def process_structured_feedback(
    company_id: str,
    structured_feedback: dict,
    confidence: float,
):
    """
    Main entry point for processing validated + structured feedback.

    1. Records each agent-specific suggestion in temporary memory.
    2. If count >= REPETITION_THRESHOLD and confidence >= CONFIDENCE_THRESHOLD,
       promotes the suggestion to long-term memory.

    Args:
        company_id: The company's unique identifier.
        structured_feedback: Dict with keys like research_feedback, strategy_feedback, etc.
        confidence: The LLM-assigned confidence score (0-1).

    Returns:
        Dict with promotion results per agent.
    """
    results = {}

    agent_map = {
        "research_feedback": "research",
        "strategy_feedback": "strategy",
        "creative_feedback": "creative",
        "production_feedback": "production",
    }

    for feedback_key, agent_name in agent_map.items():
        suggestion = structured_feedback.get(feedback_key)
        if not suggestion:
            continue

        # 1. Record in temporary memory (includes semantic matching)
        count, finalized_suggestion = await record_temporary_feedback(company_id, agent_name, suggestion)

        # 2. Check promotion rules
        if count >= REPETITION_THRESHOLD and confidence >= CONFIDENCE_THRESHOLD:
            # Promote to LTM
            await update_company_memory(
                company_id,
                agent_name,
                {"learned_preference": finalized_suggestion}
            )
            # Clean up temporary entry
            await clear_temporary_feedback(company_id, agent_name, finalized_suggestion)
            results[agent_name] = {"status": "promoted", "suggestion": finalized_suggestion, "version": "incremented"}
            print(f"   Promoted to LTM: {company_id}/{agent_name}: '{finalized_suggestion[:50]}'")
        else:
            remaining = REPETITION_THRESHOLD - count
            results[agent_name] = {"status": "pending", "count": count, "remaining": remaining}

    return results
