import sys
import asyncio
from google.genai import types, Client
from dotenv import load_dotenv

load_dotenv()
client = Client()

async def test():
    with open('veo_err2.txt', 'w', encoding='utf-8') as f:
        f.write("Testing generate_videos with reference images...\n")
        try:
            from PIL import Image
            import io
            img = Image.new('RGB', (100, 100), color = 'red')
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            image_bytes = buf.getvalue()

            ref_img = types.Image(image_bytes=image_bytes, mime_type="image/jpeg")
            
            # Try passing reference_type ASSET
            reference = types.VideoGenerationReferenceImage(image=ref_img, reference_type="ASSET")
            
            config = types.GenerateVideosConfig(
                number_of_videos=1,
                duration_seconds=4,
                aspect_ratio="16:9",
                reference_images=[reference]
            )
            
            operation = client.models.generate_videos(
                model="veo-2.0-generate-001",
                prompt="A red square moving around",
                config=config
            )
            f.write(f"Operation started: {operation.name}\n")
        except Exception as e:
            f.write("Exception:\n")
            f.write(repr(e) + "\n")
            if hasattr(e, 'message'):
                f.write(f"Message: {e.message}\n")

if __name__ == "__main__":
    asyncio.run(test())
