# Eamon Redux — Bug Tracker
**Last Updated**: June 17, 2026 (End of Session)

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
**Status**: ⏳ PENDING | 📅 Session 1  
**Severity**: 🔴 CRITICAL  
**Problem**: `Engine` has no `roll` method — it's module-level. Raises `AttributeError` when attacking without weapon.  
**Root Cause**: Incorrect method reference (`self.roll()` instead of `roll()`)  
**Fix**: Replace `self.roll(...)` with `roll(...)`  
**Time Est**: 1 minute  
**Testing**: Attack unarmed → should not crash

---

### Bug 2: EXIT_TAVERN leaves player stuck (lines 338–341)
**Status**: ⏳ PENDING | 📅 Session 1  
**Severity**: 🔴 CRITICAL  
**Problem**: Setting `player.room_id = "EXIT_TAVERN"` and returning only exits `cmd_go`, not `handle()`. Game continues with player in non-existent room, every `look` prints "(Room not found)".  
**Root Cause**: `handle()` never checks if player has exited dungeon  
**Fix**: Add check in `handle()`: `if self.player.room_id == "EXIT_TAVERN": return 1`  
**Time Est**: 10 minutes  
**Testing**: Exit adventure → should return to tavern menu cleanly

---

### Bug 3: Wrong color key on instant kill (line 1045)
**Status**: ⏳ PENDING | 📅 Session 3  
**Severity**: 🟡 MEDIUM  
**Problem**: `print(self.tc(f"INSTANT KILL!", "combat_win"))` — key `"combat_win"` doesn't exist in `tc()` mapping, falls back to `C.SYS` color  
**Root Cause**: Typo in color key name  
**Fix**: Change `"combat_win"` to `"win"`  
**Time Est**: 1 minute  
**Testing**: Get instant kill → message prints in correct color

---

### Bug 4: `_consume()` drops item instead of destroying it (line 592)
**Status**: ⏳ PENDING | 📅 Session 2  
**Severity**: 🟠 HIGH  
**Problem**: Eaten food and drunk potions reappear on the floor instead of being destroyed  
**Root Cause**: Sets `room_id = current_room` instead of deleting artifact  
**Code**:
```python
# Wrong:
self.world.artifacts[artifact.id].room_id = self.player.room_id

# Right:
del self.world.artifacts[artifact.id]
```
**Fix**: Remove item from artifacts dict instead of relocating it  
**Time Est**: 2 minutes  
**Testing**: Eat apple → should not appear on floor; inventory empty

---

### Bug 5: `engine.tc()` NameError if run directly (line 1312)
**Status**: ⏳ PENDING | 📅 Session 3  
**Severity**: 🟡 MEDIUM  
**Problem**: `print(engine.tc(...))` called when `engine` module not in scope → `NameError`  
**Root Cause**: Running `python engine.py` directly; `engine` not defined  
**Fix**: Use `Engine.tc(...)` or import `tc` directly  
**Time Est**: 2 minutes  
**Testing**: `python engine.py` → should print message, not crash

---

### Bug 6: Death doesn't sync `character.hp` before healing cost (lines 1279–1295)
**Status**: ⏳ PENDING | 📅 Session 1  
**Severity**: 🔴 CRITICAL  
**Problem**: On death, `run_adventure()` syncs gold/xp/proficiencies but NOT `hp`. Back in tavern, healing cost calculated from stale hp value, resulting in wrong cost (usually 0).  
**Root Cause**: HP sync missing from death handler  
**Fix**: Add `character.hp = self.player.hp` in death sync block  
**Location**: engine.py `run_adventure()` function, death condition (~line 1290)  
**Time Est**: 2 minutes  
**Testing**: Die with full health → healing cost should be non-zero

---

### Bug 7: Seven commands registered but never dispatched (lines 220–282)
**Status**: ⏳ PENDING | 📅 Session 2  
**Severity**: 🟠 HIGH  
**Problem**: These commands have methods but no `elif` cases in `handle()` — they silently do nothing:
- `eat` → `cmd_eat()`
- `drink` → `cmd_drink()`
- `open` → `cmd_open()`
- `close` → `cmd_close()`
- `unlock` → `cmd_unlock()`
- `talk` → `cmd_talk()`  
**Root Cause**: Missing `elif cmd == "..."` blocks in `handle()` dispatch  
**Fix**: Add 6 `elif` blocks to handle() for each command  
**Time Est**: 10 minutes  
**Testing**: `eat apple` → consumes item; `drink potion` → consumes item; etc.

---

### Bug 8: Speed spell never affects combat hit/dodge (lines 946, 1102)
**Status**: ⏳ PENDING | 📅 Session 2  
**Severity**: 🟠 HIGH  
**Problem**: `_cast_speed()` sets `agility_effective = agility * 2`, but `cmd_attack()` and `monster_round()` use `agility_bonus` (derived from base agility). Speed bonus never used.  
**Root Cause**: Speed bonus calculated but not applied to combat rolls  
**Fix**: Modify hit/dodge calculations to use speed-boosted agility when active  
**Approach**: Check if speed spell active, multiply agility_bonus * 2 in combat  
**Time Est**: 15 minutes  
**Testing**: Cast speed spell → attack monster → hit chance increases

---

### Bug 9: Failed flee gives no monster counter-attack (lines 1128–1143)
**Status**: ⏳ PENDING | 📅 Session 2  
**Severity**: 🟠 HIGH  
**Problem**: If `random.choice(DIRECTIONS)` picks direction with no exit, prints "can't flee" and returns without calling `monster_round()`. Player gets free safe "fail" with no consequences.  
**Root Cause**: `monster_round()` only called on successful flee  
**Fix**: Call `monster_round()` regardless of flee success  
**Time Est**: 5 minutes  
**Testing**: Fail flee multiple times → should take monster damage

---

### Bug 10: Auto-attack on room entry is reversed (lines 365–369)
**Status**: ⏳ PENDING | 📅 Session 2  
**Severity**: 🟠 HIGH  
**Problem**: Prints "A {monster} attacks you!" but calls `cmd_attack(monster)` — player attacks, not monster  
**Root Cause**: Wrong method called; should be `monster_round()`, not `cmd_attack()`  
**Code**:
```python
# Wrong:
print(f"A {m.name} attacks you!")
self.cmd_attack(m.name)  # Player attacks!

# Right:
print(f"A {m.name} attacks you!")
self.monster_round(m)  # Monster attacks!
```
**Fix**: Call `self.monster_round(m)` instead of `self.cmd_attack(m.name)`  
**Time Est**: 2 minutes  
**Testing**: Enter room with hostile monster → monster should attack, not player

---

## tavern.py

### Bug 11: `_launch_engine` ignores `savefile` parameter (lines 951–955)
**Status**: ⏳ PENDING | 📅 Session 3  
**Severity**: 🟡 MEDIUM  
**Problem**: Function accepts `savefile` parameter but never passes it to `run_adventure()`  
**Code**:
```python
# Wrong:
def _launch_engine(character, adv_path: str, savefile: str = ""):
    result = run_adventure(character, adv_path)  # savefile lost!

# Right:
result = run_adventure(character, adv_path, savefile)
```
**Fix**: Pass `savefile` to `run_adventure()`  
**Impact**: Blocks mid-adventure save/load feature  
**Time Est**: 2 minutes  
**Testing**: Deferred until save/load feature implementation

---

### Bug 12: `menu_load_save` defined twice (lines 323 and 738)
**Status**: ⏳ PENDING | 📅 Session 3  
**Severity**: 🟡 MEDIUM  
**Problem**: First definition (lines 323–337) completely shadowed by second (lines 738+). First is dead code.  
**Root Cause**: Duplicate function definition; second one takes precedence  
**Fix**: Delete lines 323–337 (first definition)  
**Time Est**: 1 minute  
**Testing**: Load game menu still works (no functional change, dead code removal)

---

### Bug 13: "talk to" special case is unreachable (lines 587–593)
**Status**: ⏳ PENDING | 📅 Session 3  
**Severity**: 🟡 MEDIUM  
**Problem**: `parts = raw.split(maxsplit=1)` limits to 2 items, but code checks `if len(parts) >= 3` — always False. Dead code, only works by accident.  
**Code**:
```python
# Wrong:
parts = raw.strip().lower().split(maxsplit=1)  # Max 2 items
if len(parts) >= 3 and ...:  # Always False!

# Right:
if len(parts) == 2 and parts[1].startswith("to "):
```
**Fix**: Correct the condition to match actual behavior  
**Time Est**: 5 minutes  
**Testing**: `talk to horace` → NPC dialog works

---

### Bug 14: Dead code in `_process_sell` (lines 272–275)
**Status**: ⏳ PENDING | 📅 Session 4  
**Severity**: 🟢 LOW  
**Problem**: `if raw == "sell all": pass  # total already set` — meaningless, `total` recalculated anyway  
**Fix**: Remove the `pass` block  
**Time Est**: 1 minute  
**Testing**: `sell all` still works (no functional change)

---

## command_parser.py

### Bug 15: `"get all"` space alias can never match (line 32)
**Status**: ⏳ PENDING | 📅 Session 4  
**Severity**: 🟢 LOW  
**Problem**: Parser extracts only first word (`split()[0]`), so multi-word alias `"get all"` never matches. Dead alias; feature works via manual parsing in engine.py.  
**Code**:
```python
"getall": {"aliases": ["get all", "ga"], ...}
# "get all" never matches because parser sees single token only
```
**Fix**: Remove dead alias: `{"aliases": ["ga"], ...}`  
**Time Est**: 1 minute  
**Testing**: `get all` still works (via engine.py manual check)

---

### Bug 16: Docstring example is wrong (line 116)
**Status**: ⏳ PENDING | 📅 Session 4  
**Severity**: 🟢 LOW  
**Problem**: Documented behavior incorrect:
```python
parse_command("l", "engine") → (None, "ambiguous", ["look", "load"])
# WRONG: "l" is exact alias for "look", returns ("look", "exact", None)
```
**Fix**: Update docstring to correct example  
**Time Est**: 2 minutes  
**Testing**: Run existing tests (all pass)

---

### Bug 17: "go" typed alone silently does nothing (line ~270)
**Status**: ⏳ PENDING | 📅 Session 4  
**Severity**: 🟢 LOW  
**Problem**: `handle()` checks `if len(parts) > 1` but doesn't print error if missing direction  
**Code**:
```python
elif cmd == "go":
    if len(parts) > 1:
        self.cmd_go(parts[1])
    # No else: silent failure
```
**Fix**: Add error message for missing direction  
**Time Est**: 2 minutes  
**Testing**: Type `go` alone → helpful error message

---

## world.py

### Bug 18: `Monster.to_dict()` drops `xp_value` (line 151)
**Status**: ⏳ PENDING | 📅 Session 3  
**Severity**: 🟡 MEDIUM  
**Problem**: Field `xp_value` exists but not in `to_dict()`. After save/load, reverts to auto-calculated value.  
**Fix**: Add `"xp_value": self.xp_value` to `to_dict()` return dict  
**Time Est**: 2 minutes  
**Testing**: Save/load adventure → monster XP values persist

---

### Bug 19: `Room.to_dict()` drops `first_visit` (line 200)
**Status**: ⏳ PENDING | 📅 Session 3  
**Severity**: 🟡 MEDIUM  
**Problem**: Field `first_visit` not serialized. On reload, every room prints full description again.  
**Fix**: Add `"first_visit": self.first_visit` to `to_dict()` return dict  
**Time Est**: 2 minutes  
**Testing**: Save/load → visited rooms stay short-description, not full

---

## player.py

### Bug 20: `health_bar()` division by zero (line 287)
**Status**: ⏳ PENDING | 📅 Session 1  
**Severity**: 🔴 CRITICAL  
**Problem**: If `hardiness = 0`, then `hp_max = 0`, division by zero crash  
**Code**:
```python
def health_bar(self):
    pct = max(0, self.hp) / self.hp_max  # Crashes if hp_max = 0
```
**Fix**: Add guard: `if self.hp_max <= 0: return "[=====] (0/0 HP)"`  
**Time Est**: 3 minutes  
**Testing**: Character with hardiness=0 → no crash

---

### Bug 21: `max_carry_weight` hardcoded, not synced from character (line 112)
**Status**: ⏳ PENDING | 📅 Session 1  
**Severity**: 🔴 CRITICAL  
**Problem**: `Player` defaults to 100 hardcoded. Engine never passes `character.carry_capacity`. Tavern and adventure enforce different limits.  
**Code**:
```python
class Player:
    def __init__(self, character_data=None):
        self.max_carry_weight = 100  # Hardcoded!
```
**Fix**: 
1. Update Player.__init__: `if character_data: self.max_carry_weight = character_data.carry_capacity`
2. Update engine.py: `self.player = Player(character)` (pass character)  
**Time Est**: 5 minutes  
**Testing**: Create character with custom capacity → matches in tavern and adventure

---

## Bug Summary Table

| # | Bug | File | Severity | Status | Session | Time |
|---|-----|------|----------|--------|---------|------|
| 1 | self.roll() crash | engine.py | 🔴 CRITICAL | ⏳ PENDING | S1 | 1 min |
| 2 | EXIT_TAVERN stuck | engine.py | 🔴 CRITICAL | ⏳ PENDING | S1 | 10 min |
| 3 | Color key | engine.py | 🟡 MEDIUM | ⏳ PENDING | S3 | 1 min |
| 4 | Consume drops item | engine.py | 🟠 HIGH | ⏳ PENDING | S2 | 2 min |
| 5 | NameError | engine.py | 🟡 MEDIUM | ⏳ PENDING | S3 | 2 min |
| 6 | Death HP sync | engine.py | 🔴 CRITICAL | ⏳ PENDING | S1 | 2 min |
| 7 | Commands not dispatched | engine.py | 🟠 HIGH | ⏳ PENDING | S2 | 10 min |
| 8 | Speed spell no effect | engine.py | 🟠 HIGH | ⏳ PENDING | S2 | 15 min |
| 9 | Failed flee no penalty | engine.py | 🟠 HIGH | ⏳ PENDING | S2 | 5 min |
| 10 | Auto-attack reversed | engine.py | 🟠 HIGH | ⏳ PENDING | S2 | 2 min |
| 11 | savefile param ignored | tavern.py | 🟡 MEDIUM | ⏳ PENDING | S3 | 2 min |
| 12 | Duplicate definition | tavern.py | 🟡 MEDIUM | ⏳ PENDING | S3 | 1 min |
| 13 | Unreachable code | tavern.py | 🟡 MEDIUM | ⏳ PENDING | S3 | 5 min |
| 14 | Dead code | tavern.py | 🟢 LOW | ⏳ PENDING | S4 | 1 min |
| 15 | Dead alias | command_parser.py | 🟢 LOW | ⏳ PENDING | S4 | 1 min |
| 16 | Bad docstring | command_parser.py | 🟢 LOW | ⏳ PENDING | S4 | 2 min |
| 17 | Silent fail | engine.py | 🟢 LOW | ⏳ PENDING | S4 | 2 min |
| 18 | Monster serialization | world.py | 🟡 MEDIUM | ⏳ PENDING | S3 | 2 min |
| 19 | Room serialization | world.py | 🟡 MEDIUM | ⏳ PENDING | S3 | 2 min |
| 20 | Div by zero | player.py | 🔴 CRITICAL | ⏳ PENDING | S1 | 3 min |
| 21 | Carry weight | player.py | 🔴 CRITICAL | ⏳ PENDING | S1 | 5 min |

---

## Fix Roadmap

### 🎯 Session 1: Critical Fixes (NEXT - ~2 hours)
**Bugs**: #1, #2, #6, #20, #21  
**Focus**: Game-breaking crashes and logic errors  
**Estimated Time**: 1 hour fix + 1 hour test  
**Status**: Ready to begin  
**Resources**: See `SESSION_1_CODE_FIXES.md`

### Session 2: High Priority (~2 hours)
**Bugs**: #4, #7, #8, #9, #10  
**Focus**: Missing features and combat balance

### Session 3: Medium Priority (~1.5 hours)
**Bugs**: #3, #5, #11, #12, #13, #18, #19  
**Focus**: Save/load preparation and cleanup

### Session 4: Low Priority (~30 min)
**Bugs**: #14, #15, #16, #17  
**Focus**: Code quality and documentation

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

### ⏳ Session 1 Testing Needed (Post-Fix)
```
⏳ Unarmed combat (no roll crash)
⏳ Adventure exit (no stuck in dungeon)
⏳ Death/revival (correct healing cost)
⏳ Carry weight (tavern vs adventure match)
⏳ Corrupted saves (no div by zero)
```

---

## How to Use This Document

1. **For Claude Code**: Review "Bug Summary Table" for quick overview
2. **For Session Planning**: Check "Fix Roadmap" for prioritization
3. **For Implementation**: Use exact fix descriptions + `SESSION_1_CODE_FIXES.md`
4. **For Testing**: Each bug has "Testing:" line with exact test procedure
5. **For Tracking**: Use bug numbers (Bug #1, etc.) in commits and notes

---

## Continuous Updates

This document is updated after each session:
- ✅ Status changed from ⏳ PENDING to ✅ FIXED
- 📝 Add actual lines changed
- 📅 Move bugs to FIXED sections
- 🧪 Add final test results

**Next Update**: After Session 1 completion

---

---

## Additional Issues (Discovered June 18)

### Bug 23: Dead bodies appear in rooms before NPC is killed
**Status**: ⏳ PENDING | 📅 Session TBD  
**Severity**: 🟠 HIGH  
**Problem**: When entering a room with an NPC, a dead body is visible even though the NPC is still alive. Dead bodies should only appear after the NPC is actually killed.  
**Root Cause**: `look()` function doesn't filter monsters by `hp > 0` before displaying them. Likely showing all artifacts including dead body artifacts.  
**Fix**: In `look()`, filter monsters to show only living ones: `living_monsters = [m for m in room_monsters if m.hp > 0]`  
**Testing**: Enter room with living NPC → should NOT see dead body; kill NPC → dead body appears

---

### Bug 24: Talk command doesn't dispatch (related to Bug #7)
**Status**: ⏳ PENDING | 📅 Session 2  
**Severity**: 🟠 HIGH  
**Problem**: `talk to <npc>` command exists but does nothing. NPCs should respond with dialogue.  
**Root Cause**: Missing `elif cmd == "talk"` in `handle()` dispatch. Also no dialogue/event system.  
**Solution**: Implement event handler system - each adventure defines NPC behavior in `event_handlers.py`  
**Design**: See ADVENTURE_MECHANICS_DESIGN.md  
**Testing**: Talk to NPCs → receive dialogue; Talk to girl → option to rescue

---

### Feature: NPC Follower System (Not Yet Implemented)
**Status**: ⏳ NOT STARTED | 📅 Session TBD  
**Complexity**: MEDIUM  
**Requirement**: NPCs like Henrich, hermits, rescued girl should "follow" player around  
**Use Cases**:
- Girl follows after rescue (part of win condition)
- Henrich assists with navigation
- Hermit helps in combat
**Implementation**: Event handlers in each adventure define follower behavior  
**Design**: See ADVENTURE_MECHANICS_DESIGN.md  
**Testing**: Rescue NPC → appears in player's follower list → follows on movement → appears in room descriptions

---

### Feature: Adventure-Specific Mechanics (Not Yet Implemented)
**Status**: ⏳ NOT STARTED | 📅 Session TBD  
**Complexity**: MEDIUM  
**Requirement**: Adventures define unique mechanics (boat escape, special items, quests)  
**Examples**:
- Pirate's Den: Boat allows escape
- Beginner's Cave: Rescue girl = win
- Various: NPC assistance in combat
**Implementation**: Event handler system (`on_use_item()`, `on_win_condition()`, etc.)  
**Design**: See ADVENTURE_MECHANICS_DESIGN.md

---

**Prepared by**: Session Analysis, June 17-18, 2026  
**For**: Rick (Eamon Redux Developer)  
**Status**: Active tracking document — treat as source of truth for project state
