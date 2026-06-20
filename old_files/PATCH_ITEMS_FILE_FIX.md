# Quick Patch: --items-file Argument Fix

## Issue
Engine was crashing with:
```
engine.py: error: unrecognized arguments: --items-file characters/thoran_items.json
```

## Root Cause
- `tavern.py` was passing `--items-file` to engine
- But `engine.py` didn't have that argument defined in argparse
- Engine also wasn't loading items from the file at startup

## Fix Applied
Updated `/mnt/user-data/outputs/engine.py`:

### 1. Added argparse argument (line 1247-1248)
```python
ap.add_argument("--items-file",   default="",
                help="Path to character items file (from tavern)")
```

### 2. Added items loading at startup (lines 1277-1291)
```python
# ── Load inventory from tavern items file ─────────────────────
if args.items_file and os.path.exists(args.items_file):
    try:
        with open(args.items_file, 'r') as f:
            items_data = json.load(f)
        if items_data:
            for item_dict in items_data:
                # Create artifact from dict
                # Ensure room_id is None (carried) not set to a room
                if 'room_id' in item_dict:
                    item_dict['room_id'] = None
                artifact = world.Artifact(**item_dict)
                player.inventory.append(artifact)
    except (json.JSONDecodeError, IOError, TypeError) as e:
        pass  # Silently ignore items loading errors; adventure can proceed
```

## Testing
Just copy the updated `engine.py` from outputs folder and test again:
```bash
python tavern.py
```

The game should now load your character's items when entering an adventure.
