# Movement Bug - Indentation Error in cmd_go()

**Issue**: Moving south (or any direction) did nothing - no error, no movement

**Root Cause**: Movement code was **indented into cmd_status()** instead of staying in **cmd_go()**

---

## The Bug

In engine.py, cmd_go() had this structure:

```python
def cmd_go(self, direction: str) -> None:
    """Move in a direction."""
    # Check exit exists
    if direction not in room.exits:
        print(self.tc("You can't go that way.", "error"))
        return
    
    # Check for locked exit
    if direction in room.locked_exits:
        ...
        return
    
    # ❌ MISSING: Code to actually move!
    # This was indented into cmd_status() instead!

def cmd_status(self) -> None:
    """Display character status/sheet."""
    print()
    # ... print stats ...
    print()
    
    # Move to new room ← WRONG PLACE! Should be in cmd_go()
    new_room_id = room.exits[direction]
    self.player.room_id = new_room_id
    # ... rest of movement code ...
```

So `cmd_go()` would:
1. ✅ Check if direction exists
2. ✅ Check if exit is locked
3. ❌ Return without moving!

The movement code was never executed because it was in the wrong function.

---

## The Fix

Moved lines 413-431 (movement code) from `cmd_status()` back into `cmd_go()`:

```python
def cmd_go(self, direction: str) -> None:
    """Move in a direction."""
    # ... checks ...
    
    # ✅ Move to new room
    new_room_id = room.exits[direction]
    self.player.room_id = new_room_id

    new_room = self.world.get_room(new_room_id)
    
    if new_room and new_room.first_visit:
        new_room.first_visit = False
        self.look()
    else:
        print(self.tc(f"You go {direction}.", "sys"))
    
    # Check for hostile monsters
    monsters = self.world.monsters_in_room(new_room_id)
    for m in monsters:
        if m.attitude == Attitude.HOSTILE:
            print(self.tc(f"A {m.name} attacks you!", "warn"))
            self.cmd_attack(m.name)
            break

def cmd_status(self) -> None:
    """Display character status/sheet."""
    # ... just stats display ...
```

Now:
1. ✅ Check if direction exists
2. ✅ Check if exit is locked
3. ✅ **Actually move the player!**
4. ✅ Display new room
5. ✅ Check for hostile monsters

---

## Changes

| File | Change | Line |
|------|--------|------|
| engine.py | Moved movement code from cmd_status() to cmd_go() | 413-431 |
| engine.py | Restored cmd_status() to proper state | 404-411 |

---

## Testing

```bash
cd ~/git/Eamon

# Copy fixed engine.py
python3 tavern.py

# 1. Load Thoran
# 2. adventure → 1 (Beginner's Cave)
# 3. s (go south)
#    ✅ Should see: "You go south." + new room description
# 4. Try other directions: n, e, w
#    ✅ Should all work now
```

---

## How This Happened

Likely during code reorganization or merging:
1. Movement code got copied/pasted into cmd_status()
2. cmd_go() copy wasn't updated to include the movement
3. Python indentation made this valid code, but logically broken
4. Silent failure - no errors, just nothing happens

---

## Prevention

- Always verify function bodies are complete
- Movement commands should never end with just `return`
- Add tests for basic movement (n, s, e, w)

**Status**: Fixed ✅ Ready to test!
