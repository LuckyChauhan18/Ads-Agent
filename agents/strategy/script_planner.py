import os
import json
from typing import Dict, Any

class ScriptPlannerEngine:
    def __init__(self, campaign_psychology: Dict[str, Any]):
        self.campaign = campaign_psychology
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shared", "ads_template_db")

    def _load_template(self, ad_type: str) -> Dict[str, Any]:
        """Loads a template from the database."""
        # Sanitize ad_type for filename
        filename = ad_type.lower().replace(" ", "_").replace("/", "_") + ".json"
        template_path = os.path.join(self.template_dir, filename)
        
        if os.path.exists(template_path):
            with open(template_path, "r") as f:
                return json.load(f)
        
        # Fallback to product_demo if not found
        default_path = os.path.join(self.template_dir, "product_demo.json")
        if os.path.exists(default_path):
            with open(default_path, "r") as f:
                return json.load(f)
        
        return {}

    def plan_script(self, ads_type_preference: str = None) -> Dict[str, Any]:
        """
        Decides on the ad template and avatar requirement.
        1. Uses explicit preference if available.
        2. Otherwise, infers from funnel stage or psychology.
        """
        ad_type = ads_type_preference
        
        if not ad_type:
            # Simple heuristic if no preference
            funnel_stage = self.campaign.get("funnel_stage", "cold")
            if funnel_stage == "cold":
                ad_type = "influencer"
            else:
                ad_type = "product_demo"
        
        template = self._load_template(ad_type)
        
        return {
            "ad_type": ad_type,
            "template": template,
            "needs_avatar": template.get("needs_avatar", False),
            "planning_notes": f"Selected {ad_type} template based on user preference or funnel stage."
        }
