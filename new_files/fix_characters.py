#!/usr/bin/env python3
"""
Fix corrupted character JSON files.
This can restore characters that were accidentally saved with wrong format.
"""

import os
import json
import sys
from pathlib import Path

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

def fix_character_file(filepath):
    """Fix a corrupted character file."""
    print(f"\nProcessing: {filepath}")
    
    try:
        with open(filepath) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON Error: {e}")
        return False
    
    # Case 1: File contains a list (probably items)
    if isinstance(data, list):
        print(f"   ⚠️  File contains list with {len(data)} items (not a character)")
        
        # Try to extract character info from items
        character_name = None
        if data and isinstance(data[0], dict) and "name" in data[0]:
            character_name = data[0].get("character_name")
        
        if not character_name:
            # Ask what to do
            char_name = input(f"   Enter character name to restore: ").strip()
            if not char_name:
                print("   Skipped (no name provided)")
                return False
            character_name = char_name
        
        # Create minimal character dict
        restored = {
            "name": character_name,
            "hardiness": 10,
            "agility": 10,
            "charisma": 10,
            "intelligence": 10,
            "strength": 10,
            "hp": 0,
            "gold": 200,
            "spell_proficiencies": {
                "blast": None, "heal": None, "speed": None, "power": None
            },
            "weapon_proficiencies": {
                "axe": 5, "bow": -10, "club": 20, "spear": 10, "sword": 0
            },
            "xp": 0,
            "level": 1,
            "is_beginner": True,
            "adventures_completed": []
        }
        
        backup_file(filepath)
        
        with open(filepath, 'w') as f:
            json.dump(restored, f, indent=2)
        
        print(f"   ✅ Restored character: {character_name}")
        print(f"   Note: Stats reset to defaults (HP=0 will be set to max on load)")
        return True
    
    # Case 2: File is already a dict, but missing required fields
    elif isinstance(data, dict):
        required = ["name", "hardiness", "agility", "charisma", 
                   "intelligence", "strength", "hp", "gold", 
                   "spell_proficiencies", "weapon_proficiencies", "xp", "level"]
        missing = [k for k in required if k not in data]
        
        if missing:
            print(f"   ⚠️  Missing fields: {missing}")
            
            backup_file(filepath)
            
            # Fill in defaults
            defaults = {
                "hardiness": 10,
                "agility": 10,
                "charisma": 10,
                "intelligence": 10,
                "strength": 10,
                "hp": 0,
                "gold": 200,
                "spell_proficiencies": {
                    "blast": None, "heal": None, "speed": None, "power": None
                },
                "weapon_proficiencies": {
                    "axe": 5, "bow": -10, "club": 20, "spear": 10, "sword": 0
                },
                "xp": 0,
                "level": 1,
                "is_beginner": True,
                "adventures_completed": []
            }
            
            for key in missing:
                data[key] = defaults[key]
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"   ✅ Added missing fields: {missing}")
            return True
        else:
            print(f"   ✅ File looks OK")
            return False
    
    else:
        print(f"   ❌ Unexpected data type: {type(data)}")
        return False

def main():
    """Process all character files."""
    if not os.path.isdir(CHARACTERS_DIR):
        print(f"No {CHARACTERS_DIR} directory found.")
        return
    
    files = [f for f in os.listdir(CHARACTERS_DIR) if f.endswith(".json")]
    
    if not files:
        print("No character files found.")
        return
    
    print("=" * 70)
    print("CHARACTER FILE REPAIR UTILITY")
    print("=" * 70)
    print(f"Found {len(files)} character file(s)\n")
    
    fixed = 0
    for filename in sorted(files):
        filepath = os.path.join(CHARACTERS_DIR, filename)
        if fix_character_file(filepath):
            fixed += 1
    
    print("\n" + "=" * 70)
    print(f"Summary: {fixed} file(s) repaired")
    print("=" * 70)

if __name__ == "__main__":
    main()
