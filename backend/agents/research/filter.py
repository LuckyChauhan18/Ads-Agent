import os
import json
import re
from typing import List, Dict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Load .env from root directory (parent of src)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path, override=True)

class DNAFilter:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=self.api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.3
        )

    def is_senseless(self, ad: Dict) -> bool:
        """Checks if the ad DNA contains senseless placeholders."""
        dna = ad.get("dna", {})
        hook = dna.get("hook", "").lower()
        punch = dna.get("punch_line", "").lower()
        
        placeholders = [
            "copy could not be isolated",
            "string",
            "n/a",
            "content was removed",
            "advertising standards"
        ]
        
        # If hook or punch line match placeholders, it's senseless
        if any(p in hook for p in placeholders) or any(p in punch for p in placeholders):
            return True
        
        # If metadata is just placeholder 'string'
        if dna.get("hook_type") == "string" or dna.get("tone") == "string":
            return True
            
        return False

    def enrich_with_research(self, ad: Dict, brand_info: str, product_info: str, category: str) -> Dict:
        """Uses LLM to synthesize realistic DNA based on nested brand and product research."""
        company = ad.get("company", "Unknown Brand")
        
        prompt = f"""
        You are a senior ad creative strategist. We extract data from Meta Ads Library, but some ads are missing copy.
        
        CATEGORY: {category}
        BRAND: {company}
        
        BRAND RESEARCH SUMMARY (Company Level):
        {brand_info}
        
        SPECIFIC PRODUCT RESEARCH (Product Level):
        {product_info}
        
        YOUR TASK:
        Synthesize a realistic, high-performing Instagram/Facebook ad variant for '{company}'. 
        The ad must reflect the brand's actual value proposition, winning slogans, and typical tone derived from the nested research.
        
        Return ONLY a JSON object:
        {{
            "dna": {{
                "hook": "A powerful 1-2 sentence hook for the ad.",
                "punch_line": "The concluding punch line or CTA phrase.",
                "hook_type": "Question/Offer/Pain Point/Bold Claim/Story",
                "tone": "Professional/Casual/Urgent/Empathetic",
                "angle": "Price/Lifestyle/Technical/Social Proof/Benefit",
                "problem": "The specific user problem this ad addresses.",
                "solution": "How the product solves it."
            }}
        }}
        """

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a marketing data enrichment expert. Return ONLY JSON."),
                HumanMessage(content=prompt)
            ])
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            
            enrichment = json.loads(content)
            # Preserve original company and metadata, update DNA
            ad['dna'].update(enrichment['dna'])
            return ad
        except Exception as e:
            print(f"      Filter Warning: Enrichment failed for {company}: {e}")
            return ad

    def filter_and_enrich(self, ad_list: List[Dict], research_data: Dict) -> List[Dict]:
        """Main entry point: filters and enriches sparse ads using provided nested research."""
        print(f"--- Running DNA Filter & Enrichment for {len(ad_list)} ads ---")
        enriched_list = []

        for ad in ad_list:
            company = ad.get("company")
            category = ad.get("category", "Product")
            if not self.is_senseless(ad):
                enriched_list.append(ad)
                continue
                
            print(f"  --- Enriching sparse ad for: {company}")
            
            # Get the nested research for this ad's company
            company_research = research_data.get(company, {}).get("company_info", "A leading competitor.")
            product_research = research_data.get(company, {}).get("product_info", "High-quality products in the category.")

            # Step 2: Synthesize high-quality DNA
            enriched_ad = self.enrich_with_research(ad, company_research, product_research, category)
            enriched_list.append(enriched_ad)
            
        return enriched_list


