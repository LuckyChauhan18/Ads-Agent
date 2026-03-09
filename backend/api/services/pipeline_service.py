import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from agents.graph import build_ad_graph
from utils.logger import logger

def run_pipeline_background(initial_state: dict = None):
    """
    Wrapper function to run the main LangGraph pipeline orchestrator.
    This function will be called as a background task.
    """
    try:
        logger.info("============== STARTING NEW PIPELINE RUN ==============")
        logger.info(f"Initial State: {list(initial_state.keys()) if initial_state else 'None'}")
        
        graph = build_ad_graph()
        state = initial_state or {}
        graph.invoke(state)
        
        logger.info("✅ Background pipeline execution finished successfully.")
        logger.info("=======================================================")
    except Exception as e:
        logger.error(f"❌ Error during background pipeline execution: {e}", exc_info=True)
