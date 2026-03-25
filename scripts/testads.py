"""
Final Standalone Test Script: Multi-Layer Ad (Veo + Image Overlay + Audio).
- Generates 5s cinematic video via Gemini Veo.
- Overlays poco1.jpg as a product asset via FFmpeg.
- Mixes VO + BGM + SFX.
- One single API call for video.
"""
import asyncio, os, sys, requests, subprocess
from google import genai
from google.genai import types
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Pathing
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

async def generate_test_ad():
    print("🎬 Starting Single-Scene Hybrid Test Ad...")
    
    # 1. Gemini Config
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    model_id = "veo-3.1-generate-preview" 

    # 2. Files
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    image_path = os.path.join(root_dir, "poco1.jpg")
    os.makedirs("agents/video", exist_ok=True)
    temp_video = "agents/video/test_raw.mp4"
    branded_video = "agents/video/test_branded.mp4"
    final_ad = "agents/video/poco_test_ad.mp4"

    # 3. Video Generation (Prompt Only - 100% Reliable)
    prompt = (
        "Cinematic commercial shot of a futuristic smartphone on a dark sleek surface. "
        "Dynamic lighting, lens flares, slow rotation, 4k, photorealistic, high-end product photography."
    )
    print(f"📹 Generating 5s Video via {model_id}...")
    
    try:
        operation = client.models.generate_videos(model=model_id, prompt=prompt)
        while not operation.done:
            print("   ⏳ Rendering video...", end="\r")
            await asyncio.sleep(10)
            operation = client.operations.get(operation)
        
        if operation.error:
            print(f"\n❌ Gemini Error: {operation.error}")
            return
            
        video_uri = operation.result.generated_videos[0].video.uri
        
        # Download
        url = video_uri + (f"&key={api_key}" if '?' in video_uri else f"?key={api_key}")
        resp = requests.get(url)
        with open(temp_video, "wb") as f:
            f.write(resp.content)
        print(f"✅ Raw Video saved: {temp_video}")
    except Exception as e:
        print(f"\n❌ Video generation failed: {e}")
        return

    # 4. Product Overlay (Using poco1.jpg via FFmpeg)
    print(f"🖼️  Overlaying {os.path.basename(image_path)}...")
    try:
        # Scale image to 250px width and place in bottom-right
        cmd = [
            "ffmpeg", "-y", "-i", temp_video, "-i", image_path,
            "-filter_complex", "[1:v]scale=250:-1[prod];[0:v][prod]overlay=W-w-20:H-h-20",
            "-c:a", "copy", branded_video
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Overlay complete: {branded_video}")
    except Exception as e:
        print(f"⚠️ Overlay failed: {e}")
        branded_video = temp_video

    # 5. Audio Pipeline
    print(f"🔊 Generating Audio...")
    VO_TEXT = "The all new POCO. Power. Style. Innovation. Experience the future in your hands today."
    try:
        from agents.production.audio_service import audio_service
        from agents.production.audio_mixer import AudioMixer
        
        vo_path = audio_service.generate_voiceover(VO_TEXT, "English")
        audio_plan = {
            "ad_type": "product_demo",
            "music_style": "modern_product_music",
            "sfx_list": ["whoosh", "shimmer"]
        }
        mixer = AudioMixer(audio_plan, total_duration=5.0)
        mixed_audio = mixer.mix_final_audio(voiceover_path=vo_path)
        
        # 6. Final Merge
        print(f"🎛️  Final Mix & Merge...")
        cmd = [
            "ffmpeg", "-y", "-i", branded_video, "-i", mixed_audio,
            "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", "-shortest",
            final_ad
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"\n🎉 SUCCESS! Final ad: {final_ad}")
    except Exception as e:
        print(f"❌ Audio/Merge failed: {e}")

if __name__ == "__main__":
    asyncio.run(generate_test_ad())
