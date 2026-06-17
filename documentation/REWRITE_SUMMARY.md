# EAMON REDUX - MAGIC SYSTEM REWRITE
## Complete Status & Implementation Guide

**Date:** June 15, 2026  
**Status:** 40% Complete (3 of 7 core files rewritten, 1 implementation guide created)

---

## FILES CREATED ✅

### 1. **character_NEW.py** (250 lines)
**Status:** ✅ **READY TO USE**

**Changes from original:**
- ❌ Removed `CharClass` (FIGHTER/SORCERER classes deleted)
- ❌ Removed `mana` and `mana_max` (no longer used)
- ❌ Removed `spells` list (replaced with proficiencies)
- ✅ Added `spell_proficiencies: dict` (None = not learned, int = proficiency %)
  - Keys: "blast", "heal", "speed", "power"
- ✅ Added `weapon_proficiencies: dict` (independent for each weapon type)
  - Keys: "axe"(5%), "bow"(-10%), "club"(20%), "spear"(10%), "sword"(0%)
- ✅ Starting gold: 200 (increased from 100, allows spell learning)
- ✅ New method: `learn_spell(spell_key)` → handles learning cost and proficiency
- ✅ Updated `stat_summary()` → shows ALL spell/weapon proficiencies

**Testing checklist:**
- [ ] Create character, verify gold = 200
- [ ] Check stat_summary shows all proficiencies
- [ ] Load saved character, verify proficiencies persist

---

### 2. **player_NEW.py** (300 lines)
**Status:** ✅ **READY TO USE**

**Changes from original:**
- ❌ Removed `char_class` field
- ❌ Removed `mana`, `mana_max`, `mana_bar()`
- ❌ Removed `spells` list
- ✅ Added `spell_proficiencies: dict` (mirrors character)
- ✅ Added `weapon_proficiencies: dict` (mirrors character)
- ✅ Added `spell_fatigue_multiplier: dict` (1.0, 0.5, 0.25, etc.)
- ✅ Added `spell_locked: dict` (tracks 1% critical failure lock)
- ✅ Added speed spell state:
  - `speed_active: bool`
  - `speed_rounds_remaining: int`
- ✅ New methods for spell fatigue:
  - `get_effective_spell_proficiency(spell_key)` → applies fatigue
  - `apply_spell_fatigue(spell_key)` → halve multiplier
  - `recover_spell_fatigue(spell_key, recovery_pct)` → restore fatigue
  - `recover_all_spell_fatigue(recovery_pct)` → all spells
  - `lock_spell(spell_key)` → 1% critical failure
  - `is_spell_locked(spell_key)` → check lock status
- ✅ New methods for speed spell:
  - `activate_speed(duration)` → start speed spell
  - `deactivate_speed()` → end speed spell
  - `tick_speed_duration()` → decrement rounds
- ✅ New property: `agility_effective` → returns doubled agility if speed active

**Testing checklist:**
- [ ] Verify fatigue halving: 1.0 → 0.5 → 0.25 → 0.125 (5% minimum)
- [ ] Verify fatigue recovery: 5-10% per action
- [ ] Verify speed doubles agility for correct duration
- [ ] Verify spell lock stays locked for adventure

---

### 3. **world_NEW.py** (380 lines)
**Status:** ✅ **READY TO USE**

**Changes from original:**
- ✅ Added `WeaponType` class with constants:
  - AXE, BOW, CLUB, SPEAR, SWORD
- ✅ Added `weapon_type` field to Artifact
  - For weapons: stores which type (axe, bow, club, spear, sword)
  - For other artifacts: None
- ✅ Updated `to_dict()` and `from_dict()` to handle weapon_type

**Testing checklist:**
- [ ] Create weapon artifact with weapon_type="sword"
- [ ] Save/load artifact, verify weapon_type persists

---

### 4. **ENGINE_IMPLEMENTATION_GUIDE.md** (350 lines)
**Status:** ✅ **COMPREHENSIVE REFERENCE**

Complete pseudocode and implementation guide for engine.py covering:
- Spell casting with proficiency checks
- Fatigue system (halving, recovery)
- Skill growth (2% per successful cast)
- Critical failures (1% → locks spell)
- Critical successes (1% roll = 01)
- Weapon proficiency integration
- Critical hit table (5% chance)
- Fumble table (4% chance)
- Speed spell duration tracking
- Fatigue recovery in movement/REST

---

## FILES NOT YET CREATED ⏳

### 5. **engine_PARTIAL.py** (2200+ lines estimated)
**Status:** 🚧 **IN PROGRESS** - Too large for single response

**What needs implementing:**
See `ENGINE_IMPLEMENTATION_GUIDE.md` for detailed specs

**Key methods to add:**
- `cmd_cast(args)` - Main spell casting command
- `_attempt_cast(spell_key, target_name)` - Core spell logic with proficiency check
- `_cast_blast(target_name)` - 1D6 damage, bypasses armor
- `_cast_heal(target_name)` - 1D10 healing
- `_cast_speed(target_name)` - 11-20 round duration, doubles agility
- `_cast_power(target_name)` - Adventure-specific (sonic boom for beginner cave)
- `cmd_spells(args)` - Show all spell proficiencies

**Modifications to existing methods:**
- `cmd_attack(args)` - Add weapon proficiency & critical hits/fumbles
- `cmd_north/south/east/west()` - Add 5-10% fatigue recovery per move
- `cmd_rest()` - Add 10-20% fatigue recovery
- `monster_round()` - Decrement speed duration
- `cmd_health()` - Remove mana display, show speed status
- `__init__()` - Load proficiencies from character
- Character saving → sync proficiencies back

---

### 6. **tavern_UPDATES.py** (Partial)
**Status:** 🚧 **IN PROGRESS**

**Changes needed:**
- Update Aldric NPC (Back Room) to have spell shop
  - Show list of spells with learn costs
  - Buy/learn interface: `B <number>`
  - Check gold and call `character.learn_spell(spell_key)`
- Update character creation to remove class selection UI
- Update stat display to show weapon/spell proficiencies instead of class
- Keep Horace's weapon shop mostly unchanged

---

### 7. **command_parser_UPDATES.py** (Small)
**Status:** 🚧 **IN PROGRESS**

**Changes needed:**
- Spell commands already exist: "cast", "spells"
- Add "heal", "blast", "speed", "power" as aliases for "cast"
  (e.g., `HEAL` → same as `CAST HEAL`)
- Could add LEARN command for spell learning in tavern
- Minor tweaks to help text

---

## IMPLEMENTATION STEPS (FOR RICK)

### PHASE 1: DROP-IN REPLACEMENTS ✅ (30 min)
```bash
# Backup originals
cp character.py character_BACKUP.py
cp player.py player_BACKUP.py
cp world.py world_BACKUP.py

# Replace with new versions
cp character_NEW.py character.py
cp player_NEW.py player.py
cp world_NEW.py world.py
```

**Then test:**
```bash
python3 tavern.py
# Create new character → should have 200 gold
# Check CHARACTER command → should show weapon/spell proficiencies
```

---

### PHASE 2: ENGINE.PY REWRITE ⏳ (2-3 hours)
Follow `ENGINE_IMPLEMENTATION_GUIDE.md` step-by-step:

1. Add imports and constants (10 min)
2. Implement spell casting methods (30 min)
3. Implement weapon proficiency in combat (30 min)
4. Add fatigue recovery to movement (15 min)
5. Add speed spell tracking (15 min)
6. Modify character initialization (10 min)
7. Test each spell individually (30 min)

---

### PHASE 3: TAVERN UPDATES ⏳ (1 hour)
1. Update Aldric NPC shop (30 min)
2. Remove class selection from character creation (15 min)
3. Update stat display (15 min)

---

### PHASE 4: TESTING ✅ (1+ hour)
See TESTING CHECKLIST below

---

## TESTING CHECKLIST

### Basic System Tests
- [ ] Create character: gold = 200, proficiencies initialized
- [ ] Load character: proficiencies persist
- [ ] Delete character works
- [ ] Save/load during adventure works

### Spell Learning Tests
- [ ] Learn spell at Aldric: gold decreases, proficiency set (25-75%)
- [ ] Try to learn spell without enough gold: fails
- [ ] Try to learn spell twice: fails
- [ ] Multiple characters can learn different spells

### Spell Casting Tests
- [ ] Cast spell successfully: proficiency roll succeeds
- [ ] Cast spell fails: proficiency roll fails
- [ ] Proficiency increases on success: +2% announced
- [ ] Fatigue halves on each cast: 100% → 50% → 25% → 12.5%
- [ ] Fatigue recovery on movement: 5-10% recovered
- [ ] Fatigue recovery on REST: 10-20% recovered, larger than move
- [ ] Spell locked on 1% critical failure: stays locked for adventure
- [ ] Spell shows "locked" when attempting to cast locked spell

### Spell-Specific Tests
**BLAST:**
- [ ] Deals 1D6 damage
- [ ] Bypasses armor completely
- [ ] Always hits (proficiency-based success only)
- [ ] Target dies: monster HP → 0
- [ ] Monster attacks back after blast

**HEAL:**
- [ ] Restores 1D10 HP
- [ ] Player at 20/30 HP, cast HEAL, HP increases
- [ ] Can't exceed max HP (capped at hp_max)
- [ ] No combat consequences (monster doesn't attack)

**SPEED:**
- [ ] Activates speed: agility doubled
- [ ] Duration 11-20 rounds (random)
- [ ] Recast SPEED: resets duration, doesn't stack
- [ ] Speed expires after duration: agility back to normal
- [ ] In combat: Speed affects next attack roll

**POWER:**
- [ ] Sonic boom message in Beginner's Cave
- [ ] No actual game effect (just flavor)

### Weapon Proficiency Tests
- [ ] Each weapon type has independent proficiency
- [ ] Proficiency increases on successful hit: +2% announced
- [ ] Weapon critical hit (5% chance): sub-effects trigger
  - [ ] 50% ignore armor
  - [ ] 35% 1.5× damage
  - [ ] 10% 2× damage
  - [ ] 4% 3× damage
  - [ ] 1% instant kill
- [ ] Weapon fumble (4% chance): sub-effects trigger
  - [ ] 35% recover
  - [ ] 40% drop weapon
  - [ ] 20% break weapon (50% damages player)
  - [ ] 4% hit self
  - [ ] 1% kill self

### Integration Tests
- [ ] Return to tavern: proficiencies sync to character
- [ ] Load adventure: proficiencies load correctly
- [ ] Multiple adventures: proficiencies persist between adventures
- [ ] SPELLS command shows all proficiencies
- [ ] HEALTH command shows speed status (if active)
- [ ] No more MANA in any display

---

## FILE COMPARISON

| Aspect | Old System | New System |
|--------|-----------|-----------|
| Classes | Fighter/Sorcerer | Universal (no class) |
| Starting Gold | 100 | 200 |
| Magic System | Mana pool (cost per cast) | Proficiency-based (cost to learn) |
| Spell Learning | Sorcerer-only, 1 at creation | Universal, learn at Aldric |
| Weapon System | By damage (xDy) | By type + proficiency (5 types) |
| Character Stats | Includes mana_max | Removed, proficiencies added |
| Player Runtime | mana pool, spells list | fatigue tracking, proficiencies |
| Spell Casting | Pay mana cost | Roll proficiency, apply fatigue |
| Combat | Hit/Miss binary | Weapon proficiency, crit/fumble tables |

---

## NOTES FOR RICK

**Critical Implementation Order:**
1. Do NOT test Beginner's Cave adventure until engine.py is complete
2. Phase 1 (new files) can be done immediately
3. Phase 2 (engine) is the most complex - take your time
4. Phase 4 (testing) is important - verify each system in isolation first

**Gotchas:**
- Speed spell rounds decrement **after** monster attacks in combat
- Fatigue multiplier is 1.0 initially, then halved each cast (not set to percentage)
- Proficiency 5% is the hard minimum, even with massive fatigue
- Spell locked stays locked for **entire adventure**, not just reset on REST
- Fatigue recovery happens on **every** non-magical action, not just major ones

**Files to NOT modify:**
- designer.py (no changes needed)
- README.md (update at end if needed)
- MANUAL.md (update documentation at end)

---

## NEXT STEPS

1. **Copy new files to ~/git/Eamon/**
2. **Test Phase 1** (character creation)
3. **Implement engine.py** following guide
4. **Implement tavern updates**
5. **Run full testing checklist**
6. **Launch Beginner's Cave adventure**

---

**Questions?** Review ENGINE_IMPLEMENTATION_GUIDE.md for detailed pseudocode.

Good luck! 🎮
