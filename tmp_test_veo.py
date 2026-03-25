import sys
import asyncio
from google.genai import types, Client
from dotenv import load_dotenv

load_dotenv()
client = Client()

async def test():
    print("Testing generate_videos with reference images...")
    try:
        from PIL import Image
        import io
        img = Image.new('RGB', (100, 100), color = 'red')
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        image_bytes = buf.getvalue()

        ref_img = types.Image(image_bytes=image_bytes, mime_type="image/jpeg")
        
        # Let's try without reference_type="ASSET"
        try:
           reference = types.VideoGenerationReferenceImage(image=ref_img, reference_type="REFERENCE_IMAGE_TYPE_UNSPECIFIED")
        except Exception as e:
           print("Error 1:", e)
           reference = types.VideoGenerationReferenceImage(image=ref_img)
        
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
        print("Operation started:", operation.name)
    except Exception as e:
        print("Exception:")
        print(repr(e))
        if hasattr(e, 'message'):
            print("Message:", e.message)

if __name__ == "__main__":
    asyncio.run(test())
