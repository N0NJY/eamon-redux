# Character Load Bug - Diagnosis & Fixes

**Issue**: `TypeError: list indices must be integers or slices, not str` when loading saved characters

**Root Cause**: Character JSON files contain a list `[...]` instead of a dictionary `{...}`

---

## Diagnosis

### What Happened
When `Character.load()` reads the JSON file:
```python
def load(name: str) -> Optional["Character"]:
    with open(path) as f:
        return Character.from_dict(json.load(f))  # ← json.load() returns LIST, not DICT
```

The file contains something like:
```json
[
  { "name": "sword", "type": "weapon", ... },
  { "name": "shield", "type": "armor", ... }
]
```

Instead of:
```json
{
  "name": "Thoran",
  "hardiness": 8,
  "agility": 8,
  ...
}
```

This suggests **character files got overwritten with items data**.

---

## How to Diagnose

### Step 1: Run the diagnostic script
```bash
cd ~/git/Eamon
python3 diagnose_characters.py
```

This will show:
- ✅ If files are correct (DICT structure)
- ❌ If files are corrupted (LIST structure)
- Missing fields
- Detailed structure information

### Step 2: Inspect manually
```bash
cat characters/Thoran.json
```

If you see `[` at the start, it's a list (corrupted).  
If you see `{` at the start, it's a dict (correct).

---

## How to Fix

### Option A: Auto-Repair (Recommended)
```bash
python3 fix_characters.py
```

This will:
1. ✅ Backup all corrupted files (.backup extension)
2. ✅ Detect list vs. dict corruption
3. ✅ Restore character with default stats
4. ✅ Preserve character name and level

**Result**: Character loads, stats reset to defaults (you keep name/level/XP)

### Option B: Manual Deletion
If you want fresh characters:
```bash
rm characters/*.json
```

Then create new characters through the tavern menu.

---

## Root Cause Analysis

### Why Did This Happen?

Looking at the code, there are two possible causes:

**Possibility 1: Items file got renamed to character name**
```
characters/Thoran_items.json  → Got renamed/copied → characters/Thoran.json
```

The items JSON is a list, character JSON is a dict.

**Possibility 2: Wrong serialization in save**
```python
# This would save a list:
json.dump(character.items, f)  # ← Wrong! Should be character.to_dict()

# Should be:
json.dump(character.to_dict(), f)  # ← Correct
```

### Current Code is Correct
Looking at `character.py`:
```python
def save(self) -> None:
    with open(self._path(self.name), "w") as f:
        json.dump(self.to_dict(), f, indent=2)  # ✅ Correct
```

So this is likely a **file corruption issue** from a previous version or manual intervention.

---

## Prevention Going Forward

### Add Validation to Load
Modify `character.py` `load()` method to detect and handle this:

```python
@staticmethod
def load(name: str) -> Optional["Character"]:
    path = Character._path(name)
    if not os.path.exists(path):
        return None
    
    with open(path) as f:
        data = json.load(f)
    
    # ← NEW: Detect and handle list corruption
    if isinstance(data, list):
        print(f"ERROR: {name}.json contains a list, not a character.")
        print(f"This file appears to be corrupted (items list saved as character).")
        print(f"Use 'python3 fix_characters.py' to repair.")
        return None
    
    return Character.from_dict(data)
```

### Enhanced to_dict() Documentation
Add a comment to `to_dict()`:
```python
def to_dict(self) -> dict:
    """
    Serialize character to dict for JSON storage.
    MUST return a dict, not a list!
    """
    return { ... }
```

---

## Testing the Fix

### After repair, verify:
```bash
# 1. Run diagnostic
python3 diagnose_characters.py

# 2. Start tavern
python3 tavern.py

# 3. Try loading Thoran
# Should show: "1. Thoran               H:8 A:8 Beginner"
# Should load without crashes

# 4. Quick adventure test
# adventure → select adventure → enter game
# Should not crash when entering/exiting

# 5. Check persistence
# After exiting adventure, start tavern again
# Thoran should still be there with saved data
```

---

## Files Provided

1. **diagnose_characters.py** — Inspect all character JSON files
2. **fix_characters.py** — Auto-repair corrupted files
3. **This document** — Explanation and prevention

---

## Quick Action Plan

1. **Diagnose**: `python3 diagnose_characters.py`
2. **Fix**: `python3 fix_characters.py`
3. **Test**: `python3 tavern.py` → load Thoran → adventure
4. **Verify**: Exit and reload, character should persist

---

## Questions to Answer

To understand what happened:
- When was Thoran last saved before the crash?
- Did you modify any files manually?
- Are there any `*.backup` files in the characters directory?
- Check: `ls -la characters/`

Let me know what the diagnostic shows and we can debug further if needed!
