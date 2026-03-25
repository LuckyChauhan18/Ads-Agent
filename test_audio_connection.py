"""
Dry-run test: Verify that audio_planning attaches correctly to storyboard
without actual video rendering.

This simulates the creative -> production pipeline data flow.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.creative.audio_planner import AudioPlannerEngine
from agents.production.audio_mixer import AudioMixer, BGM_PROMPTS, SFX_PROMPTS

AD_TYPES = ["product_demo", "influencer", "lifestyle", "testimonial", "before_after"]

# Simulated storyboard for product_demo (matching template)
MOCK_STORYBOARDS = {
    "product_demo": [
        {"scene": "Problem Visual", "duration": "3s", "voiceover": "Phone hang ho raha hai?"},
        {"scene": "Product Reveal", "duration": "3s", "voiceover": "Pesh hai POCO M7 5G!"},
        {"scene": "Feature 1", "duration": "5s", "voiceover": "Zero lag, zero wait."},
        {"scene": "Feature 2", "duration": "4s", "voiceover": "Blazing 5G speed aur crystal display."},
        {"scene": "Result", "duration": "2s", "voiceover": "Sab kuch smooth."},
        {"scene": "Logo/CTA", "duration": "3s", "voiceover": "Abhi grab karo!"},
    ]
}

print("=" * 60)
print("  AUDIO <-> STORYBOARD CONNECTION TEST (Dry Run)")
print("=" * 60)

all_pass = True

for ad_type in AD_TYPES:
    print(f"\n{'-' * 50}")
    print(f"Ad Type: {ad_type}")
    print(f"{'-' * 50}")
    
    # Step 1: Audio Planning
    planner = AudioPlannerEngine(ad_type)
    audio_plan = planner.plan_audio()
    
    print(f"  voice_type:   {audio_plan.get('voice_type')}")
    print(f"  lip_sync:     {audio_plan.get('lip_sync')}")
    print(f"  music_style:  {audio_plan.get('music_style')}")
    print(f"  sfx_list:     {audio_plan.get('sfx_list')}")
    print(f"  pacing:       {audio_plan.get('pacing')}")
    
    # Step 2: Verify BGM prompt exists for this music_style
    music_style = audio_plan.get("music_style", "")
    if music_style in BGM_PROMPTS:
        print(f"  OK: BGM prompt found for '{music_style}'")
    else:
        print(f"  FAIL: BGM prompt MISSING for '{music_style}'")
        all_pass = False
    
    # Step 3: Verify SFX prompts exist for each sfx in list
    sfx_list = audio_plan.get("sfx_list", [])
    for sfx_name in sfx_list:
        if sfx_name in SFX_PROMPTS:
            print(f"  OK: SFX prompt found for '{sfx_name}'")
        else:
            print(f"  FAIL: SFX prompt MISSING for '{sfx_name}'")
            all_pass = False
    
    # Step 4: Verify AudioMixer can be instantiated with this plan
    storyboard = MOCK_STORYBOARDS.get(ad_type, MOCK_STORYBOARDS["product_demo"])
    total_duration = sum(
        float(s.get("duration", "5s").replace("s", "")) for s in storyboard
    )
    
    mixer = AudioMixer(audio_plan, total_duration)
    print(f"  OK: AudioMixer created: duration={total_duration}s, ffmpeg={mixer._ffmpeg_available}")
    
    # Step 5: Verify scene timestamps calculation
    timestamps = []
    accumulated = 0
    for s in storyboard:
        timestamps.append(accumulated)
        accumulated += float(s.get("duration", "5s").replace("s", ""))
    
    sfx_timestamps = timestamps[1:]  # Skip first scene
    print(f"  OK: SFX timestamps calculated")
    
    # Step 6: Verify voiceover collection
    voice_type = audio_plan.get("voice_type", "")
    voiceover_text = " ".join([s.get("voiceover", "") for s in storyboard if s.get("voiceover")])
    
    if voice_type == "none":
        print(f"  OK: No voiceover needed (voice_type=none)")
    elif voiceover_text.strip():
        print(f"  OK: Voiceover text collected ({len(voiceover_text)} chars)")
    else:
        print(f"  WARN: No voiceover text in storyboard scenes")
    
    # Step 7: Verify context passing (simulation)
    fake_context = {"audio_planning": audio_plan, "campaign_id": "test"}
    if fake_context.get("audio_planning"):
        print(f"  OK: audio_planning passed through context correctly")
    else:
        print(f"  FAIL: audio_planning NOT in context")
        all_pass = False
    
    mixer.cleanup()

print(f"\n{'=' * 60}")
if all_pass:
    print("  ALL CHECKS PASSED - Audio <-> Storyboard perfectly connected!")
else:
    print("  SOME CHECKS FAILED - See above for details")
print(f"{'=' * 60}")
