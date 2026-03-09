import json
import os
import glob
import subprocess
import sys

# --- Step 5: Scene-to-Asset Mapping Rules ---

SCENE_ASSET_RULES = {
    "Hook": {
        "shot_type": "avatar_talking_head",
        "asset_categories": [],
        "text_overlay": None,
        "realistic_directives": "Dynamic zoom-in, natural micro-expressions, evolving background lighting (warm to cool transition), 4K photorealism.",
        "rationale": "Clean hook — no distractions, just avatar + copy"
    },
    "Problem": {
        "shot_type": "avatar_talking_head",
        "asset_categories": ["lifestyle"],
        "text_overlay": None,
        "realistic_directives": "Push-in camera movement, shifting environment shadows, high-contrast cinematic lighting, authentic emotional journey.",
        "rationale": "Avatar main, optional lifestyle B-roll for empathy"
    },
    "Relatable Moment": {
        "shot_type": "avatar_talking_head",
        "asset_categories": ["lifestyle"],
        "text_overlay": None,
        "realistic_directives": "Active handheld sway, environment change (indoor to outdoor transition), soft focus transitions, vibrant and alive colors.",
        "rationale": "Mirror user experience, lifestyle imagery supports connection"
    },
    "Solution": {
        "shot_type": "avatar_with_product",
        "asset_categories": ["product"],
        "text_overlay": None,
        "realistic_directives": "360-degree product orbit, slow-motion splash/particle effects, dramatic lighting shift, hyper-realistic metallic/fabric textures.",
        "rationale": "Product reveal — show the solution visually"
    },
    "Trust": {
        "shot_type": "avatar_with_badges",
        "asset_categories": ["logo"],
        "text_overlay": None,
        "realistic_directives": "Floating holographic UI elements, depth-of-field shift, clean minimalist environment that evolves with the narrative.",
        "rationale": "Trust badges + review indicators on screen"
    },
    "Proof": {
        "shot_type": "avatar_with_badges",
        "asset_categories": ["product", "logo"],
        "text_overlay": None,
        "realistic_directives": "Dynamic parallax movement, layered textures, environmental elements react to product presence, premium aesthetic.",
        "rationale": "Social proof with product visibility"
    },
    "CTA": {
        "shot_type": "avatar_with_cta",
        "asset_categories": ["logo"],
        "text_overlay": None,
        "realistic_directives": "Soft zoom-out, final environment transformation (gold/sunset glow), high-energy delivery, sharp terminal focus.",
        "rationale": "Logo + CTA button/text, clean ending"
    }

}

# Duration estimates per scene (adjusted to ~8.5s for 48s total after fades)
SCENE_DURATION = {
    "Hook": "8.5s",
    "Problem": "8s",
    "Relatable Moment": "8s",
    "Solution": "8.5s",
    "Trust": "7.5s",
    "Proof": "7.5s",
    "CTA": "8s"
}



class StoryboardBuilder:
    """STEP 5: Converts avatar + script into a shot-by-shot storyboard
    and binds real assets (images, logos, product shots) to each scene.
    
    STEP 4 = who + how
    STEP 5 = what appears on screen at each second
    
    This step does NOT change script or avatar decisions.
    """
    
    def __init__(self, script_output, avatar_config, campaign_context, assets_dir=None):
        """
        Args:
            script_output: Output from Step 3
            avatar_config: Output from Step 4
            campaign_context: Output from Step 1
            assets_dir: Path to the assets directory (default: project_root/assets)
        """
        self.script = script_output
        self.avatar = avatar_config
        self.context = campaign_context  
        
        # Get selected avatars array (plural support)
        self.selected_avatars = self.avatar.get("selected_avatars", [])
        
        # Robust URL extraction: if results is a list, treat as selected_avatars
        if not self.selected_avatars and isinstance(self.avatar.get("results"), list):
            self.selected_avatars = self.avatar["results"]

        # Fallback to legacy single avatar if plural missing
        if not self.selected_avatars:
            url = self.avatar.get("url") or self.avatar.get("custom_avatar_url") or self.avatar.get("id")
            if url:
                self.selected_avatars = [{"url": url}]
        
        # Resolve assets directory
        if assets_dir:
            self.assets_dir = assets_dir
        else:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            campaign_id = self.context.get("campaign_id") if isinstance(self.context, dict) else None
            
            base_assets_dir = os.path.join(base, "assets")
            self.assets_dir = os.path.join(base_assets_dir, campaign_id) if campaign_id else base_assets_dir
            
            if not os.path.exists(self.assets_dir):
                self.assets_dir = base_assets_dir
        
        # Scan real assets, auto-generate missing ones
        self.available_assets = self._scan_assets()
        self._auto_generate_missing()
    
    def _scan_assets(self):
        """Scans the assets directory for real files."""
        assets = {
            "product": [],
            "lifestyle": [],
            "logo": []
        }
        
        image_exts = ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.gif", "*.svg")
        
        for category in assets:
            category_dir = os.path.join(self.assets_dir, category)
            if os.path.exists(category_dir):
                for ext in image_exts:
                    found = glob.glob(os.path.join(category_dir, ext))
                    assets[category].extend(found)
        
        return assets
    
    def _auto_generate_missing(self):
        """Auto-generates missing lifestyle images using AI when none are provided."""
        if not self.available_assets["lifestyle"]:
            print("   No lifestyle images found  generating with AI...")
            self._generate_ai_images("lifestyle")
            # Re-scan after generation
            self.available_assets = self._scan_assets()
    
    def _generate_ai_images(self, category):
        """Generates AI images for a missing asset category."""
        user_problem = self.context.get("user_problem_raw", "person using a product")
        brand_voice = self.context.get("brand_voice", "relatable")
        platform = self.context.get("platform", "meta_reels")
        
        # Build context-aware prompts based on category
        prompts = {
            "lifestyle": [
                f"A realistic photo of a young person (22-35) experiencing discomfort while running outdoors. "
                f"Natural lighting, candid UGC style, mobile phone quality. "
                f"Context: {user_problem}. "
                f"9:16 vertical format for {platform}. No text or logos.",
                
                f"A realistic lifestyle photo of a young runner (22-35) stretching or preparing for a run "
                f"in a park or urban setting. Warm natural light, authentic and {brand_voice} mood. "
                f"9:16 vertical format. No text or logos."
            ]
        }
        
        category_prompts = prompts.get(category, [])
        category_dir = os.path.join(self.assets_dir, category)
        os.makedirs(category_dir, exist_ok=True)
        
        for i, prompt in enumerate(category_prompts):
            output_path = os.path.join(category_dir, f"ai_generated_{category}_{i+1}.png")
            
            if os.path.exists(output_path):
                print(f"     Already exists: {os.path.basename(output_path)}")
                continue
            
            try:
                # Save the prompt as a text file for reference
                prompt_file = os.path.join(category_dir, f"ai_generated_{category}_{i+1}_prompt.txt")
                with open(prompt_file, "w") as f:
                    f.write(prompt)
                
                # Create a placeholder image with the prompt embedded
                # (The actual AI generation happens via external tools/APIs)
                self._create_placeholder_with_prompt(output_path, prompt, category, i+1)
                print(f"     Generated: {os.path.basename(output_path)}")
                
            except Exception as e:
                print(f"     Failed to generate {category} image {i+1}: {e}")
    
    def _create_placeholder_with_prompt(self, output_path, prompt, category, index):
        """Creates a placeholder PNG with generation instructions.
        
        This creates a simple image file that the storyboard can reference.
        For production, replace this with actual AI image generation (DALL-E, Midjourney, etc.)
        """
        try:
            # Try to use PIL if available for a proper placeholder
            from PIL import Image, ImageDraw, ImageFont
            
            img = Image.new('RGB', (1080, 1920), color=(30, 30, 40))
            draw = ImageDraw.Draw(img)
            
            # Add text
            try:
                font = ImageFont.truetype("arial.ttf", 32)
                small_font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
                small_font = font
            
            draw.text((50, 100), f"AI Generated {category.title()} Image", fill=(255, 255, 255), font=font)
            draw.text((50, 200), f"Image #{index}", fill=(180, 180, 180), font=small_font)
            
            # Word-wrap the prompt
            words = prompt.split()
            lines = []
            current = ""
            for w in words:
                if len(current + w) < 45:
                    current += w + " "
                else:
                    lines.append(current.strip())
                    current = w + " "
            if current:
                lines.append(current.strip())
            
            y = 350
            draw.text((50, 300), "Prompt:", fill=(100, 200, 255), font=small_font)
            for line in lines[:15]:
                draw.text((50, y), line, fill=(200, 200, 200), font=small_font)
                y += 30
            
            img.save(output_path)
            
        except ImportError:
            # Fallback: create a minimal valid PNG without PIL
            # This is a 1x1 pixel PNG — enough for the storyboard to reference
            import struct
            import zlib
            
            def create_minimal_png(path):
                signature = b'\x89PNG\r\n\x1a\n'
                # IHDR
                ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
                ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
                ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
                # IDAT
                raw = b'\x00\x1e\x1e\x28'  # filter + dark pixel
                idat_data = zlib.compress(raw)
                idat_crc = zlib.crc32(b'IDAT' + idat_data)
                idat = struct.pack('>I', len(idat_data)) + b'IDAT' + idat_data + struct.pack('>I', idat_crc)
                # IEND
                iend_crc = zlib.crc32(b'IEND')
                iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
                
                with open(path, 'wb') as f:
                    f.write(signature + ihdr + idat + iend)
            
            create_minimal_png(output_path)
    
    def _get_trust_overlay(self):
        """Generates trust text overlay from campaign context."""
        signals = self.context.get("trust_signals", [])
        offer = self.context.get("offer", {})
        
        parts = []
        if "7_day_return" in signals or "easy_return" in signals:
            days = offer.get("return_days", 7)
            parts.append(f"{days}-Day Easy Return")
        if "customer_reviews" in signals or "reviews" in signals:
            parts.append("Verified Reviews")
        if offer.get("free_shipping"):
            parts.append("Free Shipping")
        if offer.get("cash_on_delivery"):
            parts.append("COD Available")
        
        return " | ".join(parts) if parts else None
    
    def _bind_assets(self, scene_name, scene_index=0):
        """Binds real asset files to a scene based on rules.
        Uses a rotation logic to ensure all available assets are used across scenes.
        """
        rules = SCENE_ASSET_RULES.get(scene_name, SCENE_ASSET_RULES["Hook"])
        bound_assets = []
        
        for category in rules["asset_categories"]:
            files = self.available_assets.get(category, [])
            if files:
                # Rotation logic: Pick asset based on scene index and category
                # This ensures if we have 3 images and 6 scenes, each image is used twice
                asset_index = (scene_index) % len(files)
                selected_file = files[asset_index]
                
                bound_assets.append({
                    "category": category,
                    "file_path": selected_file,
                    "file_name": os.path.basename(selected_file)
                })
            else:
                bound_assets.append({
                    "category": category,
                    "file_path": None,
                    "file_name": f"[PLACEHOLDER: add {category} image to assets/{category}/]"
                })
        
        return bound_assets
    
    def build_storyboard(self):
        """Core STEP 5: Builds scene-by-scene storyboard with asset binding and avatar rotation."""
        scenes = self.script.get("scenes", [])
        avatar_profile = self.avatar.get("avatar_profile", {})
        trust_overlay = self._get_trust_overlay()
        cta_text = self.script.get("pattern_used", {}).get("cta", "Learn More")
        
        storyboard = []
        
        for idx, scene_data in enumerate(scenes):
            scene_name = scene_data["scene"]
            rules = SCENE_ASSET_RULES.get(scene_name, SCENE_ASSET_RULES["Hook"])
            
            # Rotation logic: Pick avatar based on scene index (Round Robin)
            current_avatar_url = None
            if self.selected_avatars:
                avatar_obj = self.selected_avatars[idx % len(self.selected_avatars)]
                current_avatar_url = avatar_obj.get("url") or avatar_obj.get("id")
                print(f"   [Storyboard] Scene {idx}: Binding avatar {current_avatar_url} (Selection count: {len(self.selected_avatars)})")
            
            # Determine text overlay per scene
            text_overlay = trust_overlay if scene_name == "Trust" else (cta_text if scene_name == "CTA" else None)
            
            # Bind real assets (rotating through available ones)
            bound_assets = self._bind_assets(scene_name, scene_index=idx)
            
            shot = {
                "scene": scene_name,
                "duration": SCENE_DURATION.get(scene_name, "8s"),
                "voiceover": scene_data["voiceover"],
                "intent": scene_data.get("intent", ""),
                "shot_type": rules["shot_type"],
                "avatar": {
                    "type": avatar_profile.get("avatar_type", "presenter"),
                    "camera": avatar_profile.get("camera_style", "studio"),
                    "expression": avatar_profile.get("facial_expression", "neutral"),
                    "energy": avatar_profile.get("delivery_energy", "balanced"),
                    "pace": avatar_profile.get("speaking_pace", "normal"),
                    "custom_image_url": current_avatar_url
                },
                "assets": bound_assets,
                "text_overlay": text_overlay,
                "realistic_directives": rules.get("realistic_directives"),
                "visual_continuity": scene_data.get("visual_continuity", ""),
                "rationale": rules["rationale"]
            }
            
            storyboard.append(shot)
        
        return storyboard
    
    def generate_output(self):
        """Produces the full STEP 5 output object."""
        storyboard = self.build_storyboard()
        
        return {
            "campaign_id": self.context.get("campaign_id", "unknown"),
            "storyboard_type": "scene_based",
            "platform": self.context.get("platform", "meta_reels"),
            "aspect_ratio": "9:16",
            "total_scenes": len(storyboard),
            "estimated_duration": "15-20s",
            "assets_summary": {
                "product_images": len(self.available_assets["product"]),
                "lifestyle_images": len(self.available_assets["lifestyle"]),
                "logo_files": len(self.available_assets["logo"])
            },
            "storyboard": storyboard
        }


if __name__ == "__main__":
    # Test with local files
    script_path = os.path.join("output", "script_output.json")
    avatar_path = os.path.join("output", "avatar_config.json")
    ctx_path = os.path.join("output", "campaign_psychology.json")
    
    if all(os.path.exists(p) for p in [script_path, avatar_path, ctx_path]):
        with open(script_path, "r") as f:
            script_data = json.load(f)
        with open(avatar_path, "r") as f:
            avatar_data = json.load(f)
        with open(ctx_path, "r") as f:
            ctx_data = json.load(f)
        
        builder = StoryboardBuilder(script_data, avatar_data, ctx_data)
        output = builder.generate_output()
        print(json.dumps(output, indent=2))
    else:
        print("Missing required files in output/")
