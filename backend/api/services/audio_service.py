import os
import requests
import base64
import uuid
import tempfile
from dotenv import load_dotenv

load_dotenv()

class SarvamAudioService:
    """Service to generate authentic Indian text-to-speech using Sarvam AI."""
    
    def __init__(self):
        self.api_key = os.getenv("SARVAM_API_KEY")
        self.base_url = "https://api.sarvam.ai/text-to-speech"
        
    def generate_voiceover(self, text: str, language: str = "Hindi", output_path: str = None) -> str:
        """
        Generates TTS audio and saves it to a file.
        Returns the path to the saved audio file, or None if failed.
        """
        if not text or not text.strip():
            return None
            
        if not self.api_key:
            print("SarvamAudioService: Missing SARVAM_API_KEY. Skipping TTS generation.")
            return None
            
        print(f"SarvamAudioService: Generating {language} voiceover for text: '{text[:30]}...'")
        
        # Map languages to Sarvam codes
        lang_map = {
            "hindi": "hi-IN",
            "english": "en-IN", # Indian English
            "bengali": "bn-IN",
            "tamil": "ta-IN",
            "telugu": "te-IN",
            "marathi": "mr-IN",
            "gujarati": "gu-IN",
            "kannada": "kn-IN",
            "malayalam": "ml-IN"
        }
        
        target_lang = lang_map.get(language.lower(), "hi-IN")
        
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": [text[:500]], # Sarvam typically constraints input length
            "target_language_code": target_lang,
            "speaker": "anushka", # Valid Sarvam AI female voice
            "pitch": 0,
            "pace": 1.0,
            "loudness": 1.5,
            "speech_sample_rate": 24000,
            "enable_preprocessing": True,
            "model": "bulbul:v2"
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                resp_data = response.json()
                audios = resp_data.get("audios", [])
                
                if audios and len(audios) > 0:
                    base64_audio = audios[0]
                    audio_bytes = base64.b64decode(base64_audio)
                    
                    if not output_path:
                        temp_dir = tempfile.gettempdir()
                        output_path = os.path.join(temp_dir, f"sarvam_tts_{uuid.uuid4().hex}.wav")
                        
                    with open(output_path, "wb") as f:
                        f.write(audio_bytes)
                        
                    print(f"SarvamAudioService: Successfully generated audio at {output_path}")
                    return output_path
                else:
                    print("SarvamAudioService: API returned success but no audio array.")
            else:
                print(f"SarvamAudioService Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"SarvamAudioService Exception: {e}")
            
        return None

audio_service = SarvamAudioService()
