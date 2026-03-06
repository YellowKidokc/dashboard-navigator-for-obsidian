import os

ROOT_DIR = os.environ.get("SONNET_PICTURES_ROOT", os.getcwd())
OUTPUT_FILE = os.path.join(ROOT_DIR, "GALLERY.md")

def update_gallery():
    print("Updating GALLERY.md...")

    if not os.path.isdir(ROOT_DIR):
        raise FileNotFoundError("ROOT_DIR does not exist: " + ROOT_DIR)

    # Group images by category
    categories = {
        "System": [],
        "Theology": [],
        "Physics": [],
        "Cosmology": [],
        "Other": []
    }

    total_count = 0

    for filename in os.listdir(ROOT_DIR):
        if not filename.endswith(".png"):
            continue

        total_count += 1

        if filename.startswith("System_"):
            categories["System"].append(filename)
        elif filename.startswith("Theology_"):
            categories["Theology"].append(filename)
        elif filename.startswith("Physics_"):
            categories["Physics"].append(filename)
        elif filename.startswith("Cosmology_"):
            categories["Cosmology"].append(filename)
        else:
            categories["Other"].append(filename)

    # Sort everything
    for cat in categories:
        categories[cat].sort()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Theophysics Visual Library\n\n")
        f.write(f"**Total Images:** {total_count}\n\n")
        f.write("--- \n\n")

        # Write categories
        for cat, files in categories.items():
            if not files:
                continue

            f.write(f"## {cat} ({len(files)})\n\n")

            # Create a grid or list
            for filename in files:
                # ![Name](Path)
                name = filename.replace(".png", "")
                # Remove prefix for cleaner display name
                if cat != "Other":
                    name = name.replace(f"{cat}_", "")

                f.write(f"### {name}\n")
                f.write(f"![{name}]({filename})\n\n")

            f.write("---\n\n")

    print(f"Updated gallery with {total_count} images.")

if __name__ == "__main__":
    update_gallery()
