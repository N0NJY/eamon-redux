"""
Mid-game save/load system for Eamon Redux.
- 3 saves per adventure (with overwrite option)
- No saves during combat
- Compact JSON serialization
- Persistent saves (no auto-delete on death/complete)
"""

import json
import os
from datetime import datetime
from typing import Optional, Tuple, Dict, List

from core.data_validator import SaveFileValidator
from core.input_validator import safe_input


SAVES_DIR = 'stored_games'
MAX_SAVES_PER_ADVENTURE = 3


def ensure_saves_dir():
    """Create stored_games directory if missing."""
    os.makedirs(SAVES_DIR, exist_ok=True)


def _get_save_filename(character_name: str, adventure_name: str, slot: int) -> str:
    """Generate save filename: char_adventure_slot1.json"""
    safe_char = character_name.replace(' ', '_').lower()
    safe_adv = adventure_name.replace(' ', '_').lower()
    return f"{safe_char}_{safe_adv}_slot{slot}.json"


def get_existing_saves(character_name: str, adventure_name: str) -> List[Tuple[int, str, dict]]:
    """
    Return list of (slot, filename, metadata) for this character+adventure.
    Sorted by slot number.
    """
    ensure_saves_dir()
    saves = []
    
    for slot in range(1, MAX_SAVES_PER_ADVENTURE + 1):
        filename = _get_save_filename(character_name, adventure_name, slot)
        filepath = os.path.join(SAVES_DIR, filename)
        
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                meta = {
                    'timestamp': data.get('timestamp'),
                    'room': data.get('player', {}).get('room_id'),  # Use room_id, not current_room
                    'hp': data.get('player', {}).get('hp'),
                }
                saves.append((slot, filename, meta))
            except (json.JSONDecodeError, IOError):
                pass
    
    return saves


def prompt_save_slot(character_name: str, adventure_name: str) -> Optional[int]:
    """
    Show player existing saves and prompt for slot (1-3).
    Return slot number, or None if cancelled.
    """
    existing = get_existing_saves(character_name, adventure_name)
    
    print(f"\n=== SAVE GAME ({len(existing)}/{MAX_SAVES_PER_ADVENTURE} slots used) ===")
    
    # Show used slots
    for slot, filename, meta in existing:
        print(f"  Slot {slot}: {meta['room']} (HP: {meta['hp']}, {meta['timestamp']})")
    
    # Show empty slots
    for slot in range(1, MAX_SAVES_PER_ADVENTURE + 1):
        if not any(s[0] == slot for s in existing):
            print(f"  Slot {slot}: [EMPTY]")
    
    choice = safe_input("\nSave to which slot? (1-3, or 'cancel')")
    
    if choice.lower() == 'cancel':
        return None
    
    try:
        slot = int(choice)
        if 1 <= slot <= MAX_SAVES_PER_ADVENTURE:
            return slot
        else:
            print("❌ Invalid slot.")
            return None
    except ValueError:
        print("❌ Invalid input.")
        return None


def save_game(
    character_name: str,
    adventure_name: str,
    player_state: dict,
    world_state: dict,
    slot: Optional[int] = None,
    interactive: bool = True
) -> bool:
    """
    Save game to disk. Returns True if saved, False otherwise.
    
    Args:
        character_name: Player character name
        adventure_name: Adventure name
        player_state: {'hp', 'mana', 'xp', 'level', 'current_room', 'inventory', 'spells', ...}
        world_state: {'monsters', 'artifacts', 'flags', ...}
        slot: Save to specific slot (1-3), or prompt if None
        interactive: Show prompts (True) or silent (False)
    """
    if interactive and slot is None:
        slot = prompt_save_slot(character_name, adventure_name)
        if slot is None:
            print("⊘ Save cancelled.")
            return False
    elif slot is None:
        slot = 1  # Default to slot 1 if non-interactive
    
    if not (1 <= slot <= MAX_SAVES_PER_ADVENTURE):
        if interactive:
            print("❌ Invalid slot.")
        return False
    
    ensure_saves_dir()
    filename = _get_save_filename(character_name, adventure_name, slot)
    filepath = os.path.join(SAVES_DIR, filename)
    
    save_data = {
        'character': character_name,
        'adventure': adventure_name,
        'timestamp': datetime.now().isoformat(),
        'player': player_state,
        'world': world_state,
    }

    # Warn on any structural issues (data still saved as-is)
    is_valid, errors, _ = SaveFileValidator.validate(save_data)
    if not is_valid and interactive:
        for err in errors:
            print(f"  ⚠ {err}")

    # Atomic write: write to .tmp then rename so a crash mid-write
    # never leaves the slot in a half-written state.
    temp_path = filepath + ".tmp"
    try:
        with open(temp_path, 'w') as f:
            json.dump(save_data, f, indent=2, separators=(',', ': '))
        os.replace(temp_path, filepath)

        if interactive:
            print(f"✅ Game saved to slot {slot} ({filename})")
        return True

    except IOError as e:
        if interactive:
            print(f"❌ Save failed: {e}")
        try:
            os.remove(temp_path)
        except OSError:
            pass
        return False


def load_game(
    character_name: str,
    adventure_name: str,
    slot: Optional[int] = None,
    interactive: bool = True
) -> Optional[dict]:
    """
    Load game from disk. Returns save_data dict or None if not found/error.
    
    Args:
        character_name: Player character name
        adventure_name: Adventure name
        slot: Load specific slot (1-3), or prompt if None
        interactive: Show prompts (True) or silent (False)
    """
    existing = get_existing_saves(character_name, adventure_name)
    
    if not existing:
        if interactive:
            print("❌ No saves found for this adventure.")
        return None
    
    if interactive and slot is None:
        print(f"\n=== LOAD GAME ({len(existing)} save(s) available) ===")
        for slot_num, filename, meta in existing:
            print(f"  Slot {slot_num}: {meta['room']} (HP: {meta['hp']}, {meta['timestamp']})")
        
        choice = safe_input("\nLoad which slot? (1-3, or 'cancel')")

        if choice.lower() == 'cancel':
            print("⊘ Load cancelled.")
            return None

        try:
            slot = int(choice)
        except ValueError:
            print("❌ Invalid input.")
            return None
    
    if slot is None:
        slot = existing[0][0]  # Load first available if non-interactive
    
    filename = _get_save_filename(character_name, adventure_name, slot)
    filepath = os.path.join(SAVES_DIR, filename)
    
    if not os.path.exists(filepath):
        if interactive:
            print(f"❌ Slot {slot} not found.")
        return None
    
    try:
        with open(filepath, 'r') as f:
            raw_data = json.load(f)

        # Validate and repair structural issues
        is_valid, errors, save_data = SaveFileValidator.validate(raw_data)
        if not is_valid and interactive:
            print("⚠ Save file was corrupted. Repairs made:")
            for err in errors:
                print(f"  • {err}")

        if interactive:
            print(f"✅ Loaded from slot {slot} ({save_data.get('timestamp', 'unknown time')})")
        return save_data

    except json.JSONDecodeError as e:
        if interactive:
            print(f"❌ Save file is corrupted (invalid JSON): {e}")
        return None
    except IOError as e:
        if interactive:
            print(f"❌ Load failed: {e}")
        return None


def list_resumable_games(character_name: str) -> Dict[str, List[Tuple[int, str, dict]]]:
    """
    Return dict of {adventure_name: [(slot, filename, meta), ...]}
    for all adventures with saves for this character.
    """
    ensure_saves_dir()
    games = {}
    
    for filename in os.listdir(SAVES_DIR):
        if not filename.endswith('.json'):
            continue
        
        try:
            # Parse filename: char_adventure_slot1.json
            parts = filename[:-5].split('_slot')  # Remove .json, split by _slot
            if len(parts) == 2:
                char_adv = parts[0]
                slot = int(parts[1])
                
                # Simple heuristic: last part before first number is adventure
                # For now, we'll load and check metadata instead
                filepath = os.path.join(SAVES_DIR, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                if data.get('character') == character_name:
                    adv_name = data.get('adventure', 'Unknown')
                    if adv_name not in games:
                        games[adv_name] = []
                    
                    meta = {
                        'timestamp': data.get('timestamp'),
                        'room': data.get('player', {}).get('current_room'),
                        'hp': data.get('player', {}).get('hp'),
                    }
                    games[adv_name].append((slot, filename, meta))
        
        except (json.JSONDecodeError, ValueError, IOError):
            pass
    
    # Sort slots within each adventure
    for adv in games:
        games[adv].sort(key=lambda x: x[0])
    
    return games
