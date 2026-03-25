import subprocess
import os

video_path = "agents/video/ad_A_1774195707.mp4"
output_path = "agents/video/test_overlay.mp4"

filter_complex = "[0:v]"
inputs = ["-i", video_path]

logo_p = "agents/video/dummy_logo.png"
if not os.path.exists(logo_p):
    from PIL import Image
    img = Image.new('RGBA', (150, 50), color = (255, 0, 0, 128))
    img.save(logo_p)

prod_p = "agents/video/dummy_prod.png"
if not os.path.exists(prod_p):
    from PIL import Image
    img = Image.new('RGBA', (250, 250), color = (0, 255, 0, 128))
    img.save(prod_p)

input_idx = 1
inputs += ["-i", logo_p]
filter_complex += f"[{input_idx}:v]scale=150:-1[logo];{filter_complex}[logo]overlay=W-w-20:20[v_l]"
filter_complex = "[v_l]"
input_idx += 1

inputs += ["-i", prod_p]
filter_complex += f"[{input_idx}:v]scale=250:-1[prod];{filter_complex}[prod]overlay=W-w-20:H-h-20[v_p]"
filter_complex = "[v_p]"
input_idx += 1

safe_text = "Test Text Overlay"
font_path = "C\\:/Windows/Fonts/arialbd.ttf"
filter_complex += f",drawtext=text='{safe_text}':fontfile='{font_path}':fontsize=48:fontcolor=white:shadowcolor=black@0.6:shadowx=3:shadowy=3:x=(w-text_w)/2:y=H/4"

cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", filter_complex, "-c:a", "copy", output_path]

with open("ffmpeg_output.txt", "w", encoding="utf-8") as f:
    f.write("Running command: " + " ".join(cmd) + "\n")
    res = subprocess.run(cmd, capture_output=True, text=True)
    f.write(f"Return code: {res.returncode}\n")
    f.write(f"Stdout:\n{res.stdout}\n")
    f.write(f"Stderr:\n{res.stderr}\n")
