import os
import time
from google import genai
from google.genai import types
from PIL import Image
import io
from dotenv import load_dotenv

# Ensure .env is loaded before creating the client
load_dotenv()

from api.services.db_mongo_service import upload_file_to_gridfs

class AIAssistService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
            print("🚀 [LG_DEBUG] AIAssistService: Gemini client initialized successfully.", flush=True)
        else:
            self.client = None
            print("⚠️ [LG_DEBUG] AIAssistService: API key missing!", flush=True)

    async def generate_product_description(self, images: list[bytes], brand_name: str = None, product_name: str = None):
        """Generates a compelling product description using Gemini 1.5 Flash."""
        if not self.client:
            print("AIAssistService: Client not initialized (check API keys)")
            return "AI Service not initialized. Please check your GEMINI_API_KEY."

        prompt = "Analyze the following product image(s). "
        if brand_name:
            prompt += f"The brand name is '{brand_name}'. "
        if product_name:
            prompt += f"The product name is '{product_name}'. "
        
        prompt += ("Provide a compelling and professional product description (approx 80-120 words) "
                   "suitable for a high-converting digital advertisement. Focus on premium quality, "
                   "key benefits, and visual appeal. Return ONLY the description text, "
                   "no preamble, no markdown, no conversational filler.")

        parts = [prompt]
        for img_bytes in images:
            mime_type = "image/jpeg"
            headers = img_bytes[:16]
            if headers.startswith(b'\x89PNG\r\n\x1a\n'):
                mime_type = "image/png"
            elif headers.startswith(b'RIFF') and b'WEBP' in headers:
                mime_type = "image/webp"
            elif headers.startswith(b'GIF8'):
                mime_type = "image/gif"
            
            parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime_type))

        try:
            # Use the synchronous client to avoid aiohttp attribute errors
            # Using models/gemini-2.5-flash which we confirmed works with exact mime types
            response = self.client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=parts
            )
            
            if response and response.text:
                return response.text.strip()
            return "Gemini failed to generate a description."
        except Exception as e:
            print(f"AIAssistService Description Error: {e}", flush=True)
            return f"Error generating description: {str(e)}"

    async def generate_avatars(self, gender: str, style: str, custom_prompt: str = None):
        """Generates a single AI avatar portrait and saves to GridFS."""
        if not self.client:
            print("AIAssistService: Client not initialized (check API keys)")
            return None

        # Decide final prompt
        if custom_prompt and custom_prompt.strip():
            final_prompt = custom_prompt.strip()
            if "photorealistic" not in final_prompt.lower():
                final_prompt += ", photorealistic 4k, studio lighting, clean background, 9:16 vertical."
        else:
            gender_voice = gender if gender.lower() != "auto" else "young Indian person"
            final_prompt = f"A realistic cinematic portrait of a {gender_voice}, {style} style, studio lighting, clean background, 9:16 vertical, photorealistic 4k."
        
        print(f"AIAssistService: Generating avatar with Imagen 4.0. Prompt: '{final_prompt}'")
        
        try:
            response = self.client.models.generate_images(
                model="imagen-4.0-generate-001",
                prompt=final_prompt,
                config={
                    "number_of_images": 1,
                    "output_mime_type": "image/jpeg",
                }
            )
            
            if response and response.generated_images:
                img_data = response.generated_images[0].image.image_bytes
                ts = int(time.time())
                filename = f"avatar_{ts}.jpg"
                
                # Save to GridFS
                file_id = await upload_file_to_gridfs(
                    filename=filename,
                    content=img_data,
                    metadata={"type": "avatar", "gender": gender, "style": style}
                )
                
                print(f"AIAssistService: Successfully saved avatar to GridFS with ID {file_id}")
                return {
                    "id": file_id,
                    "url": f"/files/{file_id}",
                    "prompt": final_prompt,
                    "style": style,
                    "gender": gender
                }
        except Exception as e:
            print(f"AIAssistService Error: {e}")
        
        return None

    async def filter_scene_text(self, scene: dict, language: str = "English") -> dict:
        # ... (unchanged)
        return scene

    async def filter_storyboard_scenes_parallel(self, scenes: list, language: str = "English") -> list:
        # ... (unchanged)
        return scenes

    async def generate_fallback_image(self, prompt: str) -> str:
        """Generates a static fallback scene image using Imagen and saves to GridFS."""
        if not self.client:
            return None

        try:
            response = self.client.models.generate_images(
                model="imagen-4.0-generate-001",
                prompt=f"{prompt}, 9:16 vertical orientation, masterpiece, photorealistic.",
                config={
                    "number_of_images": 1,
                    "output_mime_type": "image/jpeg",
                }
            )
            
            if response and response.generated_images:
                img_data = response.generated_images[0].image.image_bytes
                filename = f"fallback_{int(time.time())}.jpg"
                
                file_id = await upload_file_to_gridfs(
                    filename=filename,
                    content=img_data,
                    metadata={"type": "fallback"}
                )
                return file_id # Now returning the GridFS ID
        except Exception as e:
            print(f"AIAssistService: Fallback Image Error: {e}")
            
        return None

ai_assist_service = AIAssistService()
