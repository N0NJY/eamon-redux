# ENGINE.PY REWRITE - COMPLETE IMPLEMENTATION GUIDE
# Total estimated new lines: ~2200+ (adding significant spell system logic)

## CRITICAL CHANGES TO engine.py:

### 1. IMPORTS & CONSTANTS (Top of file)
```python
import random
from character import SPELL_DEFS, WEAPON_TYPES
from world import WeaponType

# Magic system constants
SPELL_NAMES = {
    "blast": "Blast", "heal": "Heal", "speed": "Speed", "power": "Power"
}
```

### 2. NEW SPELL CASTING SYSTEM - Add these methods to Engine class:

#### cmd_cast(self, args) - Main spell casting command
```
Parse: CAST <spell> [target]
Cases:
  - Check if spell is learned (proficiency not None)
  - Check if spell is locked (critical failure)
  - Call _attempt_cast(spell_key, target)
  - Return results to player
```

#### _attempt_cast(self, spell_key: str, target_name: str = None) -> bool:
```
CORE SPELL LOGIC:

1. Check spell proficiency locked:
   if self.player.is_spell_locked(spell_key):
       print("This spell overloaded your mind and is unusable!")
       return False

2. Get effective proficiency (with fatigue):
   effective_prof = self.player.get_effective_spell_proficiency(spell_key)

3. Roll for success (1D100):
   success_roll = random.randint(1, 100)
   
4. Check for CRITICAL FAILURE (1% chance):
   if random.randint(1, 100) == 1:
       print("MENTAL OVERLOAD! This spell is now unusable for the rest of the adventure!")
       self.player.lock_spell(spell_key)
       self.player.apply_spell_fatigue(spell_key)
       return False

5. Check for success:
   if success_roll <= effective_prof:
       # SPELL SUCCEEDED
       
       # Check for CRITICAL SUCCESS (1% = 01 roll):
       if success_roll == 1:
           print("CRITICAL SUCCESS!")
           # For offensive spells: double damage
       
       # Attempt skill growth (only on success):
       failure_chance = 100 - self.player.spell_proficiencies[spell_key]
       growth_roll = random.randint(1, 100)
       if growth_roll < failure_chance:
           old_prof = self.player.spell_proficiencies[spell_key]
           self.player.spell_proficiencies[spell_key] += 2
           new_prof = self.player.spell_proficiencies[spell_key]
           print(f"Your {SPELL_NAMES[spell_key]} proficiency increased: {old_prof}% -> {new_prof}%")
       
       # Execute spell effect
       spell_method = f"_cast_{spell_key}"
       if hasattr(self, spell_method):
           getattr(self, spell_method)(target_name)
       
       # Apply fatigue AFTER successful cast
       self.player.apply_spell_fatigue(spell_key)
       return True
   else:
       # SPELL FAILED
       print(f"Your {SPELL_NAMES[spell_key]} fails to manifest!")
       # Fatigue still applies even on failure
       self.player.apply_spell_fatigue(spell_key)
       return False
```

#### _cast_blast(self, target_name: str):
```
- Find monster by name (target_name)
- Roll 1D6 for damage (bypasses armor)
- Apply critical hit logic (5% chance with sub-outcomes)
- Deal damage directly to monster HP
- Monster attacks back if alive
```

#### _cast_heal(self, target_name: str):
```
- Roll 1D10 for healing amount
- Add INT bonus: (intelligence - 10) // 2
- Restore player HP (can't exceed max)
- Print healing message
- No combat consequences
```

#### _cast_speed(self, target_name: str = None):
```
- Roll random duration: 10 + random(1, 11) = 11-20 rounds
- Check if speed already active:
  - If yes: reset duration to new random value (no stacking)
  - If no: activate speed
- Print message showing duration
- Player agility now doubled for combat rounds
- Speed deactivates after duration expires
```

#### _cast_power(self, target_name: str = None):
```
- For Beginner's Cave: sonic boom with silly random effects
  Messages like:
    "A sonic boom erupts from nowhere!"
    "The air crackles with chaotic energy!"
    "You hear mysterious laughter echo through the chamber!"
  - No actual game effect
- For other adventures: call adventure-specific handler
```

### 3. WEAPON PROFICIENCY SYSTEM - Add these methods:

#### cmd_attack - MODIFY existing attack logic:
```
AFTER determining hit/miss:

1. Determine weapon type from equipped weapon
   weapon = self.player.equipped_weapon(self.world)
   if weapon and hasattr(weapon, 'weapon_type'):
       weapon_type = weapon.weapon_type
   else:
       weapon_type = None  # unarmed

2. Get weapon proficiency (with 0 if not tracked):
   base_weapon_prof = self.player.weapon_proficiencies.get(weapon_type, 0)

3. Modify hit chance:
   final_hit_chance += base_weapon_prof

4. ON SUCCESSFUL HIT:
   - Check for WEAPON CRITICAL HIT (5% chance):
     if random.randint(1, 100) <= 5:
         crit_roll = random.randint(1, 100)
         if crit_roll <= 50: ignore_armor = True, use full damage
         elif crit_roll <= 85: damage *= 1.5
         elif crit_roll <= 95: damage *= 2.0
         elif crit_roll <= 99: damage *= 3.0
         else: instant_kill = True

5. ON ANY ATTACK (hit or miss):
   - Check for FUMBLE (4% chance):
     if random.randint(1, 100) <= 4:
         fumble_roll = random.randint(1, 100)
         if fumble_roll <= 35: recover (no effect)
         elif fumble_roll <= 75: drop weapon
         elif fumble_roll <= 95: break weapon (50% chance damages player)
         elif fumble_roll <= 99: hit self
         else: kill self

6. ON SUCCESSFUL HIT - Weapon proficiency growth:
   # Similar to spell growth
   failure_chance = 100 - base_weapon_prof
   growth_roll = random.randint(1, 100)
   if growth_roll < failure_chance:
       old_prof = self.player.weapon_proficiencies[weapon_type]
       self.player.weapon_proficiencies[weapon_type] += 2
       new_prof = self.player.weapon_proficiencies[weapon_type]
       print(f"Your {weapon_type} proficiency increased: {old_prof}% -> {new_prof}%")
```

### 4. FATIGUE RECOVERY - Call in movement and actions:

#### In cmd_north/south/east/west (and other non-magical actions):
```
# After successful move
recovery = random.randint(5, 10)  # 5-10% recovery
self.player.recover_all_spell_fatigue(recovery)
print(f"You feel slightly more focused. (fatigue recovery: {recovery}%)")
```

#### In cmd_rest:
```
# Modify existing REST command
# Add larger recovery
recovery = random.randint(10, 20)  # More recovery on REST
self.player.recover_all_spell_fatigue(recovery)
```

### 5. SPEED SPELL MANAGEMENT - In combat round:

#### In monster_round (after monster attacks):
```
# Decrement speed duration
if self.player.speed_active:
    self.player.tick_speed_duration()
    if not self.player.speed_active:
        print("Your speed enhancement fades.")
```

### 6. SPELL COMMAND - Show spell proficiencies:

#### Add cmd_spells(self, args):
```
Show all spells with:
- Spell name
- Current proficiency (or "not learned")
- Cost to learn (if not learned)
- Brief description
Example:
  Blast    : 45% (1D6 damage, bypasses armor)
  Heal     : Not learned (1000 gold)
  Speed    : 38% (Double agility for 11-20 rounds)
  Power    : Not learned (100 gold)
```

### 7. TAVERN INTEGRATION - Update tavern.py Aldric NPC:

#### In tavern.py shop_aldric():
```
Add spell learning interface:
- Show list of learned and unlearned spells with costs
- Option: B <number> to learn spell
- Option: DONE to leave
- Check gold and proficiency
- Call player.learn_spell(spell_key)
```

### 8. INITIALIZATION - Update Engine.__init__:

```
Add to __init__ when creating Player from Character:
  player.spell_proficiencies = character.spell_proficiencies.copy()
  player.weapon_proficiencies = character.weapon_proficiencies.copy()
  # Initialize fatigue multipliers to 1.0
  for spell in player.spell_proficiencies:
      if player.spell_proficiencies[spell] is not None:
          player.spell_fatigue_multiplier[spell] = 1.0
```

### 9. SERIALIZE TO CHARACTER - Update on adventure exit:

```
When saving progress:
  character.spell_proficiencies = player.spell_proficiencies.copy()
  character.weapon_proficiencies = player.weapon_proficiencies.copy()
  character.gold = player.gold  # Update gold spent on spells
```

### 10. HEALTH COMMAND UPDATE:

#### Modify cmd_health:
```
Show:
  HP: X/Y
  Equipped weapon (with weapon type)
  Equipped armor (with AC)
  Gold
  [IF SPEED ACTIVE] Speed active: X rounds remaining (Agility doubled)
  [NO MORE MANA - removed]
```

---

## SUMMARY OF ALL METHOD ADDITIONS:

**NEW METHODS:**
- `cmd_cast(args)` - Main spell casting
- `_attempt_cast(spell_key, target_name)` - Core spell logic
- `_cast_blast(target_name)` - Blast spell
- `_cast_heal(target_name)` - Heal spell
- `_cast_speed(target_name)` - Speed spell
- `_cast_power(target_name)` - Power spell (sonic boom)
- `cmd_spells(args)` - Show spell proficiencies

**MODIFIED METHODS:**
- `cmd_attack(args)` - Add weapon proficiency & critical hit/fumble logic
- `cmd_north/south/east/west(args)` - Add fatigue recovery on move
- `cmd_rest(args)` - Add larger fatigue recovery
- `monster_round()` - Decrement speed duration
- `__init__()` - Initialize spell/weapon proficiencies
- `cmd_health(args)` - Remove mana, add speed status
- Any method calling character loading - sync proficiencies
- Return to tavern - save proficiencies back to character

**REMOVED:**
- `cmd_cast()` if exists (for mana system)
- `_cast_fireball()` (replaced with blast)
- `_cast_shield()` (removed in favor of speed)
- `_cast_light()` (removed)
- Any mana-related logic

---

## TESTING CHECKLIST:

- [ ] Create character learns spells at Aldric
- [ ] Cast spell with proficiency check
- [ ] Proficiency increases on success
- [ ] Fatigue halving works (50%, 25%, etc.)
- [ ] Fatigue recovery on non-magical actions
- [ ] Critical failure (1%) locks spell
- [ ] Critical success (01 roll) shows message
- [ ] Speed spell doubles agility for correct duration
- [ ] Speed recast resets duration (no stack)
- [ ] Speed deactivates after rounds expire
- [ ] Weapon proficiency increases on hit
- [ ] Critical hit (5%) applies correct sub-effect
- [ ] Fumble (4%) applies correct sub-effect
- [ ] Proficiency announced on increase
- [ ] Sonic boom on Power spell cast
- [ ] Fatigue recovers on REST more than move

---

## FILE CHANGES SUMMARY:

| File | Changes | Lines Added |
|------|---------|------------|
| character.py | Remove classes/mana, add proficiencies | ~250 |
| player.py | Mirror changes, add fatigue | ~200 |
| engine.py | Entire spell system + mods | ~700 |
| tavern.py | Aldric spell shop | ~100 |
| world.py | Add weapon types | ~30 |
| command_parser.py | Add spell commands | ~20 |

**Total new code: ~1,300 lines**

---
