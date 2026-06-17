#!/usr/bin/env python3
"""
Fix corrupted items JSON files.
"""

import os
import json
import sys

CHARACTERS_DIR = "characters"

def backup_file(filepath):
    """Create a backup before modifying."""
    backup_path = filepath + ".backup"
    if not os.path.exists(backup_path):
        import shutil
        shutil.copy(filepath, backup_path)
        print(f"   Backup created: {backup_path}")
        return backup_path
    return backup_path

def fix_items_file(filepath):
    """Fix a corrupted items file."""
    print(f"\nProcessing: {filepath}")
    
    filename = os.path.basename(filepath)
    char_name = filename[:-11]  # Remove _items.json
    
    # Check file size
    size = os.path.getsize(filepath)
    
    if size == 0:
        print(f"   ⚠️  File is EMPTY")
        
        backup_file(filepath)
        
        # Create empty items list
        with open(filepath, 'w') as f:
            json.dump([], f, indent=2)
        
        print(f"   ✅ Initialized empty items list")
        return True
    
    try:
        with open(filepath) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON Error: {e}")
        print(f"   Recreating as empty list...")
        
        backup_file(filepath)
        
        with open(filepath, 'w') as f:
            json.dump([], f, indent=2)
        
        print(f"   ✅ Recreated as empty items list")
        return True
    
    # Case 1: File is a string (corrupted)
    if isinstance(data, str):
        print(f"   ❌ File contains string (CORRUPTED!)")
        print(f"   Content: {data[:50]}")
        
        backup_file(filepath)
        
        # Try to parse the string as JSON
        try:
            parsed = json.loads(data)
            if isinstance(parsed, list):
                # String was a serialized list, use it
                with open(filepath, 'w') as f:
                    json.dump(parsed, f, indent=2)
                print(f"   ✅ Recovered items from corrupted string")
                return True
            elif isinstance(parsed, dict):
                # Single item, wrap in list
                with open(filepath, 'w') as f:
                    json.dump([parsed], f, indent=2)
                print(f"   ✅ Wrapped single item in list")
                return True
        except:
            pass
        
        # Can't recover, create empty list
        with open(filepath, 'w') as f:
            json.dump([], f, indent=2)
        print(f"   ✅ Could not recover - reset to empty list")
        return True
    
    # Case 2: File is a dict (should be list)
    elif isinstance(data, dict):
        print(f"   ⚠️  File contains dict (should be list!)")
        
        backup_file(filepath)
        
        # Wrap in list if it looks like an item
        if "name" in data or "id" in data:
            with open(filepath, 'w') as f:
                json.dump([data], f, indent=2)
            print(f"   ✅ Wrapped single item in list")
        else:
            # Not an item dict, reset
            with open(filepath, 'w') as f:
                json.dump([], f, indent=2)
            print(f"   ✅ Reset to empty list")
        return True
    
    # Case 3: File is a list (correct!)
    elif isinstance(data, list):
        print(f"   ✅ Structure looks OK (list with {len(data)} items)")
        
        # Validate each item
        valid = True
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                print(f"   ⚠️  Item {i} is {type(item).__name__} (should be dict)")
                valid = False
        
        if valid:
            print(f"   ✅ All items are valid dicts")
            return False  # No fix needed
        else:
            # Try to fix invalid items
            backup_file(filepath)
            
            fixed_items = [item for item in data if isinstance(item, dict)]
            
            with open(filepath, 'w') as f:
                json.dump(fixed_items, f, indent=2)
            
            print(f"   ✅ Removed {len(data) - len(fixed_items)} invalid items")
            return True
    
    else:
        print(f"   ❌ Unexpected data type: {type(data)}")
        
        backup_file(filepath)
        
        with open(filepath, 'w') as f:
            json.dump([], f, indent=2)
        
        print(f"   ✅ Reset to empty list")
        return True

def main():
    """Process all items files."""
    if not os.path.isdir(CHARACTERS_DIR):
        print(f"No {CHARACTERS_DIR} directory found.")
        return
    
    files = [f for f in os.listdir(CHARACTERS_DIR) if f.endswith("_items.json")]
    
    if not files:
        print("No items files found.")
        return
    
    print("=" * 70)
    print("ITEMS FILE REPAIR UTILITY")
    print("=" * 70)
    print(f"Found {len(files)} items file(s)\n")
    
    fixed = 0
    for filename in sorted(files):
        filepath = os.path.join(CHARACTERS_DIR, filename)
        if fix_items_file(filepath):
            fixed += 1
    
    print("\n" + "=" * 70)
    print(f"Summary: {fixed} file(s) repaired")
    print("=" * 70)

if __name__ == "__main__":
    main()
