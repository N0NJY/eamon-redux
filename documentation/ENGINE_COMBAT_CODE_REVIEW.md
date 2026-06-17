# Eamon Redux — engine.py Combat Code Review
**Date:** June 17, 2026  
**Status:** Pre-testing code analysis for bugs/issues

---

## COMBAT FUNCTION MAP

| Function | Lines | Purpose |
|----------|-------|---------|
| `cmd_attack()` | 900–1095 | Player initiates attack on monster |
| `monster_round()` | 1097–1120 | Monster counter-attacks player |
| Helper: `roll()` | 87–88 | Roll dice (e.g., 1d6) |

---

## CRITICAL CODE REVIEW

### 1. cmd_attack() — Player Attack Resolution

**Location:** Lines 900–1095

**Flow:**
1. Parse target monster name
2. Check if player has weapon equipped
3. Calculate hit chance (base 50 + agility bonus + weapon proficiency - monster AC)
4. Roll for fumble (4% chance)
5. If fumble: roll for type (recover/drop/break/self-hit/self-kill)
6. If not fumble & miss: end
7. If hit: roll for critical (5% chance)
8. If critical: roll for type (ignore armor / 1.5× / 2× / 3× / instant kill)
9. Apply armor reduction
10. Deal damage, check if monster dead
11. Grow weapon proficiency (if hit)
12. Monster attacks back

---

### 2. ISSUE ANALYSIS: Hit Chance Calculation

**Code (Line 951):**
```python
hit_chance = 50 + agility_bonus + weapon_prof - monster_ac
hit_roll = random.randint(1, 100)

is_hit = hit_roll <= hit_chance
```

**Analysis:** ✅ CORRECT
- Base 50% hit chance is reasonable
- Agility bonus can be negative (low AGI) or positive (high AGI)
- Weapon proficiency (0-100%) adds to hit chance
- Monster AC reduces hit chance
- `hit_roll <= hit_chance` means rolling <= hit_chance succeeds (correct logic)

**Edge Case:** 
- If hit_chance becomes negative (e.g., 50 - 20 - 40 = -10), any roll > -10 hits (effectively always misses)
- If hit_chance > 100 (e.g., 50 + 30 + 50 = 130), always hits
- **No clamping to 0-100%** — is this intentional? POSSIBLE ISSUE

**Recommendation:** 
```python
# Consider clamping:
hit_chance = max(5, min(95, 50 + agility_bonus + weapon_prof - monster_ac))
```
This prevents absurd 0% or 100% hit rates.

---

### 3. ISSUE ANALYSIS: Fumble Logic (Lines 958–1000)

**Code:**
```python
if random.randint(1, 100) <= 4:  # 4% chance
    fumble_roll = random.randint(1, 100)
    
    if fumble_roll <= 35:
        # Recover (no effect)
    elif fumble_roll <= 75:
        # Drop weapon
    elif fumble_roll <= 95:
        # Break weapon
    elif fumble_roll <= 99:
        # Hit self
    else:
        # Kill self
```

**Analysis:** ✅ CORRECT
- Frequency: 4% (1 in 25 attacks) ✓
- Tiers:
  - Recover: 35% of fumbles (≤35) ✓
  - Drop: 40% of fumbles (35-75) ✓
  - Break: 20% of fumbles (75-95) ✓
  - Hit self: 4% of fumbles (95-99) ✓
  - Kill self: 1% of fumbles (>99) ✓

**Edge Case:** Unarmed fumble "drop weapon" — does it work with no weapon?
```python
if weapon:
    self.player.unequip_artifact(weapon, self.world)
```
**Good:** Checks if weapon exists before unequipping.

**Issue:** When breaking weapon and possibly injuring player:
```python
if random.randint(1, 100) <= 50:
    damage = random.randint(1, 4)
    self.player.hp -= damage
```
Damage is direct subtraction. **What if HP goes to 0?** Does death trigger?
- Checked in main game loop (lines 289-290), so ✓

---

### 4. ISSUE ANALYSIS: Critical Hit Logic (Lines 1024–1049)

**Code:**
```python
if random.randint(1, 100) <= 5:  # 5% chance
    crit_roll = random.randint(1, 100)
    
    if crit_roll <= 50:
        # Ignore armor
    elif crit_roll <= 85:
        # 1.5× damage
    elif crit_roll <= 95:
        # 2× damage
    elif crit_roll <= 99:
        # 3× damage
    else:
        # Instant kill
```

**Analysis:** ✅ CORRECT
- Frequency: 5% (1 in 20 hits) ✓
- Tiers:
  - Ignore armor: 50% of crits ✓
  - 1.5×: 35% of crits (50-85) ✓
  - 2×: 10% of crits (85-95) ✓
  - 3×: 4% of crits (95-99) ✓
  - Instant kill: 1% of crits (>99) ✓

**Potential Issue:** Instant kill (Line 1046):
```python
print(self.tc(f"INSTANT KILL!", "win"))
monster.hp = 0
monster.is_alive = False
return
```
Sets `is_alive = False` but does NOT execute normal death logic (XP, loot, proficiency growth).

**Check:** Where does monster death resolve?
- Lines 1063–1079: After normal damage, if `monster.hp <= 0`
- Instant kill skips this (early return at 1049)

**POTENTIAL BUG:** Instant kill doesn't award XP or drop loot!
- **Recommendation:** Before returning, call XP/loot logic or refactor

---

### 5. ISSUE ANALYSIS: Armor Reduction (Lines 1051–1054)

**Code:**
```python
if not ignore_armor:
    damage = max(1, damage - monster_ac)
```

**Analysis:** ✅ CORRECT
- Only reduces damage if not ignoring armor (crit tier 1)
- Ensures minimum 1 damage (never 0)
- Monster AC value is subtracted from damage

**Edge Case:** Monster with AC +0?
- Damage not reduced ✓

**Edge Case:** Monster with AC +10, player damage 3?
- 3 - 10 = -7 → max(1, -7) = 1 damage ✓

---

### 6. ISSUE ANALYSIS: Weapon Proficiency Growth (Lines 1083–1090)

**Code:**
```python
if weapon_type:
    failure_chance = 100 - weapon_prof
    growth_roll = random.randint(1, 100)
    if growth_roll < failure_chance:
        old_prof = self.player.weapon_proficiencies[weapon_type]
        self.player.weapon_proficiencies[weapon_type] += 2
        new_prof = self.player.weapon_proficiencies[weapon_type]
        print(self.tc(f"Your {weapon_type} proficiency increased: {old_prof}% → {new_prof}%", "success"))
```

**Analysis:** ✅ CORRECT
- Only grows on successful hit (only runs if `monster.hp > 0`)
- Checks if `weapon_type` exists
- Growth chance: `100 - proficiency`
  - At 0% proficiency: 100% chance to grow
  - At 50% proficiency: 50% chance to grow
  - At 100% proficiency: 0% chance to grow (capped)
- Growth amount: +2 per successful hit

**Edge Case:** Unarmed combat
```python
# At line 917:
weapon_type = None
if weapon:
    weapon_type = weapon.weapon_type  # e.g., "sword", "axe"
```
If `weapon_type = None`, proficiency growth line 1083 doesn't execute.
- **ISSUE:** Unarmed proficiency never grows!
- **Check code around line 917 for unarmed setup**

---

### 7. ISSUE ANALYSIS: Monster Round Attacks (Lines 1097–1120)

**Code:**
```python
def monster_round(self, monster) -> None:
    if not monster.is_alive:
        return
    
    # Hit chance = 50 - agility_bonus - player_armor_class
    hit_chance = 50 - self.player.agility_bonus - self.player.armor_class(self.world)
    hit_roll = random.randint(1, 100)
    
    if hit_roll > hit_chance:
        print(self.tc(f"{monster.name} misses you.", "sys"))
    else:
        damage = roll(monster.damage_dice, monster.damage_sides)
        ac_reduction = self.player.armor_class(self.world)
        damage = max(1, damage - ac_reduction)
        self.player.hp -= damage
        print(self.tc(f"{monster.name} hits you for {damage} damage!", "dmg"))
    
    # Decrement speed spell duration
    if self.player.speed_active:
        self.player.tick_speed_duration()
        if not self.player.speed_active:
            print(self.tc("Your speed enhancement fades.", "sys"))
```

**Analysis:** 
- ✅ Checks if monster alive
- ✅ Hit chance calculation: 50 - player_agility_bonus - player_AC (correct inverse of player attack)
- ✅ Damage calculation with AC reduction
- ✅ Speed spell tick-down on each monster attack

**Potential Issue (Line 1104):**
```python
if hit_roll > hit_chance:  # MISS
```
vs. player attack (Line 954):
```python
is_hit = hit_roll <= hit_chance  # HIT
```

**Check:** Are these logically consistent?
- Player: roll ≤ chance = hit ✓
- Monster: roll > chance = miss ✓ (inverse of hit)
- Both are equivalent ✓

---

## SUMMARY: CODE ISSUES IDENTIFIED

### HIGH PRIORITY
| Issue | Location | Severity | Fix |
|-------|----------|----------|-----|
| **Instant kill skips XP/loot** | Line 1046-1049 | HIGH | Award XP and drop loot before returning |
| **Unarmed proficiency never grows** | Line 917 + 1083 | HIGH | Create "unarmed" weapon type tracking |
| **Hit chance unclamped** | Line 951 | MEDIUM | Consider clamping to 5-95% |

### MEDIUM PRIORITY
| Issue | Location | Severity | Notes |
|-------|----------|----------|-------|
| Fumble self-damage unchecked | Line 984-985 | LOW | Works fine, death checked elsewhere |
| Monster can attack with 0 HP | Line 1099 | LOW | Early return prevents this |

---

## RECOMMENDED FIXES (Before Full Combat Testing)

### Fix 1: Instant Kill Must Award Rewards
**Location:** engine.py, lines 1046–1049

**Current:**
```python
else:
    # Instant kill
    print(self.tc(f"INSTANT KILL!", "win"))
    monster.hp = 0
    monster.is_alive = False
    return
```

**Proposed:**
```python
else:
    # Instant kill
    print(self.tc(f"INSTANT KILL!", "win"))
    monster.hp = 0
    monster.is_alive = False
    
    # Award XP
    xp_value = monster.xp_value or (monster.hp_max * 10)
    self.player.xp += xp_value
    print(self.tc(f"You gain {xp_value} XP!", "heal"))
    
    # Drop loot
    if monster.loot_id:
        loot = self.world.artifacts.get(monster.loot_id)
        if loot:
            loot.room_id = self.player.room_id
            print(self.tc(f"{monster.name} drops {loot.name}!", "item"))
    
    return
```

---

### Fix 2: Unarmed Proficiency Tracking
**Location:** engine.py, lines 917 + 1083

**Issue:** `weapon_type = None` for unarmed, so proficiency never grows

**Current:**
```python
# Line 917
weapon_type = None
if weapon:
    weapon_type = weapon.weapon_type
```

**Proposed:**
```python
# Line 917
weapon_type = "unarmed" if not weapon else weapon.weapon_type
```

**Then at line 1083**, proficiency growth will include unarmed.

---

### Fix 3: Hit Chance Bounds (Optional)
**Location:** engine.py, line 951

**Current:**
```python
hit_chance = 50 + agility_bonus + weapon_prof - monster_ac
```

**Proposed:**
```python
hit_chance = max(5, min(95, 50 + agility_bonus + weapon_prof - monster_ac))
```

This ensures no 0% or 100% hit rates (except intentionally).

---

## TESTING IMPACT

### Before fixes:
- ❌ Instant kill doesn't reward XP/loot
- ❌ Unarmed proficiency doesn't grow
- ⚠️ Hit chance can exceed 100% or go negative (varies by roll)

### After fixes:
- ✅ Full combat rewards system works
- ✅ All weapon types tracked consistently
- ✅ Hit chance more balanced

---

## CODE QUALITY NOTES

**Strengths:**
- Clear separation of player attack and monster counter-attack
- Proper use of `max()` to prevent negative damage
- Fumble and crit tiers well-distributed
- Speed spell mechanic integrated cleanly

**Areas for improvement:**
- Death condition (instant kill) duplicates XP/loot logic
- Unarmed as `None` rather than explicit type
- No clamping on hit_chance (extreme cases possible)

---

**End of Code Review**

