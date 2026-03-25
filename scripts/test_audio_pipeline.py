"""
Audio Pipeline Test v3 — Results saved as JSON.
"""
import asyncio, os, sys, json, traceback

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

RESULTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_results.json")

async def test():
    results = {"steps": [], "errors": []}

    STORY = "Yeh phone sirf dikhta nahi perform bhi karta hai POCO M7 5G ab bas aath hazaar mein"
    LANG = "Hindi"
    DUR = 6.0
    audio_plan = {
        "ad_type": "product_demo",
        "voice_type": "confident_narrator",
        "music_style": "modern_product_music",
        "sfx_list": ["whoosh", "pop"],
    }
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agents", "video")
    os.makedirs(out_dir, exist_ok=True)
    final_out = os.path.join(out_dir, "audio_test_final.mp3")

    # Step 1: Voiceover
    vo_path = None
    try:
        from agents.production.audio_service import audio_service
        has_key = bool(audio_service.api_key)
        results["steps"].append({"step": "vo_init", "has_api_key": has_key})
        
        vo_path = audio_service.generate_voiceover(STORY, LANG)
        vo_ok = vo_path and os.path.exists(vo_path)
        results["steps"].append({
            "step": "voiceover",
            "ok": vo_ok,
            "path": vo_path,
            "size_bytes": os.path.getsize(vo_path) if vo_ok else 0
        })
    except Exception as e:
        results["errors"].append({"step": "voiceover", "error": str(e), "tb": traceback.format_exc()})

    # Step 2: Full mix
    mixed = None
    try:
        from agents.production.audio_mixer import AudioMixer
        mixer = AudioMixer(audio_plan, DUR)
        results["steps"].append({
            "step": "mixer_init",
            "has_client": bool(mixer.client),
            "ffmpeg_ok": mixer._ffmpeg_available,
            "duration": mixer.duration,
            "temp_dir": mixer._temp_dir,
            "music_style": audio_plan.get("music_style"),
            "sfx_list": audio_plan.get("sfx_list")
        })

        mixed = mixer.mix_final_audio(voiceover_path=vo_path, output_path=final_out)
        mix_ok = mixed and os.path.exists(mixed)
        results["steps"].append({
            "step": "final_mix",
            "ok": mix_ok,
            "path": mixed,
            "size_bytes": os.path.getsize(mixed) if mix_ok else 0
        })
    except Exception as e:
        results["errors"].append({"step": "mixer", "error": str(e), "tb": traceback.format_exc()})

    # Save
    results["final_output_exists"] = os.path.exists(final_out)
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {RESULTS_FILE}")

if __name__ == "__main__":
    asyncio.run(test())
