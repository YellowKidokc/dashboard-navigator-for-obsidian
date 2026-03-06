import os

# Define the root directory of the vault
root_dir = "O:\\THEOPHYSICS"

# Loop through all the directories and subdirectories in the vault
for dirpath, dirnames, filenames in os.walk(root_dir):
    # Check if the directory contains any markdown files
    markdown_files = [f for f in filenames if f.endswith(".md")]
    if markdown_files:
        # Print the name of the directory
        print(f"Folder to be processed: {dirpath}")

        # Print the name of the merged file that would be created
        merged_file_name = "_MERGED_DOCUMENT.md"
        print(f"  - Would create: {os.path.join(dirpath, merged_file_name)}")

