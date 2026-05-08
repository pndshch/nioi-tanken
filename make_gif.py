#!/usr/bin/env python3
"""Generate the hub-card GIF for nioi-tanken using Chrome headless + PIL."""
import subprocess, os, time, shutil
from PIL import Image

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
URL = "http://127.0.0.1:8059"
OUTDIR = "/tmp/nioi-frames"
GIF_OUT = "/tmp/nioi-tanken.gif"

if os.path.isdir(OUTDIR):
    shutil.rmtree(OUTDIR)
os.makedirs(OUTDIR)

# Mobile portrait. Chrome may render scrollbars even with --hide-scrollbars
# in some configs, so we pad and crop conservatively. The page's .app has
# max-width:480 with 14px side padding — JP/EN button anchored to right:14.
WIDTH = 460
HEIGHT = 760
RIGHT_TRIM = 36   # crop right to drop scrollbar/padding without losing the JP/EN button

frames_src = []
# Sequence: empty → ramp up → hold full → EN flip → hold
sequence = [
    (0, 'ja'),
    (2, 'ja'),
    (4, 'ja'),
    (6, 'ja'),
    (8, 'ja'),
    (10, 'ja'),
    (12, 'ja'),
    (12, 'en'),
    (12, 'en'),
]

for i, (n, lang) in enumerate(sequence):
    out = f"{OUTDIR}/frame_{i:02d}.png"
    subprocess.run([
        CHROME,
        "--headless=new",
        "--hide-scrollbars",
        "--no-sandbox",
        "--disable-gpu",
        f"--window-size={WIDTH},{HEIGHT}",
        f"--screenshot={out}",
        "--virtual-time-budget=400",
        f"{URL}/?demo={n}&lang={lang}",
    ], check=True, capture_output=True)
    print(f"frame {i}: demo={n} lang={lang}")

# Compose the GIF
frames = []
for i in range(len(sequence)):
    p = f"{OUTDIR}/frame_{i:02d}.png"
    img = Image.open(p).convert("RGB")
    # Crop right edge to drop scrollbar artifact, preserve JP/EN at right:14
    w, h = img.size
    img = img.crop((0, 0, w - RIGHT_TRIM, h))
    # Resize to hub-card size
    target_w = 320
    ratio = target_w / img.size[0]
    img = img.resize((target_w, int(img.size[1] * ratio)), Image.LANCZOS)
    # Convert to palette
    img = img.quantize(colors=64, method=Image.MEDIANCUT)
    frames.append(img)

# Per-frame durations (ms)
durations = [380] * len(frames)
durations[0] = 700        # hold opening
durations[6] = 700        # hold full Japanese
durations[-1] = 1500      # hold ending

frames[0].save(
    GIF_OUT,
    save_all=True,
    append_images=frames[1:],
    duration=durations,
    loop=0,
    optimize=True,
    disposal=2,
)
print(f"\n✓ wrote {GIF_OUT}")
print(f"  size: {os.path.getsize(GIF_OUT) / 1024:.1f} KB")
