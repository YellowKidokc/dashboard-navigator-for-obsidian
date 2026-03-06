import os
import shutil

ROOT_DIR = os.environ.get("SONNET_PICTURES_ROOT", os.getcwd())
SCRIPTS_DIR = os.path.join(ROOT_DIR, "Python_Scripts")
DOCS_DIR = os.path.join(ROOT_DIR, "Documentation_and_Logs")

os.makedirs(SCRIPTS_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

def organize_root():
    print(f"Organizing {ROOT_DIR}...")

    if not os.path.isdir(ROOT_DIR):
        raise FileNotFoundError("ROOT_DIR does not exist: " + ROOT_DIR)

    for filename in os.listdir(ROOT_DIR):
        src_path = os.path.join(ROOT_DIR, filename)

        if os.path.isdir(src_path):
            continue

        # Move Python scripts
        if filename.endswith(".py"):
            print(f"Moving script: {filename}")
            shutil.move(src_path, os.path.join(SCRIPTS_DIR, filename))

        # Move Markdown/Text docs (excluding key ones if needed, but user said "folder with everything else")
        elif filename.endswith(".md") or filename.endswith(".txt") or filename.endswith(".bat"):
            print(f"Moving doc: {filename}")
            shutil.move(src_path, os.path.join(DOCS_DIR, filename))

        # Move Zips/Videos
        elif filename.endswith(".zip") or filename.endswith(".mp4"):
            print(f"Moving media/archive: {filename}")
            shutil.move(src_path, os.path.join(DOCS_DIR, filename))

if __name__ == "__main__":
    organize_root()
