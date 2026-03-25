import asyncio
import os
import sys
import json

# Ensure root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.production.agent import run_production
from agents.shared.state import AdGenState

async def execute_render():
    payload_path = os.path.join("scripts", "render_payload.json")
    print(f"DEBUG: Looking for payload at {os.path.abspath(payload_path)}")
    if not os.path.exists(payload_path):
        print(f"❌ Cannot find {payload_path}")
        return

    with open(payload_path, "r") as f:
        data = json.load(f)

    # Mock state for ProductionAgent
    state = {
        "creative": {
            "storyboard_output": data["storyboard_output"],
            "script_output": data["script_output"],
            "audio_planning": data["audio_planning"],
            "avatar_config": {
                "selected_avatars": {
                    "gender": "young person",
                    "avatar_preferences": {"gender": "young person"},
                    "voice_preferences": {"language": "Hindi"}
                }
            }
        },
        "campaign_id": data["campaign_id"],
        "user_id": data["user_id"],
        "strategy": {
            "campaign_psychology": {
                "campaign_id": data["campaign_id"],
                "user_id": data["user_id"],
                "audio_planning": data["audio_planning"]
            }
        }
    }

    print(f"🚀 Triggering render for {data['campaign_id']}...")
    result = await run_production(state)
    
    render_results = result.get("production", {}).get("render_results", [])
    if render_results:
        print(f"✅ Render Complete. Video ID: {render_results[0].get('video_id')}")
        print(f"📂 Video Path: {render_results[0].get('local_path')}")
    else:
        print("❌ Render Failed. Results empty.")

if __name__ == "__main__":
    asyncio.run(execute_render())
