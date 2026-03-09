import re
import json
import os
from typing import List, Dict
from dotenv import load_dotenv
from google import genai

# Load .env from root directory (parent of src)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path, override=True)

class ProductUnderstandingEngine:
    def __init__(self, raw_input: Dict, api_key: str = None):
        self.raw_input = raw_input
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        # Initialize the Gemini Client
        self.client = genai.Client(api_key=self.api_key)

    def detect_category(self, description: str) -> str:
        desc = description.lower()
        if "running" in desc and "shoe" in desc:
            return "Running Shoes"
        if "shoe" in desc:
            return "Footwear"
        return "General Product"

    def detect_price_range(self, price: int) -> str:
        if price < 2000:
            return "Below ₹2,000"
        elif price < 4000:
            return "₹2,000–₹4,000"
        elif price < 6000:
            return "₹4,000–₹6,000"
        else:
            return "Above ₹6,000"

    def parse_features(self, features_text: str) -> List[str]:
        return [f.strip() for f in features_text.split(",") if f.strip()]

    def detect_brand_fame(self, brand_name: str) -> str:
        if brand_name is None:
            return "unknown"
        famous_brands = [
            "nike", "adidas", "puma", "reebok", "asics", "skechers", "new balance"
        ]
        return "famous" if brand_name.lower() in famous_brands else "known"

    def get_understanding(self) -> Dict:
        """Uses AI (Gemini) to get a deep understanding of the product."""
        brand_name = self.raw_input.get("brand_name") or self.raw_input.get("company_name")
        description = self.raw_input.get("description", "")
        price = self.raw_input.get("price", 0)
        features_text = self.raw_input.get("features_text", "")
        
        prompt = f"""
        Analyze the following product data and return a structured JSON object.
        
        DATA:
        - Product Name: {self.raw_input.get("product_name")}
        - Brand/Company: {brand_name}
        - Description: {description}
        - Price: {price}
        - Raw Features: {features_text}
        
        YOUR TASK:
        Return ONLY a JSON object with these keys:
        1. "product_name": String
        2. "brand_name": String (cleaned)
        3. "category": String (e.g., "Running Shoes", "Skincare", "Body Wash", etc.)
        4. "description": String (raw or slightly cleaned)
        5. "price_range": String (e.g., "₹4,000–₹6,000", "Premium", etc.)
        6. "features": List of strings (extracted intelligently from description and features_text)
        7. "target_user": String (who is this for?)
        8. "brand_fame_level": String ("famous" or "unknown" - search your internal knowledge)
        
        CRITICAL: 
        - DO NOT use generic categories like "shop", "product", or "general". 
        - Use specific industry terms (e.g., "Skincare", "Electronics", "Apparel").
        - Accurately verify the brand's primary industry.
        
        BE ACCURATE.
        """

        understanding = {}
        try:
            # Use gemini-2.5-flash which we confirmed works
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            content = response.text
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            
            understanding = json.loads(content)
            
        except Exception as e:
            print(f" AI Product Understanding failed: {e}. Falling back to rule-based.")
            
            # Basic Regex-based category detection for better fallback
            category = "General Product"
            desc_low = description.lower()
            if any(k in desc_low for k in ["running", "shoes", "sneakers"]): category = "Footwear"
            elif any(k in desc_low for k in ["skincare", "face", "moisturizing", "bathing bar", "soap", "cream"]): category = "Skincare/Personal Care"
            elif any(k in desc_low for k in ["clothing", "apparel", "shirt", "pant"]): category = "Apparel"
            
            # Price range detection
            price_range = "Unknown"
            if price > 0:
                if price < 2000: price_range = "Below ₹2,000"
                elif price < 5000: price_range = "₹2,000-₹5,000"
                else: price_range = "Premium"

            understanding = {
                "product_name": self.raw_input.get("product_name"),
                "brand_name": brand_name,
                "category": category,
                "description": description,
                "price_range": price_range,
                "features": [f.strip() for f in features_text.split(",") if f.strip()],
                "target_user": self.raw_input.get("target_user_hint") or "General Audience",
                "brand_fame_level": "unknown"
            }

        # Let LLM handling be the primary source of truth, generalized
        if "category" not in understanding or not understanding["category"]:
            understanding["category"] = "General"

        # Pass through product_url for Buy Now CTA in video
        if self.raw_input.get("product_url"):
            understanding["product_url"] = self.raw_input["product_url"]

        return understanding

if __name__ == "__main__":
    # Test execution
    # Assuming run from root: python src/product_understanding.py
    # Look for input in root or output/
    import os
    input_path = "product_input.json" if os.path.exists("product_input.json") else "../output/product_input.json"
    
    if os.path.exists(input_path):
        with open(input_path, "r") as f:
            data = json.load(f)
        engine = ProductUnderstandingEngine(data)
        understanding = engine.get_understanding()
        print(json.dumps(understanding, indent=2))
    else:
        print("Input file not found.")
