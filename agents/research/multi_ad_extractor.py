import os
import time
import json
import random
import hashlib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Legacy MongoDB import removed
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# --- Configuration ---
# HISTORY_FILE is deprecated, using MongoDB fingerprints collection
OUTPUT_FILE = "ads_dna_10_competitors.json"
MAX_UNIQUE_BRANDS = 3
ADS_PER_BRAND = 3 

def get_history(user_id=None):
    """Fetch fingerprints from MongoDB for a specific user."""
    try:
        from pymongo import MongoClient
        load_dotenv()
        mongo_url = os.getenv("MONGODB_URL")
        if not mongo_url:
            return set()
            
        client = MongoClient(mongo_url)
        db = client.get_database("ai_ad_generator")
        collection = db["extraction_fingerprints"]
        
        query = {"user_id": user_id} if user_id else {}
        cursor = collection.find(query, {"fingerprint": 1})
        return {doc["fingerprint"] for doc in cursor}
    except Exception as e:
        print(f"Extraction History: Could not fetch from MongoDB. {e}")
        return set()

def save_history(fingerprints, user_id=None):
    """Save fingerprints to MongoDB with user_id."""
    if not fingerprints:
        return
        
    try:
        from pymongo import MongoClient
        load_dotenv()
        mongo_url = os.getenv("MONGODB_URL")
        if not mongo_url:
            return
            
        client = MongoClient(mongo_url)
        db = client.get_database("ai_ad_generator")
        collection = db["extraction_fingerprints"]
        
        docs = []
        for fp in fingerprints:
            docs.append({
                "user_id": user_id,
                "fingerprint": fp,
                "created_at": datetime.utcnow()
            })
            
        if docs:
            # Use upsert or just insert if we know they are new
            collection.insert_many(docs, ordered=False)
    except Exception as e:
        # Ignore duplicate key errors if fingerprints overlap
        if "duplicate key error" not in str(e).lower():
            print(f"Extraction History: Could not save to MongoDB. {e}")

def find_competitors(driver, company_name):
    print(f"Searching for competitors of: {company_name}...")
    common_competitors = {
        "adidas": ["Nike", "Puma", "Reebok", "Under Armour", "New Balance", "ASICS", "Skechers", "Lululemon", "Fila", "Converse"],
        "nike": ["Adidas", "Puma", "Reebok", "Under Armour", "New Balance"],
        "puma": ["Adidas", "Nike", "Reebok", "Under Armour"]
    }
    
    if company_name.lower() in common_competitors:
        return common_competitors[company_name.lower()]
    
    try:
        driver.get("https://www.google.com/search?q=top+competitors+of+" + company_name)
        time.sleep(3)
        elements = driver.find_elements(By.XPATH, "//h3")
        comps = []
        for el in elements[:5]:
            text = el.text
            if company_name.lower() not in text.lower() and len(text) > 2:
                name = text.split()[0].strip()
                if name.lower() not in [n.lower() for n in comps]:
                    comps.append(name)
        return comps
    except:
        return []

def detect_hook_type(text):
    text = text.lower()
    if "?" in text or "why" in text or "how" in text: return "Question/Curiosity"
    if "stop" in text or "tired of" in text or "hate" in text: return "Negative/Pain-Point"
    if "!" in text or "new" in text or "introducing" in text: return "Announcement"
    if "secret" in text or "trick" in text: return "Secret/Hack"
    return "Direct Statement"

def detect_tone(text):
    text = text.lower()
    if "!" in text and ("free" in text or "now" in text): return "Urgent"
    if "we" in text and "help" in text: return "Empathetic"
    if "expert" in text or "proven" in text: return "Authoritative"
    return "Conversational/Neutral"

def detect_angle(text):
    text = text.lower()
    if "save" in text or "%" in text or "discount" in text: return "Price/Value"
    if "easy" in text or "minutes" in text or "fast" in text: return "Convenience"
    if "quality" in text or "best" in text or "premium" in text: return "Quality"
    return "Benefit-Driven"

def extract_ads_for_brand(driver, brand_name, history, product_context=None):
    from urllib.parse import quote_plus
    print(f"Checking Meta Ads for: {brand_name} {product_context if product_context else ''}...")
    
    # Intelligently combine brand and product context for a targeted search
    search_query = brand_name
    if product_context and product_context.lower() not in ["shop", "general", "product"]:
        search_query = f"{brand_name} {product_context}"
        
    encoded_query = quote_plus(search_query)
    search_url = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&q={encoded_query}&search_type=keyword_unordered"
    driver.get(search_url)
    time.sleep(12) # Increased wait for Meta Ads Library
    
    # Resilient Ad Card Discovery
    ads = []
    try:
        # Facebook constantly changes class names (_8n_0, x1yztbdb, etc.).
        # The most reliable anchor is the 'Library ID:' text present on every ad card.
        library_id_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Library ID:')]")
        for el in library_id_elements:
            try:
                # Crawl up until we find an ancestor that contains 'Sponsored' and isn't the whole page
                curr = el
                valid_card = None
                for _ in range(15):
                    curr = curr.find_element(By.XPATH, "./..")
                    txt = curr.text
                    if txt and "Sponsored" in txt and len(txt) > 100:
                        # Ensure we don't accidentally grab the entire body
                        if "Ads Library" not in txt[:50]:
                            valid_card = curr
                            break
                if valid_card and valid_card not in ads:
                    ads.append(valid_card)
            except:
                continue
    except:
        pass

    if not ads:
        # Extreme fallback
        ads = driver.find_elements(By.XPATH, "//div[contains(@class, 'xh8yej3') or contains(@class, '_8n_0') or contains(@class, '_11k')]")


    records = []
    for ad in ads:
        try:
            text = ad.text.strip()
            if len(text) < 40 or "Ads Library" in text or "Filter" in text:
                continue
            
            fingerprint = hashlib.md5(text.encode('utf-8')).hexdigest()
            if fingerprint in history:
                continue

            # Highly robust advertiser (company) name extraction
            company = brand_name # Default
            page_selectors = [
                "a[role='link'] span",
                "span.x8t966v",
                "h2 span",
                "span[dir='auto']",
                "strong"
            ]
            for selector in page_selectors:
                try:
                    page_el = ad.find_element(By.CSS_SELECTOR, selector)
                    name = page_el.text.strip()
                    # Stricter exclusion for metadata masquerading as names
                    metadata_masquerade = [
                        "active", "inactive", "sponsored", "id:", " ads", " results", 
                        "filter", "meta", "©", "sorry", "trouble", "playing video", 
                        "about ads", "library", "privacy", "terms", "cookies"
                    ]
                    if name and not any(k in name.lower() for k in metadata_masquerade) and len(name) < 50:
                        company = name
                        break
                except:
                    continue
            
            # Smart copy extraction for the 'hook'
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            metadata_keywords = [
                "active", "inactive", "sponsored", "id:", "started running", 
                "library", "filter", "ads", "meta", "©", "about ads", 
                "sorry", "trouble", "playing video", "privacy", "terms", "cookies"
            ]
            
            non_metadata_lines = [l for l in lines if not any(k in l.lower() for k in metadata_keywords) and len(l) > 20]
            
            # The advertiser name usually appears as the first line of the card text
            # We want the first line of REAL copy that isn't the company name or metadata
            possible_hooks = [l for l in non_metadata_lines if l != company and len(l) > 30]
            
            if not possible_hooks:
                # Fallback to any decent line if strict filtering fails
                possible_hooks = [l for l in lines if len(l) > 40 and not any(k in l.lower() for k in ["active", "inactive", "id:"])]
            
            hook = possible_hooks[0] if possible_hooks else "Copy could not be isolated"
            
            # --- Consolidated Schema ---
            records.append({
                "company": company,
                "platform": "Instagram/Facebook",
                "format": "Video/Image",
                "fingerprint": fingerprint, 
                "dna": {
                    "hook": hook,
                    "hook_type": detect_hook_type(hook),
                    "problem": "Detected from context",
                    "solution": "Product benefit implied",
                    "offer": "Yes" if "%" in text or "off" in text.lower() else "No",
                    "cta": "Buy Now" if "buy" in text.lower() else "Learn More",
                    "tone": detect_tone(text),
                    "angle": detect_angle(text),
                    "emoji_usage": any(c in text for c in "🔥😍😎"),
                    "text_length": len(text)
                }
            })
            history.add(fingerprint)
            if len(records) >= ADS_PER_BRAND:
                break
        except:
            continue
    
    return records

def run_extraction(brand_queue, max_unique_brands=MAX_UNIQUE_BRANDS, ads_per_brand=ADS_PER_BRAND, output_file=OUTPUT_FILE, product_context=None, user_id=None):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    history = get_history(user_id)
    initial_history_count = len(history)
    final_data = []
    processed_brands = set()
    
    # Ensure brand_queue is a list
    if isinstance(brand_queue, str):
        brand_queue = [brand_queue]
    else:
        brand_queue = list(brand_queue)

    while len(processed_brands) < max_unique_brands and brand_queue:
        current_brand = brand_queue.pop(0)
        brand_key = current_brand.lower().strip()
        if brand_key in processed_brands:
            continue
            
        brand_ads = extract_ads_for_brand(driver, current_brand, history, product_context)
        
        if brand_ads:
            print(f"Collected ads for {current_brand}")
            final_data.extend(brand_ads)
            processed_brands.add(brand_key)
        
        if len(processed_brands) < max_unique_brands:
            new_comps = find_competitors(driver, current_brand)
            for c in new_comps:
                if c.lower().strip() not in processed_brands:
                    brand_queue.append(c)
        
        if len(brand_queue) > 50:
            brand_queue = brand_queue[:50]

    # Ensure directory for output_file exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2, ensure_ascii=True)
    
    # Save all fingerprints collected in this run to MongoDB
    save_history(history, user_id=user_id) 
    print(f"\nProgress: Collected {len(processed_brands)} unique brands.")
    driver.quit()
    return final_data

def main():
    run_extraction(["adidas"])

if __name__ == "__main__":
    main()
