# Eamon Redux — Bug List

## engine.py

**Bug 1 — `self.roll()` crash on unarmed combat (line 1016)**
`Engine` has no `roll` method — it's a module-level function. Should be `roll(...)`.
This raises `AttributeError` any time the player attacks without a weapon.

**Bug 2 — EXIT_TAVERN leaves player stuck (lines 338–341)**
`cmd_go` sets `self.player.room_id = "EXIT_TAVERN"` and returns, but this only exits
`cmd_go`, not `handle()`. `handle()` checks win/death (neither triggers), returns 0,
and the game loop continues with the player in a non-existent room. Every subsequent
`look` prints "(Room not found)".

**Bug 3 — Wrong color key on instant kill (line 1045)**
`print(self.tc(f"INSTANT KILL!", "combat_win"))`
The `tc()` mapping has no `"combat_win"` key — it falls back to `C.SYS`. Should be `"win"`.

**Bug 4 — `_consume` drops item in the room instead of destroying it (line 592)**
`self.world.artifacts[artifact.id].room_id = self.player.room_id`
Eaten food and drunk potions reappear on the floor.

**Bug 5 — `engine.tc()` NameError if run directly (line 1312)**
`print(engine.tc("Run via tavern.py", "error"))`
`engine` is not defined in this scope — `Engine` is the class. Crashes with `NameError`.

**Bug 6 — Death doesn't sync `character.hp` before healing cost**
On death, `run_adventure` (lines 1279–1295) syncs gold/xp/proficiencies but not
`character.hp`. Back in `_handle_engine_return`, `hp_lost = character.hp_max -
character.hp` uses the pre-adventure HP value, not 0, so the revival cost is wrong
(likely 0 cost).

---

## tavern.py

**Bug 7 — `_launch_engine` ignores `savefile` parameter (lines 951–955)**
```python
def _launch_engine(character, adv_path: str, savefile: str = ""):
    from engine import run_adventure
    result = run_adventure(character, adv_path)  # savefile never passed
```
Resume/load paths call `_launch_engine(..., savefile=...)` but it's silently dropped.
Saved games always start fresh.

**Bug 8 — `menu_load_save` defined twice (lines 323 and 738)**
The first definition (returns `bool`, uses `list_saves`) is completely shadowed by the
second (returns `None`, uses `list_resumable_games`). The first version is dead code.

**Bug 9 — "talk to" special case is unreachable (lines 587–593)**
```python
parts = raw.strip().lower().split(maxsplit=1)  # max 2 items
if len(parts) >= 3 and ...:                     # always False
```
`maxsplit=1` limits `parts` to 2 elements, so `len(parts) >= 3` is never True.
The block is dead code. It works accidentally because `noun` ends up as `"to horace"`
and `"horace" in "to horace"` is True.

**Bug 10 — Dead code in `_process_sell` (lines 272–275)**
```python
if raw == "sell all":
    pass  # total already set
sold  = [a for a in sellable if id(a) in ids_to_sell]
total = sum(sell_value(a) for a in sold)  # recalculates anyway
```
The `pass` block is meaningless — `total` is unconditionally recalculated on the next line.
