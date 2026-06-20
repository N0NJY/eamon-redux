# Items Load Bug - Diagnosis & Fix

**Issue**: `TypeError: string indices must be integers, not 'str'` when checking inventory in tavern

**Root Cause**: Items JSON file contains a STRING instead of a LIST

---

## The Problem

When you run `inv` in the tavern:
```
tavern.py → handle_tavern_command() 
  → show_inventory() 
    → _load_carried()
      → json.load(f)  ← Returns STRING, not LIST!
        → Artifact.from_dict(d)  ← Tries to access d["id"] on a string character
          → CRASH!
```

The items file should contain:
```json
[
  { "id": 1, "name": "sword", ... },
  { "id": 2, "name": "shield", ... }
]
```

But instead contains something like:
```json
"[{\"id\": 1, ...}]"   ← Double-encoded as a STRING!
```

Or is corrupted/empty.

---

## Diagnosis

### Step 1: Check items files
```bash
cd ~/git/Eamon
python3 diagnose_items.py
```

This will show:
- ✅ If items files are correct (LIST structure)
- ❌ If items files are corrupted (STRING/empty/malformed)
- Details about what's in each item

### Step 2: Inspect manually
```bash
cat characters/thoran_items.json
```

Should start with `[` (array/list)  
Should NOT start with `"` (string)

---

## The Fix

### Option A: Auto-Repair (Recommended)
```bash
python3 fix_items.py
```

This will:
1. ✅ Backup corrupted files (.backup extension)
2. ✅ Detect string/dict/empty corruption
3. ✅ Try to recover items if possible
4. ✅ Reset to empty list `[]` if recovery fails
5. ✅ Remove invalid items from lists

### Option B: Manual Reset
If you want to start fresh:
```bash
rm characters/*_items.json
```

Then:
1. Load Thoran in tavern
2. Buy some items
3. New items file will be created correctly

---

## Root Cause Analysis

### How Items Files Get Corrupted

**Possibility 1: Double JSON encoding**
```python
# WRONG - encodes JSON as a string:
json.dump(json.dumps(items), f)  # ← Extra dumps()!

# RIGHT - encodes items directly:
json.dump(items, f)  # ← Single dump()
```

**Possibility 2: File created by wrong code**
```python
# WRONG - writes string literal:
f.write("[{...}]")  # ← String, not JSON

# RIGHT - uses json.dump:
json.dump([...], f)  # ← Proper JSON encoding
```

**Possibility 3: Empty or corrupted file**
- File created but never written to
- File partially written before crash
- File corrupted by manual editing

### Current Code is Correct
Looking at `tavern.py`:
```python
def _save_carried(character, items: list) -> None:
    with open(_items_path(character), "w") as f:
        json.dump([a.to_dict() for a in items], f, indent=2)  # ✅ Correct
```

So this is likely a **legacy issue** from when items were saved incorrectly, or **file corruption** from crashes.

---

## Quick Fix Instructions

```bash
cd ~/git/Eamon

# 1. Run diagnostic to see what's wrong
python3 diagnose_items.py

# 2. Auto-repair
python3 fix_items.py

# 3. Test it
python3 tavern.py
# Load Thoran → inv (should work now!)
```

---

## Expected Results After Fix

✅ `inv` command works without crash  
✅ Shows items Thoran is carrying  
✅ Can buy items in tavern  
✅ Items persist when exiting/entering  
✅ Can use items in adventure (eat, drink, etc.)  

---

## Files Provided

1. **diagnose_items.py** — Inspect all items JSON files
2. **fix_items.py** — Auto-repair corrupted files
3. **This document** — Explanation and prevention

---

## Prevention Going Forward

Add validation to `_load_carried()` in tavern.py:

```python
def _load_carried(character) -> list:
    from world import Artifact
    path = _items_path(character)
    if not os.path.exists(path):
        return []
    
    try:
        with open(path) as f:
            data = json.load(f)
        
        # ← NEW: Validate structure
        if not isinstance(data, list):
            print(f"ERROR: Items file corrupted (contains {type(data).__name__})")
            print(f"Using diagnose_items.py to identify and fix_items.py to repair")
            return []
        
        # ← NEW: Validate each item
        items = []
        for d in data:
            if isinstance(d, dict):
                items.append(Artifact.from_dict(d))
            else:
                print(f"WARNING: Skipping invalid item: {d}")
        
        return items
    
    except Exception as e:
        print(f"ERROR loading items: {e}")
        return []
```

This way, corruption is caught gracefully instead of crashing.

---

## Questions

After running the diagnostic:
- What does the items file contain?
- Is it empty, a string, or a malformed list?
- How many items does Thoran have (if any)?

This will help us understand how the corruption happened.
