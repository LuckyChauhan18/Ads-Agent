import os
import uuid
import tempfile
from dotenv import load_dotenv

# ElevenLabs for ultra-realistic, emotively-capable TTS
from elevenlabs.client import ElevenLabs
from elevenlabs import save

load_dotenv()

class ElevenLabsAudioService:
    """Service to generate ultra-realistic text-to-speech using ElevenLabs API."""
    
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if self.api_key:
            self.client = ElevenLabs(api_key=self.api_key)
        else:
            self.client = None
            print("ElevenLabsAudioService: Warning - ELEVENLABS_API_KEY not found in environment.")
        
    def generate_voiceover(self, text: str, language: str = "Hindi", output_path: str = None) -> str:
        """
        Generates TTS audio using ElevenLabs and saves it to a file.
        Returns the path to the saved audio file, or None if failed.
        """
        if not text or not text.strip():
            return None
            
        if not self.client:
            print("ElevenLabsAudioService: Missing API Key. Cannot generate audio.")
            return None
            
        print(f"ElevenLabsAudioService: Generating {language} voiceover for text: '{text[:30]}...'")
        
        # Map languages to ElevenLabs Voice IDs
        # We use high-quality multicultural voices. You can swap these IDs with your custom cloned voices.
        # Format: Voice Name (ID) for reference
        lang_map = {
            "hindi": "EXAVITQu4vr4xnSDxMaL",       # 'Sarah' - smooth, conversational (good for multiple languages)
            "english": "EXAVITQu4vr4xnSDxMaL",    # 'Sarah'
            "urdu": "EXAVITQu4vr4xnSDxMaL",       # 'Sarah'
            # Fallback to a solid narrative voice for other Indian regional languages if needed
            "default": "JBFqnCBsd6RMkjVDRZzb"      # 'George' - warm English/Multilingual
        }
        
        voice_id = lang_map.get(language.lower(), lang_map["default"])
        
        if not output_path:
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"elevenlabs_{uuid.uuid4().hex}.mp3")
            
        try:
            # Use eleven_multilingual_v2 for best cross-language emotive support including Hindi
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )
            
            # The SDK returns a generator, save it to file
            save(audio_generator, output_path)
            
            if os.path.exists(output_path):
                print(f"ElevenLabsAudioService: Successfully generated audio at {output_path}")
                return output_path
                
        except Exception as e:
            print(f"ElevenLabsAudioService Exception: {e}")
            
        return None

# Export instance seamlessly matching the old import name from other files
audio_service = ElevenLabsAudioService()
