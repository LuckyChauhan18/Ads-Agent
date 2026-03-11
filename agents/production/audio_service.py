import os
import uuid
import tempfile
import requests
import json
from google import genai
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
            
    def _phonetic_correction(self, text: str, language: str) -> str:
        """
        Intercepts script text before TTS to correct common pronunciation errors.
        Crucial for Hindi where ElevenLabs struggles with English loan words in Devanagari.
        """
        if language.lower() not in ["hindi", "urdu", "marathi"]:
            return text # Only correct regional Indian languages for now
            
        print(f"ElevenLabsAudioService: Running phonetic LLM correction for {language}...")
        
        prompt = f"""You are an expert pronunciation coach for AI voices.
Your job is to rewrite the given {language} text phonetically so that an English-based Text-to-Speech engine (like ElevenLabs) pronounces it absolutely perfectly.

RULES:
1. Write English loan words in Latin/English script (e.g. if the text says "प्रॉब्लम", change it to "problem").
2. Ensure Devanagari words are written perfectly.
3. Spell out all numbers as words in {language} (e.g. "99" -> "ninyanve").
4. Add commas where natural pauses should happen so the AI breathes correctly.
5. DO NOT change the meaning or the words. ONLY change the spelling/script to fix pronunciation.
6. Return ONLY the rewritten text, with no markdown, quotes, or preambles.

ORIGINAL TEXT:
{text}"""

        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        try:
            if openrouter_key:
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openai/gpt-4o-mini",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1
                    },
                    timeout=15
                )
                if response.status_code == 200:
                    resp_json = response.json()
                    corrected = resp_json['choices'][0]['message']['content'].strip()
                    print(f"  [Original  ]: {text}")
                    print(f"  [Phonetic  ]: {corrected}")
                    return corrected
                    
            elif gemini_key:
                client = genai.Client(api_key=gemini_key)
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt
                )
                corrected = response.text.strip()
                print(f"  [Original  ]: {text}")
                print(f"  [Phonetic  ]: {corrected}")
                return corrected
                
        except Exception as e:
            print(f"ElevenLabsAudioService Phonetic Correction Error: {e}")
            
        # Fallback to original text if API fails
        return text

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
        
        # 1. Phonetic pre-processing
        safe_text = self._phonetic_correction(text, language)
        
        # 2. Map languages to ElevenLabs Voice IDs
        lang_map = {
            "hindi": "EXAVITQu4vr4xnSDxMaL",       # 'Sarah' - smooth, conversational (good for multiple languages)
            "english": "EXAVITQu4vr4xnSDxMaL",    # 'Sarah'
            "urdu": "EXAVITQu4vr4xnSDxMaL",       # 'Sarah'
            "default": "JBFqnCBsd6RMkjVDRZzb"      # 'George' - warm English/Multilingual
        }
        
        voice_id = lang_map.get(language.lower(), lang_map["default"])
        
        if not output_path:
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"elevenlabs_{uuid.uuid4().hex}.mp3")
            
        try:
            # Use eleven_multilingual_v2 for best cross-language emotive support including Hindi
            audio_generator = self.client.text_to_speech.convert(
                text=safe_text,
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

