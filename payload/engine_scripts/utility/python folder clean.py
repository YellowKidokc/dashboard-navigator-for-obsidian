import os
import hashlib
import shutil
from pathlib import Path

# --- CONFIG -----------------------------------------------------------------

# Root of your Logos papers repo
ROOT = Path(os.getenv("THEOPHYSICS_LOGOS_PAPERS_ROOT", r"O:\_Theophysics_v3\05_PUBLICATIONS\Logos_Papers\COMPLETE_LOGOS_PAPERS_FINAL"))

ASSETS_IMAGES = ROOT / "Assets" / "images"

# Mapping from paper number to canonical folder name under Assets/images
PAPER_FOLDERS = {
    "P01": "P01-Logos-Principle",
    "P1":  "P01-Logos-Principle",
    "P02": "P02-Quantum-Bridge",
    "P2":  "P02-Quantum-Bridge",
    "P03": "P03-Algorithm-Reality",
    "P3":  "P03-Algorithm-Reality",
    "P04": "P04-Hard-Problem",
    "P4":  "P04-Hard-Problem",
    "P05": "P05-Soul-Observer",
    "P5":  "P05-Soul-Observer",
    "P06": "P06-Physics-Principalities",
    "P6":  "P06-Physics-Principalities",
    "P07": "P07-Grace-Function",
    "P7":  "P07-Grace-Function",
    "P08": "P08-Stretched-Heavens",
    "P8":  "P08-Stretched-Heavens",
    "P09": "P09-Moral-Universe",
    "P9":  "P09-Moral-Universe",
    "P10": "P10-Creatio-Silico",
    "P11": "P11-Protocols-Validation",
    "P12": "P12-Decalogue-Cosmos",
    "P13": "P13_Test_Predictions",
}

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"}


# --- HELPERS ----------------------------------------------------------------

def guess_paper_key(filename: str) -> str | None:
    """
    Try to guess a paper key like 'P01' or 'P7' from the filename.
    Examples:
      P1_02_Great_Schism_v2.png -> 'P1'
      P01-Logos-Principle-something.png -> 'P01'
      P07_GraceFunction.png -> 'P07'
    """
    name = filename
    # Strip extension
    if "." in name:
        name = name.rsplit(".", 1)[0]

    # Look at early tokens split by '_' or '-'
    for sep in ("_", "-"):
        parts = name.split(sep)
        if parts:
            head = parts[0]
            # Normalize things like 'P01', 'P1', 'p01'
            head_norm = head.upper()
            if head_norm.startswith("P") and head_norm[1:].isdigit():
                # Pad single-digit to match mapping where needed
                num = head_norm[1:]
                if len(num) == 1:
                    # We have both P1 and P01 keys in mapping
                    key = "P" + num
                else:
                    key = "P" + num.zfill(2)
                if key in PAPER_FOLDERS:
                    return key
                # Try also the zero-padded / non‑padded variant
                alt_key = "P" + str(int(num))  # remove leading zeros
                if alt_key in PAPER_FOLDERS:
                    return alt_key
    return None


def hash_file(path: Path, chunk_size: int = 65536) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


# --- STEP 1: NORMALIZE IMAGE FOLDERS ----------------------------------------

def normalize_image_locations():
    """
    Move images into the canonical per‑paper folder under Assets/images.
    e.g. anything that starts with P1_ / P01_ goes into Assets/images/P01-Logos-Principle/
    """
    if not ASSETS_IMAGES.exists():
        print(f"[WARN] {ASSETS_IMAGES} does not exist.")
        return

    moved = 0
    skipped = 0

    for path in ASSETS_IMAGES.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in IMAGE_EXTS:
            continue

        rel = path.relative_to(ASSETS_IMAGES)
        filename = path.name

        # Guess paper key
        key = guess_paper_key(filename)
        if not key:
            # Can't determine paper; leave it where it is
            skipped += 1
            continue

        canonical_folder = PAPER_FOLDERS[key]
        dest_dir = ASSETS_IMAGES / canonical_folder
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest_path = dest_dir / filename

        # If already in the correct dir, skip
        if path == dest_path:
            skipped += 1
            continue

        if dest_path.exists():
            # Same name exists; we will let hash/dedupe handle this later
            print(f"[INFO] Dest already exists, leaving original: {dest_path}")
            skipped += 1
            continue

        print(f"[MOVE] {path} -> {dest_path}")
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(dest_path))
        moved += 1

    print(f"[DONE] Normalization complete. Moved={moved}, skipped={skipped}")


# --- STEP 2: DELETE EMPTY FOLDERS -------------------------------------------

def delete_empty_dirs():
    """
    Remove any empty subdirectories under Assets/images.
    """
    # Walk bottom-up so we delete deepest first
    removed = 0
    for dirpath, dirnames, filenames in os.walk(ASSETS_IMAGES, topdown=False):
        p = Path(dirpath)
        # Skip the root ASSETS_IMAGES itself
        if p == ASSETS_IMAGES:
            continue
        if not dirnames and not filenames:
            print(f"[RMDIR] {p}")
            p.rmdir()
            removed += 1
    print(f"[DONE] Empty folder cleanup complete. Removed={removed}")


# --- STEP 3: HASH + DEDUPE --------------------------------------------------

def deduplicate_images():
    """
    Compute SHA‑256 hash of each image file and delete exact duplicates,
    keeping the first instance encountered.
    """
    hashes: dict[str, Path] = {}
    deleted = 0
    kept = 0

    for path in ASSETS_IMAGES.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in IMAGE_EXTS:
            continue
        h = hash_file(path)
        if h in hashes:
            print(f"[DUP] {path} is duplicate of {hashes[h]} -> deleting")
            path.unlink()
            deleted += 1
        else:
            hashes[h] = path
            kept += 1

    print(f"[DONE] Dedup complete. Kept={kept}, Deleted={deleted}")


# --- MAIN -------------------------------------------------------------------

if __name__ == "__main__":
    print(f"[INFO] Assets images root: {ASSETS_IMAGES}")
    normalize_image_locations()
    delete_empty_dirs()
    deduplicate_images()
