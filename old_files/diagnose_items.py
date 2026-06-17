#!/usr/bin/env python3
"""
Diagnostic script to inspect items JSON files.
Run this to identify corrupted items saves.
"""

import os
import json
import sys

CHARACTERS_DIR = "characters"

def inspect_items_files():
    """Inspect all character items JSON files."""
    if not os.path.isdir(CHARACTERS_DIR):
        print(f"No {CHARACTERS_DIR} directory found.")
        return
    
    files = [f for f in os.listdir(CHARACTERS_DIR) if f.endswith("_items.json")]
    
    if not files:
        print("No items files found.")
        return
    
    print("=" * 70)
    print("ITEMS FILE INSPECTION")
    print("=" * 70)
    
    for filename in sorted(files):
        filepath = os.path.join(CHARACTERS_DIR, filename)
        char_name = filename[:-11]  # Remove _items.json
        
        print(f"\n📄 {filename}")
        print(f"   Path: {filepath}")
        
        # Check file size first
        size = os.path.getsize(filepath)
        print(f"   Size: {size} bytes")
        
        if size == 0:
            print(f"   ⚠️  File is EMPTY")
            continue
        
        try:
            with open(filepath) as f:
                content = f.read()
                
            print(f"   Raw content (first 100 chars): {content[:100]}")
            
            # Try to parse JSON
            f_handle = open(filepath)
            data = json.load(f_handle)
            f_handle.close()
            
            # Check structure
            if isinstance(data, list):
                print(f"   ✅ Structure: LIST (correct)")
                print(f"   Length: {len(data)} items")
                
                if data:
                    first = data[0]
                    if isinstance(first, dict):
                        print(f"   First item keys: {list(first.keys())}")
                        if "name" in first:
                            print(f"   First item: {first['name']}")
                    else:
                        print(f"   ❌ First item is {type(first).__name__} (should be dict)")
                        
            elif isinstance(data, dict):
                print(f"   ⚠️  Structure: DICT (should be LIST!)")
                print(f"   Keys: {list(data.keys())}")
                
            elif isinstance(data, str):
                print(f"   ❌ Structure: STRING (CORRUPTED!)")
                print(f"   Content: {data[:100]}")
                
            else:
                print(f"   ❌ Structure: {type(data).__name__} (INVALID)")
                
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON Error: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    inspect_items_files()
