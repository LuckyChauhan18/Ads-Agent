import json
import os
import glob
import subprocess
import sys

# --- Global Style Config ---
# [GLOBAL_CINEMATIC_STYLE DELETED - Moved to subclasses]

# --- Step 5: Scene-to-Asset Mapping Rules ---
# Each scene has: unique environment, distinct camera shot, product interaction details

# [SCENE_ASSET_RULES DELETED - Moved to subclasses]

class BaseStoryboardBuilder:
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
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
            print("   No lifestyle images found – generating with AI...")
            self._generate_ai_images("lifestyle")
            # Re-scan after generation
            self.available_assets = self._scan_assets()
    
    def _generate_ai_images(self, category):
        """Generates AI images for a missing asset category."""
        user_problem = self.context.get("user_problem_raw", "person using a product")
        brand_voice = self.context.get("brand_voice", "relatable")
        platform = self.context.get("platform", "meta_reels")
        
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
                
                self._create_placeholder_with_prompt(output_path, prompt, category, i+1)
                print(f"     Generated: {os.path.basename(output_path)}")
                
            except Exception as e:
                print(f"     Failed to generate {category} image {i+1}: {e}")
    
    def _create_placeholder_with_prompt(self, output_path, prompt, category, index):
        """Creates a placeholder PNG with generation instructions."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            img = Image.new('RGB', (1080, 1920), color=(30, 30, 40))
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("arial.ttf", 32)
                small_font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
                small_font = font
            
            draw.text((50, 100), f"AI Generated {category.title()} Image", fill=(255, 255, 255), font=font)
            draw.text((50, 200), f"Image #{index}", fill=(180, 180, 180), font=small_font)
            
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
            import struct
            import zlib
            
            def create_minimal_png(path):
                signature = b'\x89PNG\r\n\x1a\n'
                ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
                ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
                ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
                raw = b'\x00\x1e\x1e\x28'
                idat_data = zlib.compress(raw)
                idat_crc = zlib.crc32(b'IDAT' + idat_data)
                idat = struct.pack('>I', len(idat_data)) + b'IDAT' + idat_data + struct.pack('>I', idat_crc)
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
            parts.append(" Easy Return")
        if "customer_reviews" in signals or "reviews" in signals:
            parts.append("Verified Reviews")
        if offer.get("free_shipping"):
            parts.append("Free Shipping")
        if offer.get("cash_on_delivery"):
            parts.append("COD Available")
        
        return " | ".join(parts) if parts else None

    def get_global_cinematic_style(self):
        """Returns the global style descriptive string. Subclasses can override."""
        return "Cinematic lighting, high quality."

    def get_scene_asset_rules(self):
        """Returns the scene asset rules. Subclasses can override this to customize."""
        return {}

    def _bind_assets(self, scene_name, scene_index, template_scene):
        """Bind assets based on template visual hints."""
        visual = (template_scene.get("visual") or "").lower()
        name = scene_name.lower()

        # Default
        asset_categories = ["lifestyle"]

        if "product" in visual or "demo" in visual or "feature" in visual:
            asset_categories = ["product"]
        elif "logo" in visual or "cta" in name:
            asset_categories = ["logo", "product"]
        elif "before" in name or "struggle" in name:
            asset_categories = ["lifestyle"]

        bound_assets = []

        for category in asset_categories:
            files = self.available_assets.get(category, [])
            if files:
                idx = scene_index % len(files)
                selected = files[idx]
                bound_assets.append({
                    "category": category,
                    "file_path": selected,
                    "file_name": os.path.basename(selected)
                })
            else:
                bound_assets.append({
                    "category": category,
                    "file_path": None,
                    "file_name": f"[ADD {category.upper()} IMAGE]"
                })

        return bound_assets

    def build_storyboard(self):
        """Core STEP 5: Builds fully dynamic template-driven storyboard."""
        scenes = self.script.get("scenes", [])
        avatar_profile = self.avatar.get("avatar_profile", {})
        trust_overlay = self._get_trust_overlay()
        cta_text = self.script.get("pattern_used", {}).get("cta", "Learn More")
        
        strategy_data = self.context.get("strategy", {})
        script_planning = strategy_data.get("script_planning", {})
        ad_template = script_planning.get("template", {})
        template_scenes = ad_template.get("scenes", [])
        
        locked_avatars = self.avatar.get("locked_avatars", [])
        if not locked_avatars:
            if self.selected_avatars:
                locked_avatars = self.selected_avatars[:2]
            else:
                locked_avatars = []
        primary_avatar = locked_avatars[0] if locked_avatars else None
        secondary_avatar = locked_avatars[1] if len(locked_avatars) > 1 else None
        
        ad_length = self.context.get("ad_parameters", {}).get("ad_length", 15)
        if ad_length <= 15: max_avatar_scenes = 1
        elif ad_length <= 30: max_avatar_scenes = 2
        elif ad_length <= 45: max_avatar_scenes = 3
        else: max_avatar_scenes = 4
            
        storyboard = []
        avatar_usage_count = 0
        
        for idx, scene_data in enumerate(scenes):
            llm_scene_name = scene_data.get("name", scene_data.get("scene", "Scene"))
            
            # ALWAYS prefer template scene name over LLM-generated name
            template_scene = {}
            if template_scenes and idx < len(template_scenes):
                template_scene = template_scenes[idx]
            
            # Template name is authoritative; LLM name is fallback only
            scene_name = template_scene.get("name", llm_scene_name)
                
            shot_type = "b_roll_lifestyle"
            visual = (template_scene.get("visual") or "").lower()
            scene_lower = scene_name.lower()

            if "product" in visual or "demo" in visual:
                shot_type = "b_roll_product_macro"
            elif "logo" in visual or "cta" in scene_lower:
                shot_type = "logo_endcard"
            elif "person" in visual or "avatar" in visual:
                shot_type = "avatar_talking_head"
            
            if "avatar" in shot_type:
                if avatar_usage_count >= max_avatar_scenes:
                    shot_type = "b_roll_lifestyle"
                else:
                    avatar_usage_count += 1
                    
            current_avatar_url = None
            if "avatar" in shot_type and primary_avatar:
                use_primary = idx == 0 or "cta" in scene_lower
                avatar_obj = primary_avatar if use_primary else (secondary_avatar if secondary_avatar and avatar_usage_count > 2 else primary_avatar)
                current_avatar_url = avatar_obj.get("url") or avatar_obj.get("id") or avatar_obj.get("avatar_id")
                
            text_overlay = None
            if template_scene.get("text_overlay"):
                text_overlay = "TEMPLATE_TEXT_OVERLAY"
            elif "cta" in scene_lower:
                text_overlay = cta_text
            
            bound_assets = self._bind_assets(scene_name, idx, template_scene)
            
            # Use template scene_name (authoritative) to lookup rules
            rules = self.get_scene_asset_rules()
            base_rules = rules.get(scene_name, rules.get("Hook", {}))
            duration = template_scene.get("duration", scene_data.get("duration", 5))
            
            shot = {
                "scene": scene_name,
                "duration": f"{duration}s",
                "voiceover": scene_data.get("voiceover", ""),
                "intent": llm_scene_name,
                "shot_type": shot_type,
                "avatar": {
                    "type": avatar_profile.get("avatar_type", "presenter"),
                    "custom_image_url": current_avatar_url,
                    "locked_identity": True
                } if "avatar" in shot_type else None,
                "assets": bound_assets,
                "text_overlay": text_overlay,
                "realistic_directives": base_rules.get("realistic_directives", "Follow template visual instructions."),
                "visual_style": template_scene.get("visual", ""),
                "rationale": base_rules.get("rationale", "Scene driven by template structure.")
            }
            storyboard.append(shot)
            
        return storyboard

    def generate_output(self):
        """Produces the full STEP 5 output object."""
        storyboard = self.build_storyboard()
        
        return {
            "campaign_id": self.context.get("campaign_id", "unknown"),
            "storyboard_type": "scene_based",
            "global_style": self.get_global_cinematic_style(),
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
