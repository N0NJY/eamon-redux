# Mid-Game Save/Load Integration Summary

## Files Modified

### 1. **save_system.py** (NEW)
- Created in project root
- Implements 3-slot save system per adventure
- Functions:
  - `save_game()` — Save with slot selection and overwrite prompts
  - `load_game()` — Load from slot
  - `list_resumable_games()` — List all saves for a character
  - `get_existing_saves()` — Check which slots are used
  - `prompt_save_slot()` — Interactive slot picker

### 2. **engine.py** (MODIFIED)

#### Imports (Line 22-28)
Added imports from `save_system`:
```python
from save_system import (
    save_game as save_game_slotted,
    load_game as load_game_slotted,
    ensure_saves_dir,
    get_existing_saves,
    prompt_save_slot,
)
```

#### cmd_save() Method (Replaced)
**Old behavior:** `SAVE <filename>` saved to arbitrary file
**New behavior:** 
- Prevents saving during combat ❌ no monsters in current room
- Shows 3 available slots per adventure
- Prompts user to pick slot (1-3) or overwrite existing save
- Compacts state serialization

#### cmd_help() (Updated)
Changed help text:
- Old: `SAVE <name>                      Save game to stored_games/`
- New: `SAVE                             Save game (up to 3 slots)`

---

### 3. **tavern.py** (MODIFIED)

#### Imports (Line 19)
Added:
```python
from save_system import list_resumable_games, load_game as load_game_slotted
```

#### New Function: menu_load_save() (Line 668-751)
- Shows all saved games grouped by adventure
- Lists saves with room, HP, timestamp
- Prompts for adventure selection
- Prompts for slot if multiple saves exist
- Launches engine with `--savefile` argument
- Handles engine return (reload character, mark complete if won)

#### Existing Infrastructure
- `_launch_engine()` already supports `--savefile` arg ✓
- `_handle_engine_return()` already reloads character from disk ✓
- `handle_tavern_command()` already calls `menu_load_save()` on RESUME/LOAD/SAVES ✓

---

## How It Works

### Saving During Adventure
1. Player types `SAVE`
2. Engine checks for combat (monsters in room)
3. If safe, shows slots:
   ```
   ═══ SAVE GAME (2/3 slots used) ═══
   Slot 1: Main Hall (HP: 45, 2026-06-13T14:30:00)
   Slot 2: Treasure Room (HP: 80, 2026-06-13T15:45:00)
   Slot 3: [EMPTY]
   ```
4. Player chooses slot 1-3 or cancels
5. Game state saved to `stored_games/<char>_<adventure>_slot<N>.json`

### Resuming from Tavern
1. Player types `RESUME` in tavern
2. Menu shows all adventures with saves
3. Player picks adventure
4. If multiple saves, pick slot
5. Engine launched with `--savefile stored_games/<file>.json`
6. Engine deserializes and restores state

### Save Persistence
- Saves are **never auto-deleted**
- Player can replay from any save point
- Saves survive death/adventure completion
- Can create new saves on top of old ones (overwrite)

---

## File Size/Token Impact

**save_system.py:** ~200 lines (compact JSON only, no duplication)
**engine.py:** +30 lines net (replaced old save code)
**tavern.py:** +85 lines net (new menu_load_save function)

Total: ~315 new/modified lines

Efficiency notes:
- Save format is minified JSON (no unnecessary whitespace in output)
- Only serializes changed state (monsters, artifacts, rooms, player)
- No compression (keeps it human-readable for debugging)

---

## Testing Checklist

```
□ Copy save_system.py to project root
□ Replace engine.py with engine_modified.py
□ Replace tavern.py with tavern_modified.py
□ Test: SAVE command without combat → slot picker appears
□ Test: Try SAVE during combat → "Cannot save during combat!"
□ Test: Save to slot 1, then slot 2 (overwrite check)
□ Test: RESUME in tavern → see saved game list
□ Test: Load save → verify character in correct room with correct HP
□ Test: Complete adventure → save deleted (optional) or preserved
□ Test: Die → revival fee applied, save persists for replay
```

---

## Code Quality

✅ Uses existing argument passing (no breaking changes)
✅ Leverages engine's existing apply_save_state logic
✅ Reuses _handle_engine_return for consistency
✅ Compact JSON serialization
✅ Interactive prompts match tavern style (tc() colors)
✅ Error handling for missing files/slots
✅ No external dependencies beyond stdlib
