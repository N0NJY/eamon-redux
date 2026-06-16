# EAMON REDUX - COMPLETE IMPLEMENTATION CHECKLIST
## Magic System Rewrite (June 15, 2026)

---

## QUICK START (5 min)

- [ ] Read `REWRITE_SUMMARY.md` for overview
- [ ] Understand the 4 phases of implementation
- [ ] Decide: full rewrite now, or phase by phase?

---

## PHASE 1: FILE REPLACEMENT (30 minutes) ✅ READY

### 1.1 Backup Original Files
```bash
cd ~/git/Eamon
cp character.py character_BACKUP_$(date +%s).py
cp player.py player_BACKUP_$(date +%s).py
cp world.py world_BACKUP_$(date +%s).py
```
- [ ] character.py backed up
- [ ] player.py backed up
- [ ] world.py backed up

### 1.2 Copy New Files
```bash
# From outputs folder to your Eamon directory:
cp character_NEW.py character.py
cp player_NEW.py player.py
cp world_NEW.py world.py
```
- [ ] character_NEW.py → character.py
- [ ] player_NEW.py → player.py
- [ ] world_NEW.py → world.py

### 1.3 Test Phase 1
```bash
python3 tavern.py
```
- [ ] Tavern loads (no import errors)
- [ ] Create character
- [ ] Verify starting gold = 200
- [ ] Check CHARACTER command shows all proficiencies
- [ ] Load character
- [ ] Verify proficiencies persist
- [ ] Delete character works

---

## PHASE 2: ENGINE.PY REWRITE (3-4 hours) 🚧 IN PROGRESS

### READ FIRST:
- [ ] `ENGINE_IMPLEMENTATION_GUIDE.md` (understand the system)

### 2.1 Imports & Constants (15 min)
In engine.py top section, add:
```python
from character import SPELL_DEFS, WEAPON_TYPES
from world import WeaponType
```

- [ ] SPELL_DEFS imported
- [ ] WEAPON_TYPES imported
- [ ] WeaponType class imported

### 2.2 Spell Casting (60 min)
Add to Engine class:

- [ ] `cmd_cast(self, args)` - Main cast command dispatcher
- [ ] `_attempt_cast(self, spell_key, target_name)` - Core logic
  - [ ] Check if spell learned
  - [ ] Check if spell locked
  - [ ] Calculate effective proficiency with fatigue
  - [ ] Roll 1D100 for success/failure
  - [ ] Check 1% critical failure (lock spell)
  - [ ] Check 1% critical success (double damage for offensive)
  - [ ] Attempt skill growth on success (+2%)
  - [ ] Apply fatigue multiplier
  - [ ] Execute spell-specific method
  
- [ ] `_cast_blast(self, target_name)` - 1D6 damage
  - [ ] Roll 1D6
  - [ ] Bypass armor (apply full damage)
  - [ ] Check 5% critical hit table
  - [ ] Deal damage to monster
  - [ ] Monster attacks back
  
- [ ] `_cast_heal(self, target_name)` - 1D10 healing
  - [ ] Roll 1D10
  - [ ] Add INT bonus: (intelligence - 10) // 2
  - [ ] Restore HP (cap at hp_max)
  - [ ] Print message
  
- [ ] `_cast_speed(self, target_name)` - Agility buff
  - [ ] Roll duration: 10 + random(1, 11) = 11-20
  - [ ] Check if already active
  - [ ] If active: reset duration (no stack)
  - [ ] If not: activate, set duration
  - [ ] Print message with rounds
  
- [ ] `_cast_power(self, target_name)` - Special spell
  - [ ] For Beginner's Cave: sonic boom message
  - [ ] No actual game effect

### 2.3 Weapon Proficiency (60 min)
Modify existing combat code:

- [ ] `cmd_attack(args)` modifications:
  - [ ] Determine weapon type from equipped weapon
  - [ ] Get weapon proficiency for that type
  - [ ] Modify hit chance by proficiency
  - [ ] ON HIT: Check 5% critical hit table
    - [ ] 50%: ignore armor
    - [ ] 35%: 1.5× damage
    - [ ] 10%: 2× damage
    - [ ] 4%: 3× damage
    - [ ] 1%: instant kill
  - [ ] ON ANY ATTACK: Check 4% fumble table
    - [ ] 35%: recover (no effect)
    - [ ] 40%: drop weapon
    - [ ] 20%: break weapon (50% damages player)
    - [ ] 4%: hit self
    - [ ] 1%: kill self
  - [ ] ON HIT: Weapon proficiency growth (+2%)

### 2.4 Fatigue Recovery (30 min)
Add to non-magical actions:

- [ ] `cmd_north()`: Add 5-10% fatigue recovery
- [ ] `cmd_south()`: Add 5-10% fatigue recovery
- [ ] `cmd_east()`: Add 5-10% fatigue recovery
- [ ] `cmd_west()`: Add 5-10% fatigue recovery
- [ ] `cmd_up()`: Add 5-10% fatigue recovery
- [ ] `cmd_down()`: Add 5-10% fatigue recovery
- [ ] `cmd_rest()`: Add 10-20% fatigue recovery (more than movement)

### 2.5 Speed Spell Management (20 min)
In combat round:

- [ ] `monster_round()`: After monster attacks, decrement speed duration
  - [ ] Call `self.player.tick_speed_duration()`
  - [ ] If speed expired, print message

### 2.6 Spell Display Command (15 min)

- [ ] `cmd_spells(self, args)`:
  - [ ] Show all 4 spells
  - [ ] Show proficiency (or "not learned")
  - [ ] Show cost to learn
  - [ ] Show brief description

### 2.7 Character Initialization (15 min)

- [ ] In `Engine.__init__()` when creating Player from Character:
  - [ ] Copy `spell_proficiencies` from character to player
  - [ ] Copy `weapon_proficiencies` from character to player
  - [ ] Initialize `spell_fatigue_multiplier` to 1.0 for all spells
  - [ ] Initialize `spell_locked` to False for all spells

### 2.8 Character Saving (15 min)

When returning to tavern or saving:

- [ ] Sync player proficiencies back to character before saving
  - [ ] `character.spell_proficiencies = player.spell_proficiencies.copy()`
  - [ ] `character.weapon_proficiencies = player.weapon_proficiencies.copy()`
  - [ ] `character.gold = player.gold` (for learned spells)

### 2.9 Remove Old Magic Code (20 min)

- [ ] Find and delete old spell methods:
  - [ ] Remove `_cast_fireball()`
  - [ ] Remove `_cast_shield()`
  - [ ] Remove `_cast_light()`
  - [ ] Remove `_cast_heal_old()` if exists
- [ ] Remove mana-related code:
  - [ ] Remove `self.player.mana` references
  - [ ] Remove `self.player.mana_max` references
  - [ ] Remove mana bar display
  - [ ] Remove mana recovery on REST

### 2.10 Test Engine Implementation

```bash
python3 tavern.py
# Go to adventure
# Try each spell individually
```

- [ ] CAST BLAST works
- [ ] CAST HEAL works
- [ ] CAST SPEED works
- [ ] CAST POWER works
- [ ] Proficiency increases on success
- [ ] Fatigue halves on each cast
- [ ] Fatigue recovers on move (5-10%)
- [ ] Fatigue recovers on REST (10-20%)
- [ ] 1% critical failure locks spell
- [ ] Speed doubles agility for duration
- [ ] Weapon critical hits work (5%)
- [ ] Weapon fumbles work (4%)
- [ ] Weapon proficiency increases on hit
- [ ] Return to tavern: proficiencies saved

---

## PHASE 3: TAVERN UPDATES (1-2 hours) 🚧 IN PROGRESS

### READ FIRST:
- [ ] `tavern_IMPLEMENTATION_GUIDE.md` (understand changes)

### 3.1 Remove Class Selection

In `character.py` `Character.create_interactive()`:

- [ ] Delete class selection UI (~30 lines)
  - [ ] Remove Fighter/Sorcerer prompt
  - [ ] Remove "Choose class (1/2)" logic
- [ ] Delete spell selection UI (~25 lines)
  - [ ] Remove spell selection prompt
  - [ ] Remove spell choice logic
- [ ] Update final message to mention spell learning

### 3.2 Implement Aldric Spell Shop

In `tavern.py`:

- [ ] Find `shop_aldric()` function or create it
- [ ] Add spell list display
  - [ ] Show all 4 spells with name, cost, status
- [ ] Add buy/learn interface
  - [ ] Parse `B <number>` command
  - [ ] Call `character.learn_spell(spell_key)`
  - [ ] Update player proficiencies
  - [ ] Print success/error message
- [ ] Keep sell functionality
  - [ ] Allow selling potions/readables (unchanged)

### 3.3 Update Character Display

- [ ] Ensure character sheet shows:
  - [ ] All 5 weapon proficiencies
  - [ ] All 4 spell proficiencies
  - [ ] NO class field
  - [ ] NO mana field

### 3.4 Update Command Parser

From `command_parser_UPDATES.py`:

- [ ] Replace ENGINE_COMMANDS dict with updated version
  - [ ] Add "blast", "heal", "speed", "power" commands
  - [ ] Keep "cast" command
  - [ ] Keep "spells" command

### 3.5 Test Tavern Updates

```bash
python3 tavern.py
```

- [ ] Create character: no class selection
- [ ] Character starts with 200 gold
- [ ] WIZARD command opens Aldric
- [ ] Spell shop shows all 4 spells
- [ ] B 1 learns Blast
- [ ] Gold decreases
- [ ] Proficiency shows (25-75%)
- [ ] B 1 again shows "already learned"
- [ ] Learn second spell
- [ ] Character sheet shows both proficiencies

---

## PHASE 4: FULL TESTING (1-2 hours) ✅ CRITICAL

### 4.1 Unit Tests (Each System Isolated)

#### Spell Learning
```bash
python3 tavern.py
# Create character: gold = 200
# Learn Blast: gold = 197, prof = XX%
# Learn Heal: gold = 196, prof = XX%
# Learn Speed: gold = 191, prof = XX%
# Learn Power: gold = 191, prof = XX%
```

- [ ] Aldric spell shop works
- [ ] Gold decreases correctly
- [ ] Proficiency initializes 25-75%
- [ ] Can't learn without gold
- [ ] Can't learn twice

#### Spell Casting
```bash
# In adventure with learned spells
CAST BLAST rat
```

- [ ] Blast cast succeeds on roll ≤ proficiency
- [ ] Blast cast fails on roll > proficiency
- [ ] Fatigue halves: 100% → 50% → 25% → 12.5%
- [ ] Fatigue hard minimum 5%
- [ ] Fatigue recovery on NORTH: +5-10%
- [ ] Fatigue recovery on REST: +10-20%

#### Critical Failure
```bash
# Keep casting until 1% triggers (may take a while)
CAST BLAST rat  # multiple times
```

- [ ] 1% critical failure locks spell
- [ ] Locked spell shows error message
- [ ] Locked spell persists for entire adventure
- [ ] Spell still locked after REST

#### Spell Skill Growth
```bash
# Cast successfully multiple times
CAST HEAL
CAST HEAL
CAST HEAL
```

- [ ] On success: "proficiency increased XX% → YY%"
- [ ] Growth only on successful cast
- [ ] Growth is +2%
- [ ] Announcement in-line

#### Speed Spell
```bash
CAST SPEED
# Check agility doubled in combat
ATTACK rat  # should hit more often
```

- [ ] Speed activates
- [ ] Agility doubled (property returns base × 2)
- [ ] Duration 11-20 rounds
- [ ] Speed expires after duration
- [ ] Recast SPEED resets duration (no stacking)
- [ ] Agility back to normal when expired

#### Heal Spell
```bash
# Take damage first
ATTACK rat  # let rat hit you
CAST HEAL
```

- [ ] Heal restores 1D10 HP
- [ ] Can't exceed hp_max
- [ ] No combat consequence (monster doesn't attack)

#### Blast Spell
```bash
CAST BLAST rat
```

- [ ] Deals 1D6 damage
- [ ] Bypasses armor entirely
- [ ] Monster attacks back if alive
- [ ] Monster dies if HP → 0

#### Power Spell (Beginner's Cave)
```bash
CAST POWER
```

- [ ] Sonic boom message shows
- [ ] No actual game effect
- [ ] (For other adventures: check adventure-specific handler)

#### Weapon Proficiency
```bash
# Equip different weapons
EQUIP sword
ATTACK rat  # multiple times
```

- [ ] Weapon proficiency increases on hit: +2%
- [ ] Each weapon type independent
- [ ] Critical hits trigger correctly (5%)
- [ ] Fumbles trigger correctly (4%)
- [ ] Critical hit effects work
- [ ] Fumble effects work

#### Weapon Critical Hit
```bash
# Repeatedly attack until 5% critical triggers
ATTACK rat  # keep attacking
```

- [ ] 5% chance triggers
- [ ] Sub-effect randomizes:
  - [ ] 50%: ignore armor
  - [ ] 35%: 1.5× damage
  - [ ] 10%: 2× damage
  - [ ] 4%: 3× damage
  - [ ] 1%: instant kill
- [ ] Message shows "Critical Hit!"

#### Weapon Fumble
```bash
# Repeatedly attack until 4% fumble triggers
ATTACK rat  # keep attacking
```

- [ ] 4% chance triggers
- [ ] Sub-effect randomizes:
  - [ ] 35%: recover (nothing happens)
  - [ ] 40%: drop weapon (must retrieve)
  - [ ] 20%: break weapon (50% sub-chance damages player)
  - [ ] 4%: hit self (self damage)
  - [ ] 1%: kill self (instant death)
- [ ] Message shows effect

### 4.2 Integration Tests (Full Adventure Flow)

```bash
python3 tavern.py
# Create character
# Go to Beginner's Cave
# Cast spells, fight monsters
# Return to tavern
# Create second character
# Play second adventure
# Return to tavern
```

- [ ] Proficiencies sync to character on exit
- [ ] Proficiencies load on enter
- [ ] Multiple characters have independent proficiencies
- [ ] Proficiencies persist between adventures
- [ ] Same character can play multiple adventures
- [ ] Gold from spell learning persists

### 4.3 Regression Tests (Old Features)

```bash
# Verify old features still work
```

- [ ] Movement works (N/S/E/W/U/D)
- [ ] Equipment works (equip/unequip)
- [ ] Inventory works (get/drop/examine)
- [ ] Monsters attack back
- [ ] Monster death works
- [ ] Food/potion consumption works
- [ ] Keys and locked doors work
- [ ] Save/load game state works
- [ ] Adventure win conditions work

### 4.4 Edge Cases

```bash
# Test edge cases
```

- [ ] Cast spell with 5% proficiency (hard minimum)
- [ ] Fatigue at 0.03125 (multiple halvings)
- [ ] Learn all 4 spells at once
- [ ] Play with 0 learned spells
- [ ] Speed expires mid-combat
- [ ] Weapon breaks during combat
- [ ] Character dies with locked spell
- [ ] Revival and spell still locked

---

## TROUBLESHOOTING

### Issue: Import errors
**Solution:** Verify all imports in each file match new structure

### Issue: Character creation crashes
**Solution:** Ensure character_NEW.py is installed correctly

### Issue: Spells don't cast
**Solution:** Check cmd_cast() and _attempt_cast() implementation

### Issue: Fatigue doesn't recover
**Solution:** Verify recovery called in movement/rest, check formula

### Issue: Proficiency doesn't increase
**Solution:** Verify skill growth logic in _attempt_cast(), check success check

### Issue: Speed doesn't work
**Solution:** Verify activate_speed() called, tick_speed_duration() in monster_round()

### Issue: Weapon critical/fumble doesn't trigger
**Solution:** Verify percentages (5% and 4%), check secondary roll tables

---

## FINAL CHECKLIST

- [ ] All Phase 1 tests pass
- [ ] All Phase 2 tests pass
- [ ] All Phase 3 tests pass
- [ ] All Phase 4 unit tests pass
- [ ] All Phase 4 integration tests pass
- [ ] All Phase 4 regression tests pass
- [ ] All Phase 4 edge cases pass
- [ ] Documentation updated
- [ ] README.md updated with new system
- [ ] MANUAL.md updated with new spells/proficiencies
- [ ] All backup files safely stored

---

## OPTIONAL: ADVANCED FEATURES

After completion, consider adding:

- [ ] "Learn" command in tavern (shortcut to Aldric)
- [ ] Proficiency caps (e.g., max 100%)
- [ ] Experience-based proficiency growth
- [ ] Enchantment effects for rings/cloaks
- [ ] Additional spells for higher levels
- [ ] Spell combination mechanics
- [ ] Weapon specialization (expert proficiency bonus)
- [ ] Spell school system (fire, frost, lightning, etc.)

---

## ESTIMATED TIME

| Phase | Task | Time |
|-------|------|------|
| 1 | File replacement | 30 min |
| 2 | Engine rewrite | 3-4 hours |
| 3 | Tavern updates | 1-2 hours |
| 4 | Testing | 1-2 hours |
| **Total** | **Complete rewrite** | **6-9 hours** |

---

## NOTES

- Take breaks between phases
- Test thoroughly after each phase
- Keep backup files for rollback
- Ask questions in transcript if stuck
- Celebrate when complete! 🎉

---

**Good luck, Rick! You've got this.** 🎮✨
