import os
import shutil

ROOT_DIR = os.environ.get("SONNET_PICTURES_ROOT", os.getcwd())

def process_new_files():
    print("Processing new files...")

    if not os.path.isdir(ROOT_DIR):
        raise FileNotFoundError("ROOT_DIR does not exist: " + ROOT_DIR)

    for filename in os.listdir(ROOT_DIR):
        if not filename.endswith(".png"):
            continue

        # Skip already processed files
        if filename.startswith("System_") or filename.startswith("Theology_") or filename.startswith("Physics_") or filename.startswith("Cosmology_"):
            continue

        new_name = filename
        category = "Uncategorized"

        # Determine Category and New Name
        if filename.startswith("law_"):
            # law_07b_complementarity.png -> Theology_Law_07b_Complementarity.png
            parts = filename.replace(".png", "").split("_")
            # Capitalize parts
            capitalized_parts = [p.capitalize() for p in parts]
            new_name = f"Theology_{'_'.join(capitalized_parts)}.png"
            category = "Theology"

        elif filename.startswith("trinity_"):
            # trinity_fractal.png -> Theology_Trinity_Fractal.png
            parts = filename.replace(".png", "").split("_")
            capitalized_parts = [p.capitalize() for p in parts]
            new_name = f"Theology_{'_'.join(capitalized_parts)}.png"
            category = "Theology"

        if new_name != filename:
            src_path = os.path.join(ROOT_DIR, filename)
            dest_path = os.path.join(ROOT_DIR, new_name)

            print(f"Renaming {filename} -> {new_name}")
            try:
                shutil.move(src_path, dest_path)

                # Generate YAML
                yaml_path = dest_path + ".meta.yaml"
                clean_name = new_name.replace(".png", "").replace(f"{category}_", "")

                yaml_content = f"""id: {new_name}
name: {clean_name}
path: {new_name}
tags:
  - {category}
  - New_Addition
canonical:
  category: {category}
  name: {clean_name}
  description: "New addition: {clean_name}"
taxonomy:
  phase_1:
    decision: Keep
    initial_impression: "New Image"
  phase_2:
    physics_nature: "Digital/Visual"
    explanatory_power: "High"
    quality: "High"
"""
                with open(yaml_path, "w", encoding="utf-8") as f:
                    f.write(yaml_content)
                print(f"Generated YAML for {new_name}")

            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    process_new_files()
