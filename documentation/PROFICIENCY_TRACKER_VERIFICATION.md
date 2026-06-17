# Eamon Redux — Weapon Proficiency Tracking Verification

**Purpose:** Ensure weapon proficiency system works correctly:
- Proficiencies are initialized for all weapon types
- Proficiencies increase on successful hits
- Proficiencies persist between fights
- Proficiencies are properly saved/loaded
- All weapon types are tracked separately

---

## ARCHITECTURE OVERVIEW

### Weapon Types (from character.py WEAPON_TYPES)
```python
WEAPON_TYPES = {
    "sword": "Sword",
    "axe": "Axe", 
    "bow": "Bow",
    "club": "Club",
    "spear": "Spear",
}
```

Plus **unarmed** (implicit, should be tracked as "unarmed")

### Proficiency Data Structure (in Character)
```python
character.weapon_proficiencies = {
    "sword": 50,    # Fighter starts at 50%
    "axe": 50,
    "bow": 50,
    "club": 50,
    "spear": 50,
    "unarmed": 25,  # Lower for unarmed
}
```

### Player State (in Player)
```python
player.weapon_proficiencies = {
    "sword": 50,
    # ... same as character
}
```

---

## VERIFICATION CHECKLIST

### 1. CHARACTER INITIALIZATION

**Test:** Create a new Fighter character

**Expected:**
```
Weapon Proficiencies (Fighter):
  sword: 50%
  axe: 50%
  bow: 50%
  club: 50%
  spear: 50%
  unarmed: 25%
```

**Where to check:**
- File: `character.py`, method `Character.create_interactive()`
- Look for weapon proficiency initialization
- Verify all 6 types are initialized

**Code to review:**
```python
# In character.py, __init__ or create methods:
self.weapon_proficiencies = {
    "sword": 50,
    "axe": 50,
    "bow": 50,
    "club": 50,
    "spear": 50,
    "unarmed": 25,
}
```

### 2. RUNTIME TRACKING

**Test:** Start a combat, attack with sword, check proficiency mid-fight

**Location to check:** engine.py, `cmd_attack()` method

**Code path:**
1. Line 917: Extract weapon type
   ```python
   weapon_type = "unarmed" if not weapon else weapon.weapon_type
   ```
2. Line 1083–1090: Check for proficiency growth
   ```python
   if weapon_type:
       failure_chance = 100 - weapon_prof
       growth_roll = random.randint(1, 100)
       if growth_roll < failure_chance:
           # Growth happens
   ```

**Expected behavior:**
- After landing a hit with sword, check `SPELLS` menu
- Sword proficiency should have increased by +2 (5-10% chance per hit)
- Other weapon types unchanged

### 3. PROFICIENCY PERSISTENCE

**Test:** End combat, return to tavern, check proficiency again

**Data flow:**
1. Line 1273–1274 in engine.py:
   ```python
   character.weapon_proficiencies = engine.player.weapon_proficiencies.copy()
   # ... saved to character
   ```
2. Character saved to JSON file in `characters/<name>.json`

**Expected:**
- After returning to tavern, proficiency should still be increased
- Character sheet shows updated values

**File location:** `characters/<character_name>.json`

**Check JSON:**
```json
{
  "weapon_proficiencies": {
    "sword": 54,    // Increased from 50
    "axe": 50,      // Unchanged
    ...
  }
}
```

### 4. PROFICIENCY GROWTH MECHANICS

**Test:** Attack same monster 20 times with sword

**Expected growth pattern:**
- Proficiency 0%: 100% chance to grow (always grows)
- Proficiency 50%: 50% chance to grow each hit
- Proficiency 90%: 10% chance to grow (slow)
- Proficiency 100%: 0% chance to grow (capped)

**Formula verification:**
```python
failure_chance = 100 - weapon_prof
growth_roll = random.randint(1, 100)
if growth_roll < failure_chance:
    # Grow
```

Example: proficiency 50%
- failure_chance = 100 - 50 = 50
- On each hit, if random(1-100) < 50, growth occurs
- ~50% of hits cause growth

**Verification:**
1. Start with sword at 50%
2. Attack 10 times, count how many show proficiency increase message
3. Expected: roughly 5 increases (might be 3-7 due to randomness)

### 5. MULTIPLE WEAPON TRACKING

**Test:** Fight with sword, then switch to axe

**Expected:**
- Sword proficiency: increased from previous attacks
- Axe proficiency: starts fresh or continues if already used
- Both track independently

**Code:**
```python
# Line 917
weapon_type = "unarmed" if not weapon else weapon.weapon_type

# Line 1087
self.player.weapon_proficiencies[weapon_type] += 2  # Updates correct weapon
```

**Verification steps:**
1. Record sword proficiency
2. Record axe proficiency
3. Attack 5 times with sword
4. Switch to axe, attack 5 times
5. Check both proficiencies increased separately

### 6. UNARMED PROFICIENCY

**Test:** Attack with no weapon equipped

**Current issue:**
- `weapon_type = None` if not equipped
- Line 1083: `if weapon_type:` skips growth for unarmed
- **BUG: Unarmed proficiency never increases**

**Expected fix:**
```python
weapon_type = "unarmed" if not weapon else weapon.weapon_type
```

**After fix verification:**
1. Unequip all weapons
2. Attack monster 10 times with bare hands
3. Check unarmed proficiency in SPELLS menu
4. Should see increases

---

## DATA VALIDATION SCRIPT

Run this Python script to validate proficiency data in character file:

```python
#!/usr/bin/env python3
import json

def validate_character(filepath):
    """Check proficiency structure in character JSON"""
    with open(filepath) as f:
        char = json.load(f)
    
    expected_weapons = {"sword", "axe", "bow", "club", "spear", "unarmed"}
    actual_weapons = set(char.get("weapon_proficiencies", {}).keys())
    
    print(f"Character: {char.get('name')}")
    print(f"Expected weapons: {expected_weapons}")
    print(f"Actual weapons: {actual_weapons}")
    
    missing = expected_weapons - actual_weapons
    extra = actual_weapons - expected_weapons
    
    if missing:
        print(f"⚠ MISSING: {missing}")
    if extra:
        print(f"⚠ EXTRA: {extra}")
    
    # Check values are 0-100
    for weapon, prof in char.get("weapon_proficiencies", {}).items():
        if not (0 <= prof <= 100):
            print(f"⚠ {weapon}: {prof}% (should be 0-100)")
        else:
            print(f"✓ {weapon}: {prof}%")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        validate_character(sys.argv[1])
    else:
        print("Usage: python validate_proficiency.py <character.json>")
```

**Usage:**
```bash
python validate_proficiency.py characters/fighter_bob.json
```

**Expected output:**
```
Character: Fighter Bob
Expected weapons: {'sword', 'axe', 'bow', 'club', 'spear', 'unarmed'}
Actual weapons: {'sword', 'axe', 'bow', 'club', 'spear', 'unarmed'}
✓ sword: 54%
✓ axe: 50%
✓ bow: 50%
✓ club: 50%
✓ spear: 50%
✓ unarmed: 25%
```

---

## TESTING WORKFLOW

### Step 1: Pre-Combat
```
1. Create new Fighter character
2. Check SPELLS menu → Weapon Proficiencies
3. Record initial values:
   - sword: 50%
   - axe: 50%
   - ... all others
```

### Step 2: Combat
```
1. Equip sword
2. Fight rats/goblins in Beginner's Cave
3. After each successful hit, watch for:
   "Your sword proficiency increased: 50% → 52%"
4. Attack ~20 times, observe growth pattern
5. Count approximate frequency (~50% of hits at 50% proficiency)
```

### Step 3: Weapon Switching
```
1. Equip axe
2. Attack 10 times with axe
3. Check both sword and axe proficiencies increased independently
```

### Step 4: Unarmed Combat
```
1. Unequip all weapons
2. Attack monster 10 times
3. Check for unarmed proficiency growth
   (Currently broken, should be fixed first)
```

### Step 5: Persistence
```
1. Return to tavern (end adventure)
2. Open character sheet again
3. Verify proficiencies are saved
4. Close and reopen game
5. Verify proficiencies persist
```

---

## COMMON ISSUES & FIXES

### Issue 1: Proficiency Not Increasing
**Symptom:** Attack 50 times with sword, proficiency still 50%

**Possible causes:**
- All attacks are misses (check hit rate)
- Proficiency growth chance is broken (check line 1086)
- Proficiency already at 100% (check SPELLS menu)

**Fix checklist:**
- [ ] Verify hits are landing (damage messages appear)
- [ ] Check if growth message appears (even once)
- [ ] Verify proficiency not already at 100%

### Issue 2: Unarmed Proficiency Never Grows
**Symptom:** Attack with bare hands 20 times, unarmed proficiency unchanged

**Root cause:** 
- Line 917: `weapon_type = None` for unarmed
- Line 1083: `if weapon_type:` fails for None

**Fix:**
```python
# Line 917:
weapon_type = "unarmed" if not weapon else weapon.weapon_type
```

### Issue 3: Wrong Weapon Type Proficiency Increases
**Symptom:** Use sword, but axe proficiency increases instead

**Root cause:** 
- Weapon.weapon_type returns wrong value
- Dictionary key mismatch

**Fix checklist:**
- [ ] Verify weapon.weapon_type matches character.weapon_proficiencies keys
- [ ] Check artifact JSON has correct "weapon_type" field
- [ ] Verify key names are lowercase (sword, not Sword)

### Issue 4: Proficiencies Not Saved
**Symptom:** Return to tavern, proficiencies reset to baseline

**Root cause:**
- Line 1273: `character.weapon_proficiencies = engine.player.weapon_proficiencies.copy()` not executed
- character.save() not called

**Fix checklist:**
- [ ] Verify run_adventure() syncs proficiencies before returning
- [ ] Verify character.save() is called
- [ ] Check JSON file actually contains updated values

---

## SUCCESS CRITERIA

### All proficiencies working if:
- ✅ All 6 weapon types initialized (sword, axe, bow, club, spear, unarmed)
- ✅ Proficiencies visible in SPELLS menu
- ✅ Proficiencies increase on successful hits (~4-6% of hits for 50% proficiency)
- ✅ Multiple weapons tracked independently
- ✅ Proficiencies persist across fights
- ✅ Proficiencies saved to JSON and loaded correctly
- ✅ Unarmed proficiency increases (after bug fix)

### Testing complete when:
- ✅ All items above verified
- ✅ No negative proficiency values
- ✅ No proficiency exceeds 100%
- ✅ Growth message format is clear and consistent

---

**End of Verification Guide**

