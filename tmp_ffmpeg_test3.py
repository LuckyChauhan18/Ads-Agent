import subprocess

video_path = "agents/video/ad_A_1774195707.mp4"
output_path = "agents/video/test_overlay_fixed.mp4"

filter_complex = ""
current_v = "[0:v]"
inputs = ["-y", "-i", video_path]
input_idx = 1

logo_p = "agents/video/dummy_logo.png"
inputs += ["-i", logo_p]

prod_p = "agents/video/dummy_prod.png"
inputs += ["-i", prod_p]

# logo
filter_complex += f"[{input_idx}:v]scale=150:-1[logo];{current_v}[logo]overlay=W-w-20:20[v_l]"
current_v = "[v_l]"
input_idx += 1

# prod
filter_complex += f";[{input_idx}:v]scale=250:-1[prod];{current_v}[prod]overlay=W-w-20:H-h-20[v_p]"
current_v = "[v_p]"
input_idx += 1

# text
font_path = "C\\:/Windows/Fonts/arialbd.ttf"
safe_text = "Test Text Overlay"
filter_complex += f";{current_v}drawtext=text='{safe_text}':fontfile='{font_path}':fontsize=48:fontcolor=white:shadowcolor=black@0.6:shadowx=3:shadowy=3:x=(w-text_w)/2:y=H/4[v_out]"
current_v = "[v_out]"

cmd = ["ffmpeg"] + inputs + ["-filter_complex", filter_complex, "-map", current_v, "-c:v", "libx264", "-pix_fmt", "yuv420p"]
# Map audio if it exists. But we don't know if ad_A_1774195707.mp4 has audio. Let's omit audio mapping for this test or map if exists.
# cmd += ["-c:a", "copy"] # omit for safety
cmd.append(output_path)

print("Command:", " ".join(cmd))
res = subprocess.run(cmd, capture_output=True, text=True)
print("Return code:", res.returncode)
if res.returncode != 0:
    print("Stderr:", res.stderr)
else:
    print("SUCCESS")
