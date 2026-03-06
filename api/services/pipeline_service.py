import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from agents.graph import build_ad_graph

def run_pipeline_background(initial_state: dict = None):
    """
    Wrapper function to run the main LangGraph pipeline orchestrator.
    This function will be called as a background task.
    """
    try:
        print("Starting background LangGraph pipeline execution...")
        graph = build_ad_graph()
        state = initial_state or {}
        graph.invoke(state)
        print("Background pipeline execution finished successfully.")
    except Exception as e:
        print(f"Error during background pipeline execution: {e}")
