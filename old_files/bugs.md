# Eamon Redux — Bug Tracker
**Last Updated**: June 18, 2026 — ALL 22 BUGS RESOLVED

---

## Session Summary: June 17, 2026

### ✅ Bugs Fixed This Session (Foundational Issues)
These bugs were discovered and fixed during the session but were not in the original 21-bug list:

1. **Movement system indentation bug**
   - **Problem**: Movement code was indented into `cmd_status()` instead of `cmd_go()`
   - **Impact**: Players couldn't move in any direction (s/n/e/w)
   - **Status**: ✅ FIXED — Restored 19 lines of code to correct location
   - **File**: engine.py lines 413-431

2. **Item persistence missing**
   - **Problem**: Items disappeared when exiting adventure (gold/XP saved but items lost)
   - **Impact**: Players lost all inventory on exit (CRITICAL)
   - **Status**: ✅ FIXED — Added `_save_carried_items()` function called at all exit points
   - **Files**: engine.py (lines 1316, 1335, 1345)

3. **Character loading crash**
   - **Problem**: `Character.list_all()` returned item files (`*_items.json`) as characters
   - **Impact**: Tavern menu showed invalid entries, crashes on load
   - **Status**: ✅ FIXED — Added filter to exclude `*_items.json` files
   - **File**: character.py

4. **Command parsing infrastructure**
   - **Problem**: No abbreviation system for commands
   - **Impact**: Players had to type full commands (tedious UX)
   - **Status**: ✅ FIXED — Added 40+ aliases (ex, ca, dr, sp, hp, etc.)
   - **Files**: command_parser.py
   - **Test Coverage**: 50+ test cases, all passing

### Test Results
```
✅ Character operations (create, load, persist)
✅ Adventure entry/exit (can now exit properly)
✅ Item persistence (items stay across sessions)
✅ Movement system (s/n/e/w/u/d all functional)
✅ Combat system (working end-to-end)
✅ Spell system (functional with proficiency tracking)
✅ Command parsing (full commands and abbreviations)
```

### Commit Status
All fixes committed locally. Ready to push after Session 1 bug fixes.

---

## 21 Known Bugs — Current Status

**Key**:
- 🔴 CRITICAL: Game crash or completely broken feature
- 🟠 HIGH: Major missing feature or broken logic
- 🟡 MEDIUM: State persistence or UX issue
- 🟢 LOW: Code quality or documentation
- ⏳ PENDING: Not yet fixed
- ✅ FIXED: Completed and tested
- 📅 S1/S2/S3/S4: Scheduled for that session

---

## engine.py

### Bug 1: `self.roll()` crash on unarmed combat (line 1016)
**Status**: ✅ FIXED | Session June 17  
**Severity**: 🔴 CRITICAL  
**Problem**: `Engine` has no `roll` method — it's module-level. Raises `AttributeError` when attacking without weapon.  
**Root Cause**: Incorrect method reference (`self.roll()` instead of `roll()`)  
**Fix**: Replaced `self.roll(...)` with `roll(...)` — now at line 1079  
**Affects Other Files**: No — `roll()` is only defined and used within engine.py

---

### Bug 2: EXIT_TAVERN leaves player stuck (lines 338–341)
**Status**: ✅ FIXED | Session June 18  
**Severity**: 🔴 CRITICAL  
**Problem**: Previous attempt removed `player.room_id = "EXIT_TAVERN"` assignment but `_check_win()` still relied on it — escape message printed but game loop continued with player stuck in original room.  
**Fix Applied**:
- `cmd_go`: restored `self.player.room_id = "EXIT_TAVERN"` assignment
- `handle()`: added EXIT_TAVERN check after both direction and `go` branches → returns `3` (escaped)
- `_check_win()`: removed incorrect EXIT_TAVERN check (not a win condition)
- `run_adventure()`: added `result == 3` handler — syncs character state and items, returns `3`
- `_handle_engine_return()`: added `escaped = (result == 3)` — prints return message, no death cost, no completion mark
- `run_tavern()`: `result == 3` skips "return to adventure board?" and loops back to tavern exploration
**Result**: Player exits dungeon → returns to tavern to buy/sell → can re-enter adventure board when ready

---

### Bug 3: Wrong color key on instant kill (line 1045)
**Status**: ✅ FIXED | Pre-existing (verified June 18)  
**Severity**: 🟡 MEDIUM  
**Problem**: Already fixed before this session — no `"combat_win"` key exists anywhere in engine.py. All death/kill messages correctly use `"win"`.

---

### Bug 4: `_consume()` drops item instead of destroying it (line 592)
**Status**: ✅ FIXED | Pre-existing (verified June 18)  
**Severity**: 🟠 HIGH  
**Problem**: Bug was already fixed before this session — `_consume()` correctly uses `del self.world.artifacts[artifact.id]` at line 674. Bug description was written against an earlier version of the code.

---

### Bug 5: `engine.tc()` NameError if run directly (line 1312)
**Status**: ✅ FIXED | Pre-existing (verified June 18)  
**Severity**: 🟡 MEDIUM  
**Problem**: Never existed in current code. All `engine.tc(...)` calls are inside `run_adventure()` where `engine` is a local `Engine` instance (line 1307). The `__main__` block uses `c(C.ERROR, ...)` directly, not `engine.tc()`.

---

### Bug 6: Death doesn't sync `character.hp` before healing cost (lines 1279–1295)
**Status**: ✅ FIXED | Session June 17 + hardened June 18  
**Severity**: 🔴 CRITICAL  
**Problem**: On death, `run_adventure()` synced gold/xp/proficiencies but NOT `hp`. Healing cost was calculated from stale (full) hp, resulting in 0 cost.  
**Fix Applied**: `character.hp = max(0, engine.player.hp)` on death — clamps overkill damage to 0 so healer charges full `hp_max` cost correctly

---

### Bug 7: Seven commands registered but never dispatched (lines 220–282)
**Status**: ✅ FIXED | Session June 18  
**Severity**: 🟠 HIGH  
**Problem**: These commands had methods but no `elif` cases in `handle()` — they silently did nothing:
- `eat` → `cmd_eat()`
- `drink` → `cmd_drink()`
- `open` → `cmd_open()`
- `close` → `cmd_close()`
- `unlock` → `cmd_unlock()`
- `talk` → `cmd_talk()`  
**Fix**: Added 6 `elif` blocks to `handle()` after the `flee` case, each extracting the noun from raw_input and passing it to the corresponding method.

---

### Bug 8: Speed spell never affects combat hit/dodge (lines 946, 1102)
**Status**: ✅ FIXED | Session June 18  
**Severity**: 🟠 HIGH  
**Problem**: `_cast_speed()` sets `agility_effective = agility * 2`, but `cmd_attack()` and `monster_round()` used `agility_bonus` (derived from base agility). Speed bonus never applied to combat.  
**Fix**: Added `agility_effective_bonus` property to `Player` — returns `(agility_effective - 10) // 2`, which automatically doubles when `speed_active` is True. Both `cmd_attack()` and `monster_round()` now use `agility_effective_bonus` instead of `agility_bonus`.

---

### Bug 9: Failed flee gives no monster counter-attack (lines 1128–1143)
**Status**: ✅ FIXED | Session June 18  
**Severity**: 🟠 HIGH  
**Problem**: If `random.choice(DIRECTIONS)` picks direction with no exit, prints "can't flee" and returns without calling `monster_round()`. Player gets free safe "fail" with no consequences.  
**Root Cause**: `monster_round()` only called on successful flee  
**Fix**: Restructured `cmd_flee()` — monster always attacks first, then flee direction is checked. Failed flee prints "You're trapped!" instead of "You can't flee {direction}!"  
**Testing**: Fail flee multiple times → should take monster damage

---

### Bug 10: Auto-attack on room entry is reversed (lines 365–369)
**Status**: ✅ FIXED | Session June 18  
**Severity**: 🟠 HIGH  
**Problem**: Printed "A {monster} attacks you!" but called `cmd_attack(m.name)` — player attacked monster instead.  
**Fix Applied**: Replaced `self.cmd_attack(m.name)` with `self.monster_round(m)` — monster now correctly strikes first on room entry.

---

## tavern.py

### Bug 11: `_launch_engine` ignores `savefile` parameter (lines 951–955)
**Status**: ✅ FIXED | Pre-existing (verified June 18)  
**Severity**: 🟡 MEDIUM  
**Problem**: Already fixed — `run_adventure(character, adv_path, savefile)` correctly passes `savefile` through at line 927.

---

### Bug 12: `menu_load_save` defined twice (lines 323 and 738)
**Status**: ✅ FIXED | Pre-existing (verified June 18)  
**Severity**: 🟡 MEDIUM  
**Problem**: Already fixed — only one definition of `menu_load_save` exists, at line 710.

---

### Bug 13: "talk to" special case is unreachable (lines 587–593)
**Status**: ✅ FIXED | Session June 17  
**Severity**: 🟡 MEDIUM  
**Problem**: `parts = raw.split(maxsplit=1)` limited to 2 items — `len(parts) >= 3` was always False.  
**Fix Applied**: Changed `maxsplit=1` to `maxsplit=2` and `noun = parts[2]` — "talk to horace" now correctly extracts noun as "horace"

---

### Bug 14: Dead code in `_process_sell` (lines 272–275)
**Status**: ✅ FIXED | Session June 18  
**Severity**: 🟢 LOW  
**Problem**: The `pass` block was already removed, but two stale comments remained (`# BUG 10 FIX: Removed...` and `# ✅ REMOVED: ...`). Removed both comments.

---

## command_parser.py

### Bug 15: `"get all"` space alias can never match (line 32)
**Status**: ✅ FIXED | Session June 18  
**Severity**: 🟢 LOW  
**Fix**: Removed `"get all"` from aliases list — only `"ga"` remains. `get all` still works via manual parsing in engine.py.

---

### Bug 16: Docstring example is wrong (line 116)
**Status**: ✅ FIXED | Session June 18  
**Severity**: 🟢 LOW  
**Fix**: Corrected example to `("look", "exact", None)` — `"l"` is an exact alias for `look`, not ambiguous.

---

### Bug 17: "go" typed alone silently does nothing (line ~270)
**Status**: ✅ FIXED | Session June 18  
**Severity**: 🟢 LOW  
**Fix**: Added `else` branch printing `"Go where? (north, south, east, west, up, down)"`.

---

## world.py

### Bug 18: `Monster.to_dict()` drops `xp_value` (line 151)
**Status**: ✅ FIXED | Session June 18  
**Severity**: 🟡 MEDIUM  
**Problem**: `xp_value` was missing from both `to_dict()` and `from_dict()` — custom XP values reverted to 0 on save/load.  
**Fix**: Added `"xp_value": self.xp_value` to `to_dict()` and `xp_value=d.get("xp_value", 0)` to `from_dict()`.

---

### Bug 19: `Room.to_dict()` drops `first_visit` (line 200)
**Status**: ✅ FIXED | Session June 18  
**Severity**: 🟡 MEDIUM  
**Problem**: `first_visit` not serialized in either direction — on reload every room printed its full description again regardless of prior visits.  
**Fix**: Added `"first_visit": self.first_visit` to `to_dict()` and `first_visit=d.get("first_visit", True)` to `from_dict()`.

---

## player.py

### Bug 20: `health_bar()` division by zero (line 287)
**Status**: ✅ FIXED | Session June 18  
**Severity**: 🔴 CRITICAL  
**Problem**: If `hardiness = 0`, then `hp_max = 0`, division by zero crash  
**Fix Applied**: Added guard `if self.hp_max <= 0: return "HP [░░░░░░░░░░░░░░░░░░░░] 0/0"` before division

---

### Bug 21: `max_carry_weight` hardcoded, not synced from character (line 112)
**Status**: ✅ FIXED | Session June 18  
**Severity**: 🔴 CRITICAL  
**Problem**: `Player` defaulted to 100 hardcoded. Engine never passed `character.carry_capacity`, so tavern and adventure enforced different carry limits.  
**Fix Applied**: Added `max_carry_weight=character.carry_capacity` to `Player(...)` constructor call in `Engine.__init__()` — carry limit now derived from `hardiness * 10` consistently in both tavern and adventure.

---

## tavern.py (continued)

### Bug 22: Stale class-system references crash wizard shop (tavern.py)
**Status**: ✅ FIXED | Session June 18  
**Severity**: 🔴 CRITICAL  
**Problem**: `tavern.py` still referenced attributes from an old class+mana design that no longer exists on `Character`. Triggered immediately on `talk to wizard` / `talk to aldric`.  
**Attributes that don't exist**: `character.char_class`, `character.spells`, `character.mana`, `character.mana_max`  
**Locations fixed**:
- `_spell_price` (line 161): removed Fighter double-price penalty
- `show_spells` (lines 355–371): rewrote to use `spell_proficiencies` dict; removed mana display
- `run_wizard_shop` available spells (line 453): replaced `char_class`/`character.spells` with `spell_proficiencies.get(k) is None`
- `run_wizard_shop` status line (line 485): removed Sorcerer-only check; shows learned spells from `spell_proficiencies`
- `run_wizard_shop` buy spell (line 525): replaced `character.spells.append(key)` with `spell_proficiencies[key] = random.randint(25, 75)`  
**Testing**: `talk to wizard` → shop opens; buy spell → proficiency set 25–75%; `spells` command → shows proficiency %

---

## Bug Summary Table

| # | Bug | File | Severity | Status | Session | Time |
|---|-----|------|----------|--------|---------|------|
| 1 | self.roll() crash | engine.py | 🔴 CRITICAL | ✅ FIXED | S1 | 1 min |
| 2 | EXIT_TAVERN stuck | engine.py | 🔴 CRITICAL | ✅ FIXED | S1 | 10 min |
| 3 | Color key | engine.py | 🟡 MEDIUM | ✅ FIXED | Pre-existing | — |
| 4 | Consume drops item | engine.py | 🟠 HIGH | ✅ FIXED | Pre-existing | — |
| 5 | NameError | engine.py | 🟡 MEDIUM | ✅ FIXED | Pre-existing | — |
| 6 | Death HP sync | engine.py | 🔴 CRITICAL | ✅ FIXED | S1 | 2 min |
| 7 | Commands not dispatched | engine.py | 🟠 HIGH | ✅ FIXED | S2 | 10 min |
| 8 | Speed spell no effect | engine.py | 🟠 HIGH | ✅ FIXED | S2 | 15 min |
| 9 | Failed flee no penalty | engine.py | 🟠 HIGH | ✅ FIXED | S2 | 5 min |
| 10 | Auto-attack reversed | engine.py | 🟠 HIGH | ✅ FIXED | S2 | 2 min |
| 11 | savefile param ignored | tavern.py | 🟡 MEDIUM | ✅ FIXED | Pre-existing | — |
| 12 | Duplicate definition | tavern.py | 🟡 MEDIUM | ✅ FIXED | Pre-existing | — |
| 13 | Unreachable code | tavern.py | 🟡 MEDIUM | ✅ FIXED | S3 | 5 min |
| 14 | Dead code | tavern.py | 🟢 LOW | ✅ FIXED | S4 | 1 min |
| 15 | Dead alias | command_parser.py | 🟢 LOW | ✅ FIXED | S4 | 1 min |
| 16 | Bad docstring | command_parser.py | 🟢 LOW | ✅ FIXED | S4 | 2 min |
| 17 | Silent fail | engine.py | 🟢 LOW | ✅ FIXED | S4 | 2 min |
| 18 | Monster serialization | world.py | 🟡 MEDIUM | ✅ FIXED | S3 | 2 min |
| 19 | Room serialization | world.py | 🟡 MEDIUM | ✅ FIXED | S3 | 2 min |
| 20 | Div by zero | player.py | 🔴 CRITICAL | ✅ FIXED | S1 | 3 min |
| 21 | Carry weight | player.py | 🔴 CRITICAL | ✅ FIXED | S1 | 5 min |
| 22 | Stale class-system refs crash wizard shop | tavern.py | 🔴 CRITICAL | ✅ FIXED | S1 | 15 min |

---

## Fix Roadmap

### ✅ Session 1 — Critical Fixes (June 17)
**Bugs Fixed**: #1, #2, #6, #20, #21, #22  
**Also**: Movement system, item persistence, character loading, command parsing

### ✅ Session 2 — High Priority (June 18)
**Bugs Fixed**: #7, #8, #9, #10  
**Also verified pre-fixed**: #4 (consume), #3 (color key)

### ✅ Session 3 — Medium Priority (June 18, continued)
**Bugs Fixed**: #13, #18, #19  
**Verified pre-fixed**: #5, #11, #12

### ✅ Session 4 — Low Priority (June 18, continued)
**Bugs Fixed**: #14, #15, #16, #17  
**Verified pre-fixed**: #3, #4

### 🏁 All bugs resolved — no outstanding issues

---

## Testing Status

### ✅ Session June 17 Testing Complete
```
✅ Character creation/loading
✅ Adventure entry/exit (movement working)
✅ Item persistence (across sessions)
✅ Combat (with and without weapons)
✅ Spell system (casting, proficiency)
✅ Command parsing (full and abbreviated)
✅ Tavern menu operations
```

### ✅ All Systems Verified Fixed
```
✅ Unarmed combat (no roll crash — Bug 1)
✅ Adventure exit (EXIT_TAVERN flow — Bug 2)
✅ Death/revival (HP sync, healing cost — Bug 6)
✅ Carry weight (synced from character — Bug 21)
✅ Health bar (div-by-zero guard — Bug 20)
✅ Speed spell (now affects hit/dodge — Bug 8)
✅ Flee combat (monster counter-attack — Bug 9)
✅ Room entry combat (monster attacks first — Bug 10)
✅ eat/drink/open/close/unlock/talk commands (Bug 7)
✅ Monster XP serialization (Bug 18)
✅ Room first_visit serialization (Bug 19)
✅ Wizard shop (proficiency system — Bug 22)
```

---

---

**Prepared by**: Session Analysis, June 17–18, 2026  
**For**: Rick (Eamon Redux Developer)  
**Status**: All 22 known bugs resolved. Document retained as history.
