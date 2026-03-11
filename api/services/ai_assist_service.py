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
        """Generates a compelling product description using OpenRouter LLM."""
        import base64
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage

        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_key:
            return "AI Service not initialized. Please check your OPENROUTER_API_KEY."

        prompt_text = "Analyze the following product image(s). "
        if brand_name:
            prompt_text += f"The brand name is '{brand_name}'. "
        if product_name:
            prompt_text += f"The product name is '{product_name}'. "
        
        prompt_text += ("Provide a compelling and professional product description (approx 80-120 words) "
                   "suitable for a high-converting digital advertisement. Focus on premium quality, "
                   "key benefits, and visual appeal. Return ONLY the description text, "
                   "no preamble, no markdown, no conversational filler.")

        # Build message content with images
        content = [{"type": "text", "text": prompt_text}]
        for img_bytes in images:
            mime_type = "image/jpeg"
            headers = img_bytes[:16]
            if headers.startswith(b'\x89PNG\r\n\x1a\n'):
                mime_type = "image/png"
            elif headers.startswith(b'RIFF') and b'WEBP' in headers:
                mime_type = "image/webp"
            
            b64_data = base64.b64encode(img_bytes).decode("utf-8")
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{b64_data}"}
            })

        try:
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                openai_api_key=openrouter_key,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=0.7,
            )
            response = llm.invoke([HumanMessage(content=content)])
            if response and response.content:
                return response.content.strip()
            return "Failed to generate a description."
        except Exception as e:
            print(f"AIAssistService Description Error: {e}", flush=True)
            return f"Error generating description: {str(e)}"

    async def generate_avatars(self, gender: str, style: str, user_id: str = None, custom_prompt: str = None):
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
                
                # Save to GridFS with user_id in metadata
                file_id = await upload_file_to_gridfs(
                    filename=filename,
                    content=img_data,
                    metadata={
                        "type": "avatar", 
                        "gender": gender, 
                        "style": style,
                        "user_id": user_id
                    }
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
        """Uses LLM to polish and improve a single scene's copy and visual continuity."""
        if not self.client:
            return scene
            
        prompt = f"""
        Polish the following ad scene for better emotional impact and visual clarity.
        TARGET LANGUAGE: {language}
        
        SCENE DATA:
        - Intent: {scene.get('intent')}
        - Voiceover: {scene.get('voiceover')}
        - Visual Continuity: {scene.get('visual_continuity')}
        
        Return a refined version of the voiceover and visual continuity.
        The voiceover should be high-impact, natural, and authentic.
        The visual continuity should be specific and cinematic.
        Keep the response in JSON format: {{"voiceover": "...", "visual_continuity": "..."}}
        """
        
        try:
            import json
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            refined = json.loads(response.text)
            scene["voiceover"] = refined.get("voiceover", scene["voiceover"])
            scene["visual_continuity"] = refined.get("visual_continuity", scene["visual_continuity"])
        except Exception as e:
            print(f"AIAssistService: filter_scene_text error: {e}")
            
        return scene

    async def filter_storyboard_scenes_parallel(self, scenes: list, language: str = "English") -> list:
        """Parallel filters all scenes in a storyboard."""
        import asyncio
        tasks = [self.filter_scene_text(scene, language=language) for scene in scenes]
        return await asyncio.gather(*tasks)

    async def generate_fallback_image(self, prompt: str) -> str:
        """Generates a static fallback scene image using Imagen and saves to GridFS."""
        if not self.client:
            return None

        try:
            response = self.client.models.generate_images(
                model="imagen-4.0-generate-001",
                prompt=f"{prompt}, 9:16 vertical orientation, photorealistic, no text, no captions, no watermarks, no logos, no words, no subtitles, no UI elements.",
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
