"""Asset loading mixin for GeminiRenderer.

Handles GridFS asset loading and Veo reference image preparation.
"""
import os
import sys
from typing import Dict, List

from google.genai import types

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from utils.logger import logger


class AssetLoaderMixin:
    """Mixin: loads product/logo/lifestyle assets from GridFS and prepares Veo references."""

    async def _load_assets(self) -> Dict:
        """Loads product images and logo from GridFS based on campaign_id."""
        from api.services.db_mongo_service import get_user_assets
        
        context = self.context if isinstance(self.context, dict) else {}
        campaign_id = context.get("campaign_id") or context.get("_id")
        user_id = context.get("user_id") or context.get("owner_id")
        
        if campaign_id: campaign_id = str(campaign_id)
        if user_id: user_id = str(user_id)
            
        logger.info(f"   Loading assets for campaign: {campaign_id}, user: {user_id}")
        
        loaded = {"product": [], "logo": [], "lifestyle": []}
        
        if not user_id:
            logger.warning("   No user_id found in context. Cannot load assets.")
            return loaded

        try:
            items = await get_user_assets(user_id)
            for item in items:
                metadata = item.get("metadata", {})
                item_campaign_id = metadata.get("campaign_id")
                
                if campaign_id and item_campaign_id and str(item_campaign_id) != str(campaign_id):
                    continue
                
                asset_type = metadata.get("asset_type")
                file_id = str(item["_id"])
                if asset_type in loaded:
                    loaded[asset_type].append(file_id)
        except Exception as e:
            logger.error(f"       Failed to load assets from GridFS: {e}")
            
        logger.info(f"   Assets loaded: {len(loaded['product'])} product, {len(loaded['logo'])} logo")
        return loaded

    async def _load_image_for_veo(self, asset_id: str):
        """Loads an image from GridFS and returns a types.Image."""
        from api.services.db_mongo_service import get_file_from_gridfs
        try:
            image_bytes, metadata = await get_file_from_gridfs(asset_id)
            mime_type = metadata.get("content_type", "image/jpeg")
            return types.Image(image_bytes=image_bytes, mime_type=mime_type)
        except Exception as e:
            logger.error(f"       Failed to load GridFS image {asset_id}: {e}")
            return None

    async def _get_reference_images_for_scene(self, scene: Dict) -> List:
        """Returns Veo reference images based on D2C story arc + multi-avatar support."""
        scene_name = scene.get("scene", "")
        references = []

        # --- Multi-Avatar: Get the correct avatar for THIS scene ---
        scene_avatar = self._get_avatar_for_scene(scene)
        
        custom_avatar_url = None
        if isinstance(scene_avatar, dict):
            custom_avatar_url = scene_avatar.get("custom_image_url") or scene_avatar.get("url")
        
        if custom_avatar_url:
            file_id = None
            if "/files/" in str(custom_avatar_url):
                file_id = str(custom_avatar_url).split("/files/")[-1]
            elif len(str(custom_avatar_url)) >= 24:
                file_id = str(custom_avatar_url)
            
            if file_id:
                img = await self._load_image_for_veo(file_id)
                if img:
                    ref = types.VideoGenerationReferenceImage(
                        image=img,
                        reference_type="ASSET"
                    )
                    references.append(ref)
                    avatar_name = scene_avatar.get("name", scene_avatar.get("role", "avatar"))
                    logger.info(f"       ✅ Using avatar '{avatar_name}' reference for scene '{scene_name}'")
        
        # --- D2C STORY ARC: NO product in Hook/Problem ---
        if scene_name in ("Hook", "Problem", "Relatable Moment", "Stop scroll", "Agitate pain"):
            return references[:3]
        
        # --- Solution/Proof: Product images (the reveal) ---
        elif scene_name in ("Solution", "Proof", "Introduce product", "Show results"):
            for img_path in self.assets["product"][:2]:
                img = await self._load_image_for_veo(img_path)
                if img:
                    ref = types.VideoGenerationReferenceImage(
                        image=img,
                        reference_type="ASSET"
                    )
                    references.append(ref)
        
        # --- Trust/CTA: Logo + product (brand identity) ---
        elif scene_name in ("CTA", "Trust", "Drive action", "Build credibility"):
            for img_path in self.assets["logo"][:1]:
                img = await self._load_image_for_veo(img_path)
                if img:
                    ref = types.VideoGenerationReferenceImage(
                        image=img,
                        reference_type="ASSET"
                    )
                    references.append(ref)
            if self.assets["product"]:
                img = await self._load_image_for_veo(self.assets["product"][0])
                if img:
                    ref = types.VideoGenerationReferenceImage(
                        image=img,
                        reference_type="ASSET"
                    )
                    references.append(ref)
        
        return references[:3]
