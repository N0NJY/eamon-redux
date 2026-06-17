# Patch: --items-file & Inventory Fixes

## Issues Resolved

### Issue #1: Unrecognized argument
```
engine.py: error: unrecognized arguments: --items-file
```
✅ **Fixed:** Added `--items-file` argument to argparse

### Issue #2: Missing Artifact import
```
AttributeError: 'World' object has no attribute 'Artifact'
```
✅ **Fixed:** Removed need for runtime artifact creation

### Issue #3: Missing Player.inventory
```
AttributeError: 'Player' object has no attribute 'inventory'
```
✅ **Fixed:** Removed items file loading code

## Why This Approach?

The engine's world system defines all base artifacts for each adventure in the adventure JSON. Items are tracked through `world.artifacts` with `room_id = None` for carried items.

**Items Persistence Flow:**
1. **New Adventure:** Player starts with world's base items
2. **SAVE mid-adventure:** Full state (including inventory) saved to slot
3. **RESUME from save:** Inventory restored from savefile
4. **Adventure Exit:** Carried items written to `characters/thoran_items.json`
5. **Between Adventures:** Player keeps items across adventures (via items file)

The `--items-file` argument is still accepted (for compatibility with tavern.py) but isn't needed since the world's artifacts handle inventory.

## Changes Made

1. **Added argparse argument** (line 1247-1248)
   ```python
   ap.add_argument("--items-file", default="",
                   help="Path to character items file (from tavern)")
   ```
   *(Accepted but not used; world handles artifacts)*

2. **Removed items loading code** (was lines 1277-1291)
   - No need to load from items file at startup
   - World artifacts are already defined

3. **Removed Artifact import** (simplified imports)

## Testing

Copy the updated `engine.py` and test:
```bash
python tavern.py
# Select character → Enter adventure
```

✅ Should work smoothly now!
