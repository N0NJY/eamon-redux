# PHASE 2c: Room Flag Editing in Designer

**Status**: Ready for Claude Code implementation  
**Dependency**: Phase 2b completed  
**Estimated Time**: 1-2 hours

---

## Objective

Enhance `designer.py` room editing menu to allow setting flags that control room behavior:
- Exit room (way out of adventure)
- Win room (victory condition location)
- Event triggers (special room mechanics)

---

## Current State

**designer.py edit_room() (around line 420):**
```python
def edit_room(self) -> None:
    rid = self._pick_room("Edit which room?")
    if rid is None:
        return

    r = self.world.rooms[rid]

    print(f"\n EDIT ROOM #{rid}")

    r.name = prompt("Name", r.name)
    r.description = prompt("Description", r.description)
    r.is_dark = prompt_bool("Is it dark?", r.is_dark)

    print(" Room updated.")
```

---

## Deliverable

After edit_room() completes (before "print Room updated"), add a submenu for flags:

```python
def _edit_room_flags(self, room) -> None:
    """Edit flags for a room (exit, win room, event trigger, etc.)."""
    print(f"\n ROOM FLAGS — {room.name} (#{room.id})")
    print(f" {self.hr('─', 40)}")
    
    flags = room.flags or {}
    
    # --- EXIT ROOM ---
    is_exit = prompt_bool("Is this an exit room (way out)?", flags.get('is_exit', False))
    if is_exit:
        flags['is_exit'] = True
    else:
        flags.pop('is_exit', None)
    
    # --- WIN ROOM ---
    is_win = prompt_bool("Is this a win room (victory condition)?", flags.get('is_win_room', False))
    if is_win:
        win_cond = prompt("Win condition (e.g., 'has_rescued_girl')", flags.get('win_condition', ''))
        win_msg = prompt("Victory message", flags.get('win_dialogue', 'You have won!'))
        flags['is_win_room'] = True
        flags['win_condition'] = win_cond
        flags['win_dialogue'] = win_msg
    else:
        flags.pop('is_win_room', None)
        flags.pop('win_condition', None)
        flags.pop('win_dialogue', None)
    
    # --- EVENT TRIGGER ---
    triggers = prompt_bool("Does entering trigger an event?", flags.get('triggers_event', False))
    if triggers:
        event_id = prompt("Event ID to trigger", flags.get('triggers_event', ''))
        flags['triggers_event'] = event_id
    else:
        flags.pop('triggers_event', None)
    
    room.flags = flags if flags else {}
    print(" Room flags updated.")
```

---

## Integration Points

**1. In edit_room() method:**

Replace the "print Room updated" line with:

```python
    # Ask if user wants to edit flags
    if prompt_bool("Edit flags (special behaviors)?", False):
        self._edit_room_flags(r)
    
    print(" Room updated.")
```

**2. Verify flags are saved:**

Make sure `world.save()` already handles the flags dict on rooms (it should, from Phase 1).

**3. Test:**
```bash
python3 designer.py adventures/sample
# Edit a room
# Set flags
# Save and check adventure.json for flags dict
```

---

## Expected JSON Output

After editing a room with flags, adventure.json should contain:

```json
{
  "id": 10,
  "name": "The Exit",
  "description": "You see daylight ahead. A way out!",
  "exits": { "north": 1 },
  "locked_exits": {},
  "is_dark": false,
  "flags": {
    "is_exit": true,
    "is_win_room": true,
    "win_condition": "has_rescued_girl",
    "win_dialogue": "You escape with the girl! You've won!"
  }
}
```

---

## Checklist for Claude Code

- [ ] View current edit_room() method
- [ ] Add _edit_room_flags() method
- [ ] Integrate flag editing into edit_room()
- [ ] Test: Create room with flags
- [ ] Verify flags save to adventure.json
- [ ] Verify flags load from adventure.json when editing again
- [ ] Test win condition check works (load adventure and test)

---

## Notes

- Flags should be optional (room.flags can be empty dict)
- If user says "no" to a flag, remove it from flags dict (don't save False)
- The prompt_bool, prompt, hr() functions already exist in designer.py
- Make sure editing an existing room LOADS its flags first
- Win condition text is freeform (engine will interpret it)

---

## Claude Code Session Start

```
I'm implementing Phase 2c: Room Flag Editing for Eamon Redux designer.

PHASE 2c: Room Flag Editing

Reference document: PHASE_2c_ROOM_FLAG_EDITING.md

Current situation:
- Phase 2b (artifact flag editing) completed ✅
- world.py has flags dict on Room ✅
- designer.py has basic room editing (no flags)

Deliverable:
Add flag-editing submenu to designer.py room editing.
When editing a room, user can set:
- is_exit (way out of adventure)
- is_win_room (victory condition location)
- win_condition (what needs to be true to win)
- win_dialogue (victory message)
- triggers_event (special event firing)

Repository: ~/git/Eamon/eamon-redux/

Steps:
1. View designer.py edit_room() method (around line 420)
2. I'll provide the _edit_room_flags() code to add
3. Integrate it into edit_room()
4. Test: python3 designer.py adventures/sample

Let's start: View the edit_room() method.
```

---

**Next**: After Phase 2c passes testing, move to **PHASE_3_ENGINE_REFACTORING.md**
