import os
import shutil
from PIL import Image
import numpy as np

ROOT_DIR = os.environ.get("SONNET_PICTURES_ROOT", os.getcwd())
DELETE_DIR = os.path.join(ROOT_DIR, "Gemini", "delete")
os.makedirs(DELETE_DIR, exist_ok=True)

def analyze_and_cleanup():
    print("Analyzing System_*.png files for cleanup...")

    if not os.path.isdir(ROOT_DIR):
        raise FileNotFoundError("ROOT_DIR does not exist: " + ROOT_DIR)

    candidates = []

    for filename in os.listdir(ROOT_DIR):
        if not filename.startswith("System_") or not filename.endswith(".png"):
            continue

        filepath = os.path.join(ROOT_DIR, filename)
        size_kb = os.path.getsize(filepath) / 1024

        # Heuristic 1: Very small files (likely empty or just a header)
        # The user mentioned 'System_feedback.png' which is ~16KB.
        # Let's look at files under 30KB.
        if size_kb < 30:
            try:
                with Image.open(filepath) as img:
                    # Heuristic 2: Low color variance (mostly white/empty)
                    # Convert to grayscale
                    gray = img.convert('L')
                    stat =  np.array(gray)
                    std_dev = np.std(stat)
                    mean_val = np.mean(stat)

                    # If mostly white (high mean) and low variance (little detail)
                    # Or just very small file size is usually enough for PNGs

                    candidates.append({
                        'name': filename,
                        'size_kb': size_kb,
                        'std_dev': std_dev,
                        'mean': mean_val
                    })
            except Exception as e:
                print(f"Error reading {filename}: {e}")

    print(f"Found {len(candidates)} candidates for deletion (Size < 30KB).")

    # Sort by size
    candidates.sort(key=lambda x: x['size_kb'])

    count = 0
    for c in candidates:
        print(f"Moving {c['name']} (Size: {c['size_kb']:.2f}KB, Mean: {c['mean']:.2f})")
        src = os.path.join(ROOT_DIR, c['name'])
        dst = os.path.join(DELETE_DIR, c['name'])
        shutil.move(src, dst)

        # Also move the yaml if it exists
        yaml_src = src + ".meta.yaml"
        if os.path.exists(yaml_src):
            yaml_dst = dst + ".meta.yaml"
            shutil.move(yaml_src, yaml_dst)

        count += 1

    print(f"Moved {count} files to {DELETE_DIR}")

if __name__ == "__main__":
    analyze_and_cleanup()
