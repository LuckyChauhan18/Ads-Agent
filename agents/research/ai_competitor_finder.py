import os
import json
from typing import TypedDict, List, Dict, Annotated, Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

# Load .env from root directory (parent of src)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path, override=True)

# Define the state for our graph
class AgentState(TypedDict):
    product_info: Dict
    is_famous: bool
    competitor_brands: List[str]
    error: str

class AICompetitorFinder:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        
        # Initialize the LLM via OpenRouter
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=self.api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0 # Lower temperature for classification
        )
        
        # Build the graph
        self.graph = self._build_graph()

    def _check_fame_node(self, state: AgentState) -> Dict:
        """Evaluates if the brand is a major market leader/famous brand."""
        product_info = state["product_info"]
        brand_name = product_info.get("brand_name", "")
        
        # Priority: Check if pre-detected by understanding engine
        if product_info.get("brand_fame_level") == "famous":
            return {"is_famous": True}
            
        if not brand_name or brand_name.lower() == "none" or brand_name.lower() == "unknown":
            return {"is_famous": False}
            
        prompt = f"""
        Is '{brand_name}' a famous, well-known global or major regional brand that would have a significant presence in the Meta Ads Library?
        Examples of famous: Nike, Adidas, Boat, Mamaearth, Zomato.
        Examples of NOT famous: A local new boutique, a niche startup 'AirFlex', etc.
        
        Return ONLY a JSON object: {{"is_famous": true/false}}
        """
        
        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a market branding expert. Return only JSON."),
                HumanMessage(content=prompt)
            ])
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            result = json.loads(content)
            return {"is_famous": result.get("is_famous", False)}
        except Exception as e:
            print(f"Fame check failed: {e}")
            return {"is_famous": False, "error": str(e)}
    def _discover_competitors_node(self, state: AgentState) -> Dict:
        """Finds competitor brands based on brand fame and product context using LLM and optional Tavily search."""
        product_info = state["product_info"]
        own_brand = product_info.get('brand_name', '').strip()
        category = product_info.get('category', 'product')
        is_famous = state.get("is_famous", False)
        
        # Tavily Search (Deep Thinking)
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        tavily_context = ""
        if tavily_api_key and own_brand.lower() not in ["none", "unknown", ""]:
            try:
                import requests
                print(f"🕵️‍♂️ Running deep thinking web search for {own_brand} competitors via Tavily...")
                query = f"What are the top direct competitor brands for '{own_brand}' in the {category} industry in India?"
                response = requests.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_api_key,
                        "query": query,
                        "search_depth": "basic",
                        "include_answer": True
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    tavily_context = data.get("answer", "")
                    if not tavily_context:
                        tavily_context = "\n".join([r.get("content", "") for r in data.get("results", [])[:3]])
                    print("✅ Tavily search successful.")
            except Exception as e:
                print(f"⚠️ Tavily search failed: {e}")
        
        # Sanitize category/root_product
        root_product = product_info.get('root_product', category)
        if root_product.lower().strip() in ["shop", "product", "general", "store"]:
            root_product = category # Fallback to category if root_product is too generic
        
        if is_famous and own_brand.lower() != "unknown" and own_brand.lower() != "none":
            prompt = f"""
            Identify the top 5 direct market competitors for the famous brand '{own_brand}' in the Indian market.
            These competitors must be in the same primary industry.
            
            Industry Context: {category}
            Product Context: {product_info.get('description', '')}
            
            Deep Web Research Context (Tavily):
            {tavily_context}
            
            IMPORTANT: Ensure the competitors perfectly match the industry context ({category}). Do not return brands from unrelated industries.
            
            RULES:
            1. DO NOT include '{own_brand}'.
            2. Focus on brands that compete with '{own_brand}''s core products.
            3. Ensure they are relevant to the Indian consumer.
            
            Return ONLY a JSON list of 5 competitor brand names.
            """
        else:
            prompt = f"""
            Find exactly 5 competitor brands that make {root_product}s in the Indian market.
            These must be DIRECT competitors for a product with these details:
            
            - Our Product: {product_info.get('product_name')}
            - Our Brand: {own_brand}
            - Description: {product_info.get('description', '')}
            - Root Product Type: {root_product}
            - Category: {category}
            - Price Range: {product_info.get('price_range')}
            - Key Features: {", ".join(product_info.get('features', []))}
            
            Deep Web Research Context (Tavily):
            {tavily_context}
            
            CRITICAL RULES:
            1. DO NOT include "{own_brand}".
            2. Find brands that ALSO make {root_product} (same product type).
            3. Competitors should be in a similar price range/target audience.
            4. Focus on Indian market competitors.
            
            Return ONLY a JSON list of 5 competitor brand names.
            """

        
        try:
            response = self.llm.invoke([
                SystemMessage(content=f"You are a market research assistant specializing in {root_product}s. Return ONLY a JSON list of brand names. NEVER include {own_brand}."),
                HumanMessage(content=prompt)
            ])
            
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            brands = json.loads(content)
            # Safety: remove own brand if LLM still included it
            brands = [b for b in brands if b.lower() != own_brand.lower()]
            print(f"Found {len(brands)} competitor {root_product} brands: {brands}")
            return {"competitor_brands": brands}
        except Exception as e:
            return {"error": str(e), "competitor_brands": []}

    def _router(self, state: AgentState) -> Literal["discover", "end"]:
        """Always runs discover to ensure we get specific competitors."""
        return "discover"

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("check_fame", self._check_fame_node)
        workflow.add_node("discover", self._discover_competitors_node)
        
        # Set entry point
        workflow.set_entry_point("check_fame")
        
        # Add conditional edge
        workflow.add_conditional_edges(
            "check_fame",
            self._router,
            {
                "discover": "discover",
                "end": END
            }
        )
        
        # Add edge from discover to end
        workflow.add_edge("discover", END)
        
        return workflow.compile()

    def resolve_brands(self, query: str) -> List[str]:
        """Converts a generic search query into a list of specific brand names."""
        prompt = f"""
        Given the search query: '{query}'
        Identify 5 specific, real-world competitor brand names that are active in this market.
        DO NOT return the query itself. Return ONLY specific brand names.
        
        Return ONLY a JSON object: {{"brands": ["Brand1", "Brand2", "Brand3", "Brand4", "Brand5"]}}
        If you cannot find specific brands, return an empty list.
        """

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a market research expert. Return ONLY JSON."),
                HumanMessage(content=prompt)
            ])
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            result = json.loads(content)
            brands = result.get("brands", [])
            # Filter out the query itself if the AI returned it
            return [b for b in brands if b.lower().strip() != query.lower().strip() and len(b) > 2]
        except Exception as e:
            print(f"Brand resolution failed for '{query}': {e}")
            return []

    def verify_ad_match(self, ad_data: Dict, product_info: Dict, ads_type: str = "product_demo") -> bool:
        """Verifies if an extracted ad matches the product's contextual properties."""
        prompt = f"""
        You are an Ad Relevance Analyst. Determine if the EXTRACTED AD is a reasonable context match for the TARGET PRODUCT and STYLE.
        
        TARGET PRODUCT:
        - Category: {product_info.get('category')}
        - Features: {', '.join(product_info.get('features', []))}
        - Price: {product_info.get('price_range')}
        - Requested Style focus: {ads_type}
        
        EXTRACTED AD:
        - Company: {ad_data.get('company')}
        - Hook: {ad_data['dna'].get('hook')}
        
        VERIFICATION RULES:
        1. BE LENIENT on industry. If the ad is in the same general space (e.g., footcare / shoes), it is a match.
        2. STYLE ALIGNMENT: The user wants a '{ads_type}' ad (e.g., influencer means authentic narrator face; product_demo means focus on product closeups). If the ad content absolutely violates the chosen format (e.g., text-only when influencer was asked), do not score high, but ONLY discard if completely layout invariant.
        3. DO NOT discard if the hook is simple or generic.
        4. ONLY discard if the ad is clearly unrelated (e.g., a software SaaS ad when looking for beauty creams).
        
        Return ONLY a JSON object: {{"is_match": true/false, "reason": "brief reason"}}
        """
        try:
            response = self.llm.invoke([
                SystemMessage(content="You are an ad quality auditor. Return ONLY JSON."),
                HumanMessage(content=prompt)
            ])
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            result = json.loads(content)
            is_match = result.get("is_match", False)
            if not is_match:
                print(f"Ad discarded ({ad_data.get('company')}): {result.get('reason')}")
            return is_match
        except Exception as e:
            print(f"Ad verification failed: {e}")
            return True # Default to True on error to avoid over-filtering

    def refine_ad_dna(self, ad_data: Dict) -> Dict:
        """Refines the ad DNA using LLM to extract punch lines and improve metadata."""
        print(f"      Refining DNA for {ad_data.get('company')}...")
        hook = ad_data['dna'].get('hook', '')
        
        prompt = f"""
        Analyze this Facebook/Instagram ad copy and extract/refine it into high-quality marketing DNA.
        
        AD COPY (RAW):
        {hook}
        
        YOUR TASK:
        1. TRANSLATE TO ENGLISH: If the text is in Hindi or mixed, translate it into fluent, professional English based on its meaning.
        2. ENHANCE QUALITY: If the raw text is poor quality, repetitive, or empty, use your knowledge of the brand to generate an informative and compelling 'Hook' and 'Punch Line' that fits the product context.
        3. BEAUTIFY CONTENT: Ensure both the Hook and Punch Line are 'beautiful'—informative, premium, and ready for high-converting ads.
        
        Return ONLY a JSON object:
        {{
            "punch_line": "The most powerful, memorable concluding message (Concise & Impactful English)",
            "hook_type": "Question, Offer, Pain Point, Bold Claim, or Story",
            "tone": "Professional, Urgent, Casual, or Empathetic",
            "angle": "Price, Lifestyle, Technical, or Social Proof",
            "refined_hook": "The first 1-2 sentences that grab attention (Informative English)",
            "problem": "The specific customer pain point identified from the ad copy",
            "solution": "How the product solves that specific problem",
            "offer": "Any promotion, discount, or unique value proposition (e.g. '20% Off', 'Free Shipping', or 'Yes' if generic)",
            "emoji_usage": true,
            "text_length": 150
        }}
        """
        try:
            response = self.llm.invoke([
                SystemMessage(content=f"You are a master ad copywriter specializing in converting raw market data into high-quality, English-only ad assets. If inputs are messy, you generate informative and premium creative copy."),
                HumanMessage(content=prompt)
            ])
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            
            enrichment = json.loads(content)
            # Update the DNA with LLM insights
            ad_data['dna'].update(enrichment)
            # Sync hook with refined_hook if it was messy
            if enrichment.get("refined_hook"):
                ad_data['dna']['hook'] = enrichment['refined_hook']
            
            return ad_data
        except Exception as e:
            print(f"      Warning: DNA Refinement failed: {e}")
            ad_data['dna']['punch_line'] = "N/A" # Fallback
            return ad_data



    def find_competitors(self, product_info: Dict) -> list:
        if not self.api_key:
            print("Warning: OPENROUTER_API_KEY not found.")
            return []
            
        own_brand = product_info.get("brand_name", "").strip().lower()
        
        try:
            result = self.graph.invoke({"product_info": product_info})
            
            if result.get("is_famous"):
                print(f"Brand '{product_info.get('brand_name')}' is famous. Searching directly.")
            
            # Get competitor brands, ensure own brand is excluded
            brands = result.get("competitor_brands", [])
            brands = [b for b in brands if b.lower() != own_brand]
            
            # Build final queue: competitors first
            final_queue = list(dict.fromkeys(brands))  # deduplicate
            
            if not final_queue:
                root_product = product_info.get("root_product", product_info.get("category", ""))
                print(f"No competitors found. Falling back to '{root_product} brands India' search.")
                resolved = self.resolve_brands(f"Top {root_product} brands India")
                final_queue = [b for b in resolved if b.lower() != own_brand]
            
            print(f"Competitor queue (excluding {product_info.get('brand_name')}): {final_queue}")
            return final_queue[:5]
        except Exception as e:
            print(f"Failed to run LangGraph AI discovery: {e}")
            return []

if __name__ == "__main__":
    # Test execution
    test_info = {
        "product_name": "AirFlex Runner",
        "brand_name": "Niche-O-Shoes",
        "category": "Running Shoes",
        "price_range": "₹4,000–₹6,000",
        "description": "High performance breathable mesh shoes for long distance runners.",
        "features": ["Lightweight", "Cushioned sole"]
    }
    finder = AICompetitorFinder()
    print("Running AI Discovery Graph...")
    print(f"Result: {finder.find_competitors(test_info)}")
