# Item Persistence Bug - Root Cause & Fix

**Critical Issue**: Items (like the axe Thoran bought) disappeared after exiting an adventure

**Root Cause**: Character stats were saved on exit, but **items were never saved back to file**

---

## What Happened

When you exited the Beginner's Cave:

```
✅ Character stats synced back:
   - HP updated
   - XP gained
   - Gold changed
   - Proficiencies updated
   - character.save() called

❌ ITEMS NEVER SAVED:
   - Axe you bought: LOST
   - No code called _save_carried_items()
   - Items file was corrupted/overwritten
```

---

## The Bug (In engine.py)

At **adventure exit points** (WIN/DIED/QUIT), the code did:

```python
# Sync stats back
character.spell_proficiencies = engine.player.spell_proficiencies.copy()
character.weapon_proficiencies = engine.player.weapon_proficiencies.copy()
character.hp = engine.player.hp
character.gold = engine.player.gold
character.xp = engine.player.xp
character.save()  # ← Saves character

# ❌ MISSING: Code to save items!
# Items carried during adventure are lost
```

---

## The Fix

### 1. Added Helper Function

New function `_save_carried_items()` in engine.py:

```python
def _save_carried_items(character, world) -> None:
    """Save all carried items back to character's items file."""
    safe_name = character.name.lower().replace(" ", "_")
    items_path = os.path.join("characters", f"{safe_name}_items.json")
    
    os.makedirs("characters", exist_ok=True)
    
    # Get all artifacts that are carried (room_id is None)
    carried = [a for a in world.artifacts.values() if a.room_id is None]
    
    # Convert to dicts and save
    with open(items_path, "w") as f:
        json.dump([a.to_dict() for a in carried], f, indent=2)
```

### 2. Added Calls at Exit Points

**WIN condition** (line 1316):
```python
character.save()
_save_carried_items(character, engine.world)  # ✅ NEW
return 1
```

**DIED condition** (line 1335):
```python
character.save()
_save_carried_items(character, engine.world)  # ✅ NEW
return 2
```

**QUIT condition** (line 1345):
```python
character.save()
_save_carried_items(character, engine.world)  # ✅ NEW
print(engine.tc("Progress saved.", "sys"))
```

---

## How It Works

### Load Phase (Adventure Start)
```
1. engine.__init__()
   → _load_character_items(character)
   → Reads thoran_items.json
   → Adds items to world.artifacts
```

### Play Phase
```
2. Player is in adventure
   → Uses items (equips, drinks, eats)
   → Items remain in world.artifacts
   → Some room_id = None (carried)
   → Some room_id = <room> (dropped)
```

### Save Phase (Adventure End) - **NOW FIXED**
```
3. run_adventure() returns (WIN/DIED/QUIT)
   → character.save() syncs stats
   → _save_carried_items() syncs inventory ✅ NEW
   → Saves all carried items (room_id = None) to thoran_items.json
   → Returns to tavern
```

### Next Load Phase
```
4. Next adventure:
   → Items are in thoran_items.json
   → _load_character_items() reloads them
   → Player can use saved items
```

---

## Testing the Fix

### Step 1: Reset items file
```bash
cd ~/git/Eamon
python3 fix_items_properly.py
```

### Step 2: Update engine.py
```bash
# Copy the fixed engine.py from outputs
```

### Step 3: Full persistence test
```bash
python3 tavern.py

# 1. Load Thoran
# 2. Buy an axe: b → 1 (buy axe)
# 3. Check inventory: inv
#    Should show: Axe (1)
# 4. Enter adventure: adventure → 1
# 5. Walk around a few rooms: n, look, etc.
# 6. Exit adventure: q → y (save)
# 7. Reload tavern: python3 tavern.py
# 8. Load Thoran: 1
# 9. Check inventory: inv
#    Should still show: Axe (1) ✅
```

---

## File Changes

| File | Change | Why |
|------|--------|-----|
| engine.py | Added `_save_carried_items()` function | Serialize items on exit |
| engine.py | Call at WIN (line 1316) | Save items when adventure won |
| engine.py | Call at DIED (line 1335) | Save items when character dies |
| engine.py | Call at QUIT (line 1345) | Save items when player quits |

---

## Related Items File Issues

The items file corruption from earlier was likely caused by:
1. `_load_carried()` failing due to corrupted file
2. Character data accidentally being saved to the items file
3. OR items never being saved in the first place

Now with this fix:
- ✅ Items are properly saved on adventure exit
- ✅ Items persist across sessions
- ✅ Character items file stays separate from character file

---

## Prevention for Future

This fix ensures:
- **Item Persistence**: Items saved when adventure ends ✅
- **Separate Storage**: Character and items files kept separate ✅
- **Three Exit Points**: WIN, DIED, QUIT all save items ✅
- **No Data Loss**: Inventory preserved across sessions ✅

---

## Next Steps

1. ✅ Fix items file (reset to empty list)
2. ✅ Fix engine.py (add item saving on exit)
3. 🎮 Test: Buy item → adventure → exit → reload → verify item still there
4. 📝 Commit to GitHub

Let's test this properly and confirm items persist! 🎯
