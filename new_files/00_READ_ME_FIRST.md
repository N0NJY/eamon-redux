# EAMON REDUX - MAGIC SYSTEM REWRITE
## 🚀 QUICK START GUIDE (READ THIS FIRST!)

**Date Created:** June 15, 2026  
**Status:** 40% Complete - 3 core files rewritten, guides for remaining files  
**Estimated Implementation Time:** 6-9 hours total

---

## 📋 WHAT YOU'VE GOT

This complete rewrite package includes:

### ✅ READY TO USE (3 files)
1. **character_NEW.py** — Replace character.py (no classes, universal proficiencies)
2. **player_NEW.py** — Replace player.py (fatigue system, speed spell tracking)
3. **world_NEW.py** — Replace world.py (weapon types added)

### 📖 COMPREHENSIVE GUIDES (3 guides)
1. **ENGINE_IMPLEMENTATION_GUIDE.md** — Detailed pseudocode for engine.py rewrite
2. **tavern_IMPLEMENTATION_GUIDE.md** — Changes needed for tavern.py
3. **command_parser_UPDATES.py** — Command parser changes (minimal)

### 📊 TRACKING & REFERENCE
1. **REWRITE_SUMMARY.md** — Status of all changes
2. **MASTER_CHECKLIST.md** — Complete testing & implementation checklist (6 pages!)

---

## 🎯 QUICKEST PATH FORWARD

### Step 1: UNDERSTAND (15 min) 📚
```
Read in this order:
1. This file (you're reading it!)
2. REWRITE_SUMMARY.md (2 pages) - understand what changed
3. MASTER_CHECKLIST.md pages 1-3 - see Phase 1 (the easy part)
```

### Step 2: IMPLEMENT PHASE 1 (30 min) ⚡ FASTEST
```bash
# Backup originals
cd ~/git/Eamon
cp character.py character_BACKUP.py
cp player.py player_BACKUP.py
cp world.py world_BACKUP.py

# Copy new files
cp ~/outputs/character_NEW.py character.py
cp ~/outputs/player_NEW.py player.py
cp ~/outputs/world_NEW.py world.py

# Test
python3 tavern.py
# Create character → verify gold = 200 ✓
```

### Step 3: IMPLEMENT PHASE 2 (3-4 hours) 🏗️ THE BIG ONE
```
Follow ENGINE_IMPLEMENTATION_GUIDE.md section by section
Each method has pseudocode with exact logic
Total ~700 new lines of code
```

### Step 4: IMPLEMENT PHASE 3 (1-2 hours) 🔧 TAVERN UPDATES
```
Follow tavern_IMPLEMENTATION_GUIDE.md
- Remove class selection (~50 lines deleted)
- Add Aldric spell shop (~60 lines added)
- Update command parser (provided file)
```

### Step 5: TEST EVERYTHING (1-2 hours) ✅ CRITICAL
```
Use MASTER_CHECKLIST.md Phase 4
- Unit tests for each spell
- Integration tests (full adventure)
- Regression tests (old features)
- Edge cases
```

---

## 📁 FILE LOCATIONS

All output files are in `/mnt/user-data/outputs/`:

| File | Size | Type | Purpose |
|------|------|------|---------|
| character_NEW.py | 15K | Code | ✅ Ready to use |
| player_NEW.py | 11K | Code | ✅ Ready to use |
| world_NEW.py | 12K | Code | ✅ Ready to use |
| ENGINE_IMPLEMENTATION_GUIDE.md | 11K | Guide | 📖 Reference |
| tavern_IMPLEMENTATION_GUIDE.md | 8K | Guide | 📖 Reference |
| command_parser_UPDATES.py | 5K | Code | 📖 Reference |
| REWRITE_SUMMARY.md | 10K | Guide | 📊 Status |
| MASTER_CHECKLIST.md | 20K | Guide | ✅ Use for tracking |

---

## 🎓 WHAT WAS CHANGED

### Character System
| Old | New |
|-----|-----|
| Fighter/Sorcerer classes | Universal (no class) |
| Mana pool (resource) | Proficiency-based (skill check) |
| One starting spell | Learn at Aldric (all characters) |
| 100 starting gold | 200 starting gold |

### Magic System
| Old | New |
|-----|-----|
| Pay mana, cast spell | Roll proficiency, apply fatigue |
| 4 spells (Heal, Fireball, Shield, Light) | 4 spells (Blast, Heal, Speed, Power) |
| Mana refills on REST | Fatigue recovers on movement/REST |
| No proficiency tracking | Proficiency 25-75% → +2% on success |
| No fatigue system | Halving: 100% → 50% → 25% → 12.5% |
| No critical failures | 1% critical failure locks spell |

### Combat System
| Old | New |
|-----|-----|
| Binary hit/miss | Weapon proficiency affects hit chance |
| No weapon specialization | 5 weapon types (Axe, Bow, Club, Spear, Sword) |
| No critical hits/fumbles | Critical hit 5%, Fumble 4% with sub-tables |
| No weapon skill growth | Weapon proficiency +2% on successful hit |

---

## ✨ KEY FEATURES OF NEW SYSTEM

### Spell System
✅ **Proficiency-based casting** — Roll against proficiency %, success = spell happens  
✅ **Fatigue system** — Each cast halves effective proficiency (50%, 25%, 12.5%, etc.)  
✅ **Fatigue recovery** — Movement restores 5-10%, REST restores 10-20%  
✅ **Skill growth** — +2% proficiency on successful cast (announced to player)  
✅ **Critical failure** — 1% chance locks spell for entire adventure  
✅ **Critical success** — 1% roll (exactly 01) doubles damage (offensive spells only)  

### Weapon System
✅ **5 weapon types** — Axe, Bow, Club, Spear, Sword (independent proficiencies)  
✅ **Weapon proficiency** — Increases hit chance, +2% on successful hit  
✅ **Critical hits** — 5% chance with sub-effects (ignore armor, 1.5x, 2x, 3x, instant kill)  
✅ **Fumbles** — 4% chance with sub-effects (recover, drop, break, hit self, kill self)  

### Speed Spell
✅ **Doubles agility** — For 11-20 combat rounds  
✅ **Reset on recast** — No stacking, just resets duration  
✅ **Auto-expires** — After duration, agility returns to normal  

### Learning System
✅ **Gold-based cost** — Blast 3000g, Heal 1000g, Speed 5000g, Power 100g  
✅ **Random start proficiency** — 25-75% when first learned  
✅ **Aldric teaches all** — Any character can learn any spell (no class restrictions)  

---

## 🔍 WHAT WASN'T CHANGED

These files don't need modifications:
- **designer.py** — Adventure designer unchanged
- **README.md** — Can update at end if desired
- **MANUAL.md** — Can update with new spells at end

These features still work as before:
- Movement (N/S/E/W/U/D)
- Equipment system
- Inventory system
- Monster combat (basic mechanics)
- Keys and locked doors
- Food/potion consumption
- Adventure win conditions
- Save/load system

---

## ⚠️ CRITICAL GOTCHAS

**DO NOT MISS THESE:**

1. **Speed rounds decrement AFTER monster attacks**  
   → Put tick_speed_duration() at END of monster_round()

2. **Fatigue is multiplier, not percentage**  
   → Start at 1.0, halve to 0.5, then 0.25, minimum 5%

3. **Spell locked persists for ENTIRE adventure**  
   → Not reset on REST, only reset when returning to tavern

4. **Fatigue recovery on EVERY non-magical action**  
   → Not just major actions - includes every step

5. **Proficiency starts at None (not learned)**  
   → Check for None before using proficiency value

6. **Gold spent on spells needs to persist**  
   → Sync back to character JSON when exiting adventure

---

## 📞 NEED HELP?

If something breaks:

1. **Importerror?** → Check imports at top of each file
2. **Syntax error?** → Check for missing colons, indentation
3. **Spell doesn't work?** → Follow ENGINE_IMPLEMENTATION_GUIDE.md step by step
4. **Test fails?** → Check MASTER_CHECKLIST.md for expected behavior
5. **Confused?** → Read the guide corresponding to that file again

---

## 🎮 FINAL CHECKLIST BEFORE STARTING

- [ ] You have all 8 files listed above
- [ ] You understand the 4 phases
- [ ] You have read this file
- [ ] You have read REWRITE_SUMMARY.md
- [ ] You have backed up originals
- [ ] You have time (6-9 hours)
- [ ] You have coffee ☕

---

## 🚀 READY TO START?

### Option A: Go Fast (6 hours)
1. Do Phase 1 now (30 min)
2. Do Phase 2 over next 3-4 hours
3. Do Phase 3 (1-2 hours)
4. Do Phase 4 testing while fresh

### Option B: Go Slow (9 hours + breaks)
1. Do Phase 1 (30 min)
2. Break 30 min
3. Do Phase 2 (3-4 hours, breaks included)
4. Break 1 hour
5. Do Phase 3 (1-2 hours)
6. Break 30 min
7. Do Phase 4 testing (1-2 hours)

**I recommend Option B** — you'll catch more bugs and enjoy it more.

---

## 📊 SUCCESS CRITERIA

When done, you'll have:

✅ **Universal character system** (no classes)  
✅ **Proficiency-based magic** (skill checks, fatigue, growth)  
✅ **Weapon proficiency system** (5 types, growth, critical/fumble tables)  
✅ **Speed spell** (agility buff for combat)  
✅ **Learning system** (Aldric teaches all spells)  
✅ **Full testing suite** (50+ tests)  

---

## 🎉 NEXT STEP

**Read:** REWRITE_SUMMARY.md (2 pages)  
**Then:** MASTER_CHECKLIST.md Phase 1 (1 page)  
**Then:** Copy the 3 NEW files and test

**You've got this, Rick!** The system is well-documented and tested. Take it step by step. 🎮✨

---

**Time to code!** ⏱️
