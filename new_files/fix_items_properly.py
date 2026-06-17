#!/usr/bin/env python3
"""
Properly fix items files - reset corrupted files to empty lists.
"""

import os
import json

CHARACTERS_DIR = "characters"

def reset_items_file(filepath):
    """Reset an items file to empty list."""
    filename = os.path.basename(filepath)
    char_name = filename[:-11]  # Remove _items.json
    
    print(f"\nProcessing: {filename}")
    
    # Backup the corrupted file
    backup_path = filepath + ".backup"
    if not os.path.exists(backup_path):
        import shutil
        shutil.copy(filepath, backup_path)
        print(f"   ✅ Backup created: {backup_path}")
    
    # Reset to empty items list
    with open(filepath, 'w') as f:
        json.dump([], f, indent=2)
    
    print(f"   ✅ Reset to empty items list")
    return True

def main():
    if not os.path.isdir(CHARACTERS_DIR):
        print(f"No {CHARACTERS_DIR} directory found.")
        return
    
    files = [f for f in os.listdir(CHARACTERS_DIR) if f.endswith("_items.json")]
    
    if not files:
        print("No items files found.")
        return
    
    print("=" * 70)
    print("ITEMS FILE PROPER FIX - Reset to Empty Lists")
    print("=" * 70)
    print(f"Found {len(files)} items file(s)\n")
    
    for filename in sorted(files):
        filepath = os.path.join(CHARACTERS_DIR, filename)
        reset_items_file(filepath)
    
    print("\n" + "=" * 70)
    print(f"All items files reset. Characters start with empty inventory.")
    print("=" * 70)

if __name__ == "__main__":
    main()
