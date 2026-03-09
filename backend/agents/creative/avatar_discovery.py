"""
STEP 3.5: HeyGen Avatar Discovery
Fetches and caches HeyGen's available avatars and voices.
Extracts style tags from avatar names for intelligent matching.
"""
import os
import json
import time
import requests
from typing import Dict, List
from dotenv import load_dotenv

# Load .env from root directory (parent of src)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path, override=True)

# Style keywords to extract from avatar names
STYLE_KEYWORDS = {
    "casual": "casual",
    "ugc": "ugc",
    "business": "business",
    "office": "office",
    "sofa": "casual",
    "yoga": "lifestyle",
    "lounge": "casual",
    "nurse": "professional",
    "maintenance": "professional",
    "training": "professional",
    "suit": "formal",
    "blazer": "formal",
    "shirt": "semi_formal",
    "sweater": "casual",
    "t-shirt": "casual",
    "coat": "professional",
    "jacket": "semi_formal",
    "front": None,  # camera angle, not style
    "side": None,
    "sitting": None,
    "standing": None,
    "lying": None,
}

# Voice style keywords
VOICE_STYLE_KEYWORDS = {
    "ugc": "ugc",
    "excited": "excited",
    "lifelike": "lifelike",
    "friendly": "friendly",
    "chill": "calm",
    "mellow": "calm",
    "bold": "confident",
    "expressive": "excited",
    "crisp": "professional",
    "professor": "professional",
    "broadcaster": "professional",
    "radio": "professional",
}

CATALOG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output", "heygen_catalog.json"
)


class AvatarDiscovery:
    """STEP 3.5: Discovers and catalogs available HeyGen avatars and voices.
    
    Fetches HeyGen's library, extracts style tags from names,
    and caches the result locally to avoid repeated API calls.
    """
    
    BASE_URL = "https://api.heygen.com"
    AVATARS_URL = f"{BASE_URL}/v2/avatars"
    VOICES_URL = f"{BASE_URL}/v2/voices"
    
    def __init__(self):
        self.api_key = os.getenv("HEYGEN_API_KEY")
        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def _extract_avatar_style(self, name: str) -> List[str]:
        """Extracts style tags from avatar name."""
        styles = set()
        name_lower = name.lower()
        for keyword, style in STYLE_KEYWORDS.items():
            if keyword in name_lower and style is not None:
                styles.add(style)
        # Default if no style detected
        if not styles:
            styles.add("general")
        return sorted(styles)
    
    def _extract_voice_style(self, name: str) -> List[str]:
        """Extracts style tags from voice name."""
        styles = set()
        name_lower = name.lower()
        for keyword, style in VOICE_STYLE_KEYWORDS.items():
            if keyword in name_lower:
                styles.add(style)
        if not styles:
            styles.add("neutral")
        return sorted(styles)
    
    def _extract_camera_angle(self, name: str) -> str:
        """Extracts camera angle from avatar name."""
        name_lower = name.lower()
        if "front" in name_lower:
            return "front"
        elif "side" in name_lower:
            return "side"
        elif "sitting" in name_lower:
            return "sitting"
        elif "standing" in name_lower:
            return "standing"
        return "front"  # default
    
    def fetch_avatars(self) -> List[Dict]:
        """Fetches all available avatars from HeyGen API."""
        try:
            resp = requests.get(self.AVATARS_URL, headers=self.headers, timeout=15)
            if resp.status_code == 200:
                avatars = resp.json().get("data", {}).get("avatars", [])
                print(f"   Fetched {len(avatars)} avatars from HeyGen")
                return avatars
            else:
                print(f"   Failed to fetch avatars: {resp.status_code}")
                return []
        except Exception as e:
            print(f"   Error fetching avatars: {e}")
            return []
    
    def fetch_voices(self) -> List[Dict]:
        """Fetches all available voices from HeyGen API."""
        try:
            resp = requests.get(self.VOICES_URL, headers=self.headers, timeout=15)
            if resp.status_code == 200:
                voices = resp.json().get("data", {}).get("voices", [])
                print(f"   Fetched {len(voices)} voices from HeyGen")
                return voices
            else:
                print(f"   Failed to fetch voices: {resp.status_code}")
                return []
        except Exception as e:
            print(f"   Error fetching voices: {e}")
            return []
    
    def build_catalog(self, raw_avatars: List[Dict], raw_voices: List[Dict]) -> Dict:
        """Builds a structured catalog from raw HeyGen data."""
        
        # Process avatars — skip custom/unnamed, deduplicate
        seen_ids = set()
        avatars = []
        for a in raw_avatars:
            aid = a.get("avatar_id", "")
            name = a.get("avatar_name", "")
            gender = a.get("gender", "unknown")
            
            # Skip duplicates
            if aid in seen_ids:
                continue
            seen_ids.add(aid)
            
            # Skip premium avatars
            if a.get("premium", False):
                continue
            
            avatars.append({
                "avatar_id": aid,
                "name": name,
                "gender": gender,
                "styles": self._extract_avatar_style(name),
                "camera_angle": self._extract_camera_angle(name),
                "preview_image": a.get("preview_image_url", ""),
            })
        
        # Process voices — English only, deduplicate
        seen_vids = set()
        voices = []
        for v in raw_voices:
            vid = v.get("voice_id", "")
            lang = str(v.get("language", "")).lower()
            name = v.get("name", "").strip()
            
            if vid in seen_vids:
                continue
            seen_vids.add(vid)
            
            # English-only filter
            if "english" not in lang and lang != "en":
                continue
            
            voices.append({
                "voice_id": vid,
                "name": name,
                "gender": v.get("gender", "unknown"),
                "language": v.get("language", ""),
                "styles": self._extract_voice_style(name),
                "support_pause": v.get("support_pause", False),
                "emotion_support": v.get("emotion_support", False),
            })
        
        # Build summary stats
        avatar_genders = {}
        avatar_styles = {}
        for a in avatars:
            g = a["gender"]
            avatar_genders[g] = avatar_genders.get(g, 0) + 1
            for s in a["styles"]:
                avatar_styles[s] = avatar_styles.get(s, 0) + 1
        
        voice_genders = {}
        for v in voices:
            g = v["gender"]
            voice_genders[g] = voice_genders.get(g, 0) + 1
        
        return {
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "summary": {
                "total_avatars": len(avatars),
                "total_voices": len(voices),
                "avatar_genders": avatar_genders,
                "avatar_styles": avatar_styles,
                "voice_genders": voice_genders,
            },
            "avatars": avatars,
            "voices": voices,
        }
    
    def fetch_catalog(self, force_refresh=False) -> Dict:
        """Main entry point: fetches catalog or returns cached version.
        
        Args:
            force_refresh: If True, re-fetches from API even if cache exists.
        """
        # Check cache (valid for 24 hours)
        if not force_refresh and os.path.exists(CATALOG_FILE):
            try:
                with open(CATALOG_FILE, "r") as f:
                    cached = json.load(f)
                fetched_at = cached.get("fetched_at", "")
                if fetched_at:
                    print(f"   Using cached HeyGen catalog (from {fetched_at})")
                    print(f"     {cached['summary']['total_avatars']} avatars, {cached['summary']['total_voices']} voices")
                    return cached
            except Exception:
                pass  # Fall through to fetch
        
        if not self.api_key:
            print("   HEYGEN_API_KEY not found. Cannot fetch catalog.")
            return {"avatars": [], "voices": [], "summary": {}}
        
        print("   Fetching HeyGen avatar/voice catalog...")
        raw_avatars = self.fetch_avatars()
        raw_voices = self.fetch_voices()
        
        catalog = self.build_catalog(raw_avatars, raw_voices)
        
        # Save cache
        os.makedirs(os.path.dirname(CATALOG_FILE), exist_ok=True)
        with open(CATALOG_FILE, "w") as f:
            json.dump(catalog, f, indent=2)
        print(f"   Catalog saved: {catalog['summary']['total_avatars']} avatars, {catalog['summary']['total_voices']} voices")
        
        return catalog
    
    def generate_output(self, force_refresh=False) -> Dict:
        """Pipeline-compatible output method."""
        return self.fetch_catalog(force_refresh)


if __name__ == "__main__":
    discovery = AvatarDiscovery()
    catalog = discovery.fetch_catalog(force_refresh=True)
    print(f"\nCatalog summary:")
    print(json.dumps(catalog["summary"], indent=2))
