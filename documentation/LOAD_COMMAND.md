# LOAD Command Feature

## Overview
Players can now load a previously saved game mid-adventure using the `LOAD` command. This allows them to restore from a safe checkpoint without quitting back to the tavern.

## How It Works

### Basic Usage
While in an adventure, type:
```
> LOAD
```

### What Happens
1. Shows list of all saves for current adventure with:
   - Slot number (1-3)
   - Room name (where saved)
   - HP at time of save
   - Timestamp

2. Player selects a slot (1-3) or cancels

3. Full game state is restored:
   - Character position, HP, mana
   - Inventory state
   - Monster positions and HP
   - Room state (first visits, locked exits)
   - Spell effects (shield rounds, etc.)

4. Adventure continues from saved point

## Example

```
> LOAD

  ═══ LOAD GAME (2 save(s)) ═══
    Slot 1: Main Hall (HP: 45, 2026-06-13T14:30:00)
    Slot 2: Treasure Room (HP: 80, 2026-06-13T15:45:00)
    3. Cancel

  Load from which slot? (1-3, or 'cancel'): 1

  ✅ Loaded from slot 1

  ── Main Hall ──
  You stand in a grand hall...
```

## Technical Details

### Implementation
- Command: `"load": lambda: self.cmd_load(noun)`
- Handler: `cmd_load()` in Engine class
- Uses existing: `load_game_slotted()` and `apply_save_state()`
- Same save format as SAVE command

### State Restoration
The LOAD command restores:
- Player stats (HP, mana, position)
- XP/level (unchanged from save)
- Inventory (all carried artifacts)
- World state:
  - Monster positions and HP
  - Room state (first_visit flags, locked_exits)
  - Artifact locations
  - Light source status

### Restrictions
- Must have at least one save for current adventure
- Can load any of 3 slots
- Load happens immediately (no confirmation)
- Overwrites current game state completely

## Use Cases

**Escape a bad situation:**
```
> LOAD
# Restore from checkpoint before fighting tough monster
```

**Explore different paths:**
```
> SAVE  (at crossroads, slot 1)
> Go north
> (explore, decide not to continue)
> LOAD  (back to crossroads)
> Go east  (try different path)
```

**Retry after death:**
```
# Died and revived by tavern
# Re-enter adventure
> LOAD  (from last save, skip revival cost)
```

## Files Modified

**engine.py:**
- Added `cmd_load()` method
- Added "load" to command dispatch
- Updated HELP text

**No changes needed to:**
- tavern.py (tavern RESUME uses different slot system)
- save_system.py (reuses existing functions)
- save files (same format)
