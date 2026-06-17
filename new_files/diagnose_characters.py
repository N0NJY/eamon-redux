#!/usr/bin/env python3
"""
Diagnostic script to inspect and fix character JSON files.
Run this to identify corrupted character saves.
"""

import os
import json
import sys

CHARACTERS_DIR = "characters"

def inspect_files():
    """Inspect all character JSON files."""
    if not os.path.isdir(CHARACTERS_DIR):
        print(f"No {CHARACTERS_DIR} directory found.")
        return
    
    files = [f for f in os.listdir(CHARACTERS_DIR) if f.endswith(".json")]
    
    if not files:
        print("No character files found.")
        return
    
    print("=" * 70)
    print("CHARACTER FILE INSPECTION")
    print("=" * 70)
    
    for filename in sorted(files):
        filepath = os.path.join(CHARACTERS_DIR, filename)
        char_name = filename[:-5]  # Remove .json
        
        print(f"\n📄 {filename}")
        print(f"   Path: {filepath}")
        
        try:
            with open(filepath) as f:
                data = json.load(f)
            
            # Check structure
            if isinstance(data, dict):
                print(f"   ✅ Structure: DICT (correct)")
                print(f"   Keys: {list(data.keys())}")
                
                # Verify required fields
                required = ["name", "hardiness", "agility", "charisma", 
                           "intelligence", "strength", "hp", "gold", 
                           "spell_proficiencies", "weapon_proficiencies", "xp", "level"]
                missing = [k for k in required if k not in data]
                
                if missing:
                    print(f"   ⚠️  Missing fields: {missing}")
                else:
                    print(f"   ✅ All required fields present")
                    
            elif isinstance(data, list):
                print(f"   ❌ Structure: LIST (CORRUPTED!)")
                print(f"   Length: {len(data)} items")
                if data:
                    print(f"   First item type: {type(data[0])}")
                    if isinstance(data[0], dict) and "name" in data[0]:
                        print(f"   ⚠️  File contains item list, not character!")
                        
            else:
                print(f"   ❌ Structure: {type(data).__name__} (INVALID)")
                
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON Error: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    inspect_files()
