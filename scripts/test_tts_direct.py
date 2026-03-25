"""Minimal ElevenLabs TTS test — captures raw error."""
import os, sys, json, traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

RESULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tts_result.json")

def test():
    r = {"steps": []}
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import VoiceSettings
        
        api_key = os.getenv("ELEVENLABS_API_KEY")
        r["steps"].append({"step": "init", "has_key": bool(api_key), "key_prefix": api_key[:8] if api_key else None})
        
        client = ElevenLabs(api_key=api_key)
        r["steps"].append({"step": "client_created", "ok": True})
        
        # Direct TTS call
        text = "Hello, this is a test of the audio pipeline."
        voice_id = "EXAVITQu4vr4xnSDxMaL"  # Sarah
        
        audio_gen = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
            voice_settings=VoiceSettings(
                stability=0.40,
                similarity_boost=0.60,
                style=0.20,
                use_speaker_boost=True
            )
        )
        r["steps"].append({"step": "tts_called", "ok": True, "type": str(type(audio_gen))})
        
        # Save
        out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agents", "video", "tts_test.mp3")
        total = 0
        with open(out, "wb") as f:
            for chunk in audio_gen:
                if chunk:
                    f.write(chunk)
                    total += len(chunk)
        
        r["steps"].append({"step": "saved", "ok": os.path.exists(out), "bytes": total, "path": out})
        
    except Exception as e:
        r["steps"].append({"step": "error", "error": str(e), "type": type(e).__name__, "tb": traceback.format_exc()})
    
    with open(RESULT, "w") as f:
        json.dump(r, f, indent=2)
    print(f"Done -> {RESULT}")

if __name__ == "__main__":
    test()
