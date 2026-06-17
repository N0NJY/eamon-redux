# Character Load Bug - Fixed ✅

## The Problem

When running `tavern.py` and trying to load a saved character (e.g., Thoran), the game crashed with:
```
TypeError: list indices must be integers or slices, not str
```

## Root Cause

**File listing bug in `character.py`**

The `Character.list_all()` method returns ALL `.json` files in the `characters/` directory:
```python
# BEFORE (BUGGY):
def list_all() -> list[str]:
    return [f[:-5] for f in sorted(os.listdir(CHARACTERS_DIR))
            if f.endswith(".json")]
```

This includes:
- ✅ `thoran.json` → "thoran" (character file)
- ❌ `thoran_items.json` → "thoran_items" (items file, contains LIST)

When tavern tried to load "thoran_items", it called `Character.load("thoran_items")`, which:
1. Opened `characters/thoran_items.json`
2. Read JSON list: `[{ "name": "sword", ... }]`
3. Passed list to `Character.from_dict(d)` expecting dict
4. Crashed when trying `d["name"]` on a list

## The Fix

**Filter out `*_items.json` files:**
```python
# AFTER (FIXED):
def list_all() -> list[str]:
    if not os.path.isdir(CHARACTERS_DIR):
        return []
    return [f[:-5] for f in sorted(os.listdir(CHARACTERS_DIR))
            if f.endswith(".json") and not f.endswith("_items.json")]
            # ↑ NEW: Exclude items files
```

Now `list_all()` returns only:
- ✅ "thoran" (from thoran.json)

And ignores:
- ❌ "thoran_items" (from thoran_items.json)

## What Changed

| File | Change | Line |
|------|--------|------|
| character.py | Added filter `and not f.endswith("_items.json")` | 257 |

## Testing the Fix

```bash
cd ~/git/Eamon

# 1. Replace character.py with fixed version
# (copy from outputs)

# 2. Start tavern
python3 tavern.py

# 3. You should see:
#    1. Thoran               H:8 A:8 Beginner
#    (NOT thoran_items!)

# 4. Load Thoran
# (should work without crash)

# 5. Do a quick adventure and exit

# 6. Reload tavern
# (Thoran should still be there with saved data)
```

## Expected Behavior After Fix

✅ Tavern menu shows only actual characters (Thoran)  
✅ No "thoran_items" pseudo-character  
✅ Loading Thoran works  
✅ Character persistence works  
✅ Items are saved separately in thoran_items.json (correct)  

## File Structure

```
characters/
├── thoran.json            ← Character data (dict structure)
└── thoran_items.json      ← Character's carried items (list structure)
                              This is properly ignored now
```

## Why This Wasn't Caught Before

- The fix to add items persistence (`_load_character_items()` in engine.py) correctly saves items to `*_items.json`
- But `Character.list_all()` was never updated to exclude these files
- So it accidentally treated items files as character files

## Commit Message

```
Fix: Character list ignores items files

Character.list_all() was returning all .json files including *_items.json,
causing tavern to try loading item lists as character data.

Fix: Filter out *_items.json files - only return actual character files.

This prevents "thoran_items" from appearing as a loadable character
and allows proper character persistence without crashes.
```

## Related Code

- **character.py** — `list_all()` method (LINE 252-257)
- **character.py** — `load()` method (LINE 237-242) - unchanged but now works properly
- **character.py** — `from_dict()` method (LINE 211-234) - now receives proper dict

---

**Status**: Ready to deploy  
**Impact**: Low - only affects character selection menu  
**Risk**: None - items files are unaffected, items are still saved properly
