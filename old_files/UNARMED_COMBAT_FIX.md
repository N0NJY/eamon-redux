# Unarmed Combat Crash - Fixed ✅

**Issue**: KeyError crash when attacking without an equipped weapon  
**Root Cause**: 'unarmed' weapon type wasn't in weapon_proficiencies dict  
**Status**: FIXED

---

## The Bug

When a player didn't equip a weapon and got attacked by a monster:

```python
weapon_type = "unarmed"  # No weapon equipped

# Later, during proficiency growth:
old_prof = self.player.weapon_proficiencies[weapon_type]  # ← KeyError!
# weapon_proficiencies only had: axe, bow, club, spear, sword
# But NOT 'unarmed'!
```

**Error Message**:
```
KeyError: 'unarmed'
File ".../engine.py", line 1143, in cmd_attack
    old_prof = self.player.weapon_proficiencies[weapon_type]
```

---

## The Fixes

### Fix 1: Add 'unarmed' to weapon_proficiencies defaults

**In player.py** (lines 54-62):
```python
weapon_proficiencies: dict[str, int] = field(
    default_factory=lambda: {
        "unarmed": 0,  # ✅ NEW
        "axe": 5,
        "bow": -10,
        "club": 20,
        "spear": 10,
        "sword": 0,
    }
)
```

**In character.py** (lines 65-73):
```python
weapon_proficiencies: dict[str, int] = field(
    default_factory=lambda: {
        "unarmed": 0,  # ✅ NEW
        "axe": 5,
        "bow": -10,
        "club": 20,
        "spear": 10,
        "sword": 0,
    }
)
```

**In character.py from_dict()** (lines 225-227):
```python
weapon_proficiencies=d.get("weapon_proficiencies", {
    "unarmed": 0, "axe": 5, "bow": -10, "club": 20, "spear": 10, "sword": 0
}),
```

### Fix 2: Use .get() safely in cmd_attack

**In engine.py** (lines 1143-1146):

**Before**:
```python
old_prof = self.player.weapon_proficiencies[weapon_type]  # ← Direct access
self.player.weapon_proficiencies[weapon_type] += 2
new_prof = self.player.weapon_proficiencies[weapon_type]
```

**After**:
```python
old_prof = self.player.weapon_proficiencies.get(weapon_type, 0)  # ✅ Safe access
self.player.weapon_proficiencies[weapon_type] = old_prof + 2
new_prof = self.player.weapon_proficiencies[weapon_type]
```

---

## Why This Works

1. **'unarmed' is now initialized** with proficiency = 0 (neutral baseline)
2. **Safe dictionary access** using .get() prevents KeyError
3. **Unarmed proficiency can grow** just like weapon proficiencies
4. **All paths covered**: player.py, character.py, character.from_dict()

---

## Testing

**Test Case**: Attack without equipped weapon
```
1. Load Thoran
2. Enter adventure (don't equip axe)
3. Walk to west chamber: w
4. Fight Rat (it attacks)
5. Player attacks with unarmed
6. ✅ Should see: "You hit Rat for X damage!"
7. ✅ Should see: "Your unarmed proficiency increased: 0% → 2%"
8. ✅ No crash!
```

---

## Files Modified

| File | Change | Lines |
|------|--------|-------|
| player.py | Add "unarmed": 0 to default dict | 54-62 |
| character.py | Add "unarmed": 0 to default dict | 65-73 |
| character.py | Add "unarmed": 0 to from_dict default | 225-227 |
| engine.py | Use .get() for safe access | 1143-1146 |

---

## Impact

✅ **Unarmed combat now works without crashing**  
✅ **Unarmed proficiency can be tracked and grown**  
✅ **Consistent with weapon proficiency system**  
✅ **Safe defensive programming** (using .get())

---

## Next Steps

1. Test unarmed combat (attack without weapon)
2. Verify proficiency grows
3. Commit to GitHub
4. Continue with save/load system

**Status**: Ready for testing and deployment! 💪
