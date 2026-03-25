"""
AudioMixer: Generates BGM + SFX via ElevenLabs and mixes with voiceover using FFmpeg.

Usage:
    mixer = AudioMixer(audio_plan, total_duration=20.0)
    final_audio = mixer.mix_final_audio(voiceover_path, output_path)
"""

import os
import uuid
import tempfile
import subprocess
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


# ── ElevenLabs BGM prompt mappings per music_style ──
BGM_PROMPTS = {
    "modern_product_music": (
        "Modern upbeat electronic background music for a tech product commercial. "
        "Clean synth pads, subtle bass pulse, minimalist and sleek, 120 BPM, "
        "no vocals, suitable for a 15-25 second short-form ad."
    ),
    "light_social_media_music": (
        "Light and energetic background music for a social media video. "
        "Upbeat lo-fi hip hop with soft guitar plucks, gentle drums, positive vibes, "
        "no vocals, suitable for TikTok or Instagram Reels style content."
    ),
    "cinematic_lifestyle_music": (
        "Warm cinematic background music for a lifestyle brand commercial. "
        "Soft piano with ambient strings, golden-hour feel, aspirational and premium, "
        "no vocals, gentle crescendo, suitable for a 20 second ad."
    ),
    "emotional_soft_music": (
        "Soft emotional background music for a testimonial video. "
        "Gentle acoustic guitar with warm pad layers, heartfelt and trustworthy feel, "
        "no vocals, slow tempo, suitable for a customer story ad."
    ),
    "dramatic_transformation_music": (
        "Dramatic transformation background music for a before-and-after ad. "
        "Starts dark and tense with low rumble, then transitions to bright uplifting "
        "orchestral swell at the midpoint, no vocals, cinematic impact."
    ),
    "generic_background_music": (
        "Clean corporate background music for a video advertisement. "
        "Moderate tempo, neutral mood, professional feel, no vocals."
    )
}

# ── ElevenLabs SFX prompt mappings ──
SFX_PROMPTS = {
    "click": "Single clean digital button click sound effect, crisp and short",
    "swipe": "Smooth UI swipe sound effect, soft whoosh with digital feel",
    "pop": "Bright subtle pop notification sound effect, clean and pleasant",
    "whoosh": "Cinematic whoosh transition sound effect, smooth and fast",
    "transition_whoosh": "Fast cinematic transition whoosh with slight reverb tail",
    "subtle_pop": "Very subtle soft pop sound effect, gentle and minimal",
    "sparkle": "Magical sparkle shimmer sound effect, bright and uplifting",
    "impact": "Deep cinematic impact hit sound effect, dramatic bass thud",
    "ambient_environment": "Gentle outdoor ambient sound, birds chirping softly with distant traffic, natural and calm"
}


class AudioMixer:
    """
    Generates background music and SFX via ElevenLabs,
    then mixes all audio layers (voiceover + BGM + SFX) via FFmpeg.
    """

    def __init__(self, audio_plan: Dict, total_duration: float = 20.0):
        """
        Args:
            audio_plan: Output from AudioPlannerEngine.plan_audio()
            total_duration: Total video duration in seconds
        """
        self.plan = audio_plan
        self.duration = total_duration
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self._client = None
        self._temp_dir = tempfile.mkdtemp(prefix="audio_mix_")
        self._ffmpeg_available = self._check_ffmpeg()

    @property
    def client(self):
        if self._client is None and self.api_key:
            from elevenlabs import ElevenLabs
            self._client = ElevenLabs(api_key=self.api_key)
        return self._client

    @staticmethod
    def _check_ffmpeg() -> bool:
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return True
        except Exception:
            return False

    def _generate_sound_effect(self, prompt: str, duration: float = None, output_name: str = "sfx") -> Optional[str]:
        """Generate a sound effect using ElevenLabs text_to_sound_effects API."""
        if not self.client:
            print(f"  AudioMixer: No ElevenLabs client available, skipping SFX: {output_name}")
            return None

        try:
            print(f"  AudioMixer: Generating '{output_name}' via ElevenLabs SFX API...")

            kwargs = {"text": prompt}
            if duration and duration > 0:
                kwargs["duration_seconds"] = min(duration, 22.0)  # ElevenLabs max ~22s

            audio_generator = self.client.text_to_sound_effects.convert(**kwargs)

            output_path = os.path.join(self._temp_dir, f"{output_name}_{uuid.uuid4().hex[:8]}.mp3")
            with open(output_path, "wb") as f:
                for chunk in audio_generator:
                    if chunk:
                        f.write(chunk)

            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"  AudioMixer: Generated '{output_name}' -> {os.path.basename(output_path)}")
                return output_path
            else:
                print(f"  AudioMixer: SFX file empty for '{output_name}'")
                return None

        except Exception as e:
            print(f"  AudioMixer: SFX generation failed for '{output_name}': {e}")
            return None

    def generate_bgm(self) -> Optional[str]:
        """Generate background music track based on music_style from audio plan."""
        music_style = self.plan.get("music_style", "generic_background_music")
        prompt = BGM_PROMPTS.get(music_style, BGM_PROMPTS["generic_background_music"])

        # ElevenLabs SFX API max is ~22s. For longer ads, we generate and loop.
        gen_duration = min(self.duration, 22.0)
        bgm_path = self._generate_sound_effect(prompt, duration=gen_duration, output_name=f"bgm_{music_style}")

        if not bgm_path:
            return None

        # If video is longer than generated BGM, loop it
        if self.duration > 22.0 and self._ffmpeg_available:
            looped_path = os.path.join(self._temp_dir, f"bgm_looped_{uuid.uuid4().hex[:8]}.mp3")
            loop_cmd = [
                "ffmpeg", "-y",
                "-stream_loop", "-1",
                "-i", bgm_path,
                "-t", str(self.duration),
                "-c:a", "libmp3lame", "-b:a", "128k",
                looped_path
            ]
            result = subprocess.run(loop_cmd, capture_output=True, text=True)
            if result.returncode == 0 and os.path.exists(looped_path):
                bgm_path = looped_path

        return bgm_path

    def generate_sfx(self, scene_timestamps: List[float] = None) -> List[Dict]:
        """Generate SFX clips based on audio plan's sfx_list.
        
        Returns list of {"path": str, "timestamp": float} dicts.
        """
        sfx_list = self.plan.get("sfx_list", [])
        if not sfx_list:
            return []

        generated_sfx = []

        # Calculate even timestamps if not provided
        if not scene_timestamps:
            num_sfx = len(sfx_list)
            scene_timestamps = [i * (self.duration / (num_sfx + 1)) for i in range(1, num_sfx + 1)]

        for idx, sfx_name in enumerate(sfx_list):
            prompt = SFX_PROMPTS.get(sfx_name, f"Short {sfx_name} sound effect, clean and crisp")
            sfx_path = self._generate_sound_effect(prompt, duration=2.0, output_name=f"sfx_{sfx_name}")

            if sfx_path:
                timestamp = scene_timestamps[idx] if idx < len(scene_timestamps) else 0
                generated_sfx.append({
                    "path": sfx_path,
                    "timestamp": timestamp,
                    "name": sfx_name
                })

        return generated_sfx

    def mix_final_audio(
        self,
        voiceover_path: Optional[str] = None,
        output_path: Optional[str] = None,
        scene_timestamps: List[float] = None
    ) -> Optional[str]:
        """
        Mix all audio layers into a final track:
        1. Voiceover (if exists)
        2. Background music (volume reduced)
        3. SFX at scene transitions
        
        Returns path to final mixed audio file.
        """
        if not self._ffmpeg_available:
            print("  AudioMixer: FFmpeg not available, cannot mix audio")
            return voiceover_path  # Return voiceover as-is

        if not output_path:
            output_path = os.path.join(self._temp_dir, f"final_mix_{uuid.uuid4().hex[:8]}.mp3")

        # Step 1: Generate BGM
        print("  AudioMixer: Step 1 - Generating background music...")
        bgm_path = self.generate_bgm()

        # Step 2: Generate SFX
        print("  AudioMixer: Step 2 - Generating sound effects...")
        sfx_clips = self.generate_sfx(scene_timestamps)

        # Step 3: Mix all layers via FFmpeg
        print("  AudioMixer: Step 3 - Mixing audio layers...")

        has_voiceover = voiceover_path and os.path.exists(voiceover_path)
        has_bgm = bgm_path and os.path.exists(bgm_path)
        has_sfx = len(sfx_clips) > 0

        # If nothing to mix, return voiceover as-is
        if not has_bgm and not has_sfx:
            print("  AudioMixer: No BGM or SFX generated, returning voiceover only")
            return voiceover_path

        # Build FFmpeg command for mixing
        inputs = []
        filter_parts = []
        input_idx = 0

        # Input 0: Voiceover (if exists) or silent track
        if has_voiceover:
            inputs += ["-i", voiceover_path]
            filter_parts.append(f"[{input_idx}:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=1.0[vo]")
            input_idx += 1
        else:
            # Generate silence for the duration
            inputs += ["-f", "lavfi", "-t", str(self.duration), "-i", "anullsrc=r=44100:cl=stereo"]
            filter_parts.append(f"[{input_idx}:a]volume=0[vo]")
            input_idx += 1

        # Input 1: BGM (reduced volume)
        if has_bgm:
            inputs += ["-i", bgm_path]
            # Trim BGM to match duration and reduce volume
            bgm_volume = "0.15" if has_voiceover else "0.4"
            filter_parts.append(
                f"[{input_idx}:a]aformat=sample_rates=44100:channel_layouts=stereo,"
                f"atrim=0:{self.duration},asetpts=PTS-STARTPTS,"
                f"volume={bgm_volume}[bgm]"
            )
            input_idx += 1

        # Input N: SFX clips
        sfx_labels = []
        for sfx in sfx_clips:
            if os.path.exists(sfx["path"]):
                inputs += ["-i", sfx["path"]]
                delay_ms = int(sfx["timestamp"] * 1000)
                label = f"sfx{input_idx}"
                filter_parts.append(
                    f"[{input_idx}:a]aformat=sample_rates=44100:channel_layouts=stereo,"
                    f"volume=0.6,adelay={delay_ms}|{delay_ms},"
                    f"apad=whole_dur={self.duration}[{label}]"
                )
                sfx_labels.append(f"[{label}]")
                input_idx += 1

        # Build the mix filter
        mix_inputs = "[vo]"
        mix_count = 1
        
        if has_bgm:
            mix_inputs += "[bgm]"
            mix_count += 1
        
        for label in sfx_labels:
            mix_inputs += label
            mix_count += 1

        filter_parts.append(
            f"{mix_inputs}amix=inputs={mix_count}:duration=first:dropout_transition=2[out]"
        )

        filter_complex = ";".join(filter_parts)

        cmd = ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-c:a", "libmp3lame", "-b:a", "192k",
            "-t", str(self.duration),
            output_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and os.path.exists(output_path):
                print(f"  AudioMixer: ✅ Final mix complete -> {os.path.basename(output_path)}")
                return output_path
            else:
                print(f"  AudioMixer: ❌ FFmpeg mix failed: {result.stderr[:300]}")
                return voiceover_path if has_voiceover else bgm_path
        except Exception as e:
            print(f"  AudioMixer: ❌ Mix error: {e}")
            return voiceover_path if has_voiceover else bgm_path

    def cleanup(self):
        """Remove temporary audio files."""
        import shutil
        try:
            if os.path.exists(self._temp_dir):
                shutil.rmtree(self._temp_dir)
        except Exception:
            pass
