"""
LangGraph Orchestrator — Assembles all agents into a single graph.

The graph defines the execution order:
  Research → Strategy → Creative → Production

Each node receives the full AdGenState and writes its own outputs.

Future:
  - Add MemorySaver checkpointer for learning across campaigns
  - Add conditional edges for error recovery / retry
  - Add human-in-the-loop nodes for approval gates
"""

import os
import sys
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv(override=True)

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient

from utils.logger import logger
from agents.shared.state import AdGenState
from agents.research.agent import run_research
from agents.strategy.agent import run_strategy
from agents.creative.agent import run_creative
from agents.production.agent import run_production

# ── MongoDB Checkpointer Setup ────────────────────────────────
mongodb_url = os.getenv("MONGODB_URL")
client = None
checkpointer = None

if mongodb_url:
    try:
        # MongoDBSaver expects a synchronous pymongo.MongoClient
        # serverSelectionTimeoutMS=5000 ensures it doesn't hang for 20s if DNS/Auth fails
        client = MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
        # Verify connection immediately
        client.admin.command('ping')
        
        checkpointer = MongoDBSaver(client)
        logger.info("🧠 [Memory] MongoDB checkpointer (sync) connected successfully")
    except Exception as e:
        logger.error(f"❌ [Memory] Failed to connect to MongoDB for checkpoints: {e}")
        client = None
        checkpointer = None
else:
    logger.warning("⚠️ [Memory] MONGODB_URL not found in environment. Running without memory.")


def build_ad_graph(checkpointer=None):
    """
    Builds and compiles the full ad generation LangGraph.
    
    Graph structure:
        research → strategy → creative → production → END
    
    Returns a compiled graph that can be invoked with:
        graph.invoke(initial_state)
    """
    graph = StateGraph(AdGenState)

    # ── Register Nodes ────────────────────────────────────────
    graph.add_node("research", run_research)
    graph.add_node("strategy", run_strategy)
    graph.add_node("creative", run_creative)
    graph.add_node("production", run_production)

    # ── Define Edges (linear pipeline) ────────────────────────
    graph.set_entry_point("research")
    graph.add_edge("research", "strategy")
    graph.add_edge("strategy", "creative")
    graph.add_edge("creative", "production")
    graph.add_edge("production", END)

    # ── Compile with Checkpointer ─────────────────────────────
    compiled = graph.compile(checkpointer=checkpointer) if checkpointer else graph.compile()
    logger.info("✅ Full Ad Generation Graph compiled successfully")
    return compiled


def build_step_graph(step_name: str, checkpointer=None):
    """
    Builds a single-step graph for running one agent in isolation.
    This is used by the API when running steps individually (wizard mode).
    
    Args:
        step_name: One of 'research', 'strategy', 'creative', 'production'
    """
    node_map = {
        "research": run_research,
        "strategy": run_strategy,
        "creative": run_creative,
        "production": run_production,
    }
    
    if step_name not in node_map:
        raise ValueError(f"Unknown step: {step_name}. Must be one of {list(node_map.keys())}")
    
    graph = StateGraph(AdGenState)
    graph.add_node(step_name, node_map[step_name])
    graph.set_entry_point(step_name)
    graph.add_edge(step_name, END)
    
    compiled = graph.compile(checkpointer=checkpointer) if checkpointer else graph.compile()
    logger.info(f"✅ Single-step graph '{step_name}' compiled successfully")
    return compiled


# ── Pre-built graphs for fast access ──────────────────────────
# These are compiled once at import time and reused.
# The full pipeline graph:
# ad_pipeline = build_ad_graph()

# Individual step graphs for wizard mode:
research_graph = build_step_graph("research", checkpointer=checkpointer)
strategy_graph = build_step_graph("strategy", checkpointer=checkpointer)
creative_graph = build_step_graph("creative", checkpointer=checkpointer)
production_graph = build_step_graph("production", checkpointer=checkpointer)
