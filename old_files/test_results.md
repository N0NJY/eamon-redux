# Eamon Redux — Manual Verification Results

**Date:** 2026-06-19  
**Manual:** `documentation/MANUAL.md`  
**Verdict:** ALL 12 BUGS FIXED

---

## Summary

| Category | Pass | Fixed |
|---|---|---|
| Movement | 2 | 7 (BUG-01, BUG-09) |
| Exploration | 4 | 0 |
| Inventory | 3 | 1 (BUG-03) |
| Equipment | 3 | 0 |
| Combat / Health | 5 | 4 (BUG-07, BUG-08, BUG-09, damage bonuses) |
| Magic | 3 | 0 |
| Other | 2 | 2 (BUG-05) |
| System / Design | 0 | 5 (BUG-10, BUG-11, BUG-12, class/mana system) |
| **Total** | **22** | **12** |

All bugs listed below are now **FIXED**.

---

## Bug Report & Fix Log

### BUG-01 — All movement commands crash ✅ FIXED
**Commands:** N, S, E, W, U, D, GO \<direction\>  
**Symptom:** `AttributeError: 'Engine' object has no attribute 'running'`  
**Cause:** `Engine.__init__` never set `self.running`. `base_handlers.on_enter_room` only set
it to `False` on win-room trigger.  
**Fix:** Added `self.running = True` to `Engine.__init__` (after `self.enemy = None`).

---

### BUG-02 — TALK TO \<npc\> passes "to" as part of name ✅ FIXED
**Command:** `TALK TO hermit`  
**Symptom:** `"You don't see a to hermit here."`  
**Cause:** `handle()` split on `maxsplit=1`, passing `"to hermit"` to `cmd_talk()`.  
**Fix:** Rewrote TALK handler to detect the `to` preposition and strip it before lookup.

---

### BUG-03 — GET ALL \<type\> routes to GET instead of GET ALL ✅ FIXED
**Command:** `GET ALL POTIONS`  
**Symptom:** `"You don't see a all potions here."`  
**Cause:** `handle()` checked `parts[1] == "all"` (False for `"all potions"`) and fell through.  
**Fix 1:** `handle()` now checks `rest.lower().startswith("all ")` and routes to `cmd_get_all()`.  
**Fix 2:** `cmd_get_all()` now strips plural 's' from the filter noun and matches bidirectionally
(`"potions"` → strips to `"potion"` → matches artifact_type `"potion"`).

---

### BUG-04 — FIGHT and HIT aliases missing ✅ FIXED
**Commands:** `FIGHT <monster>`, `HIT <monster>`  
**Symptom:** `"Unknown command."`  
**Cause:** `command_parser.py` only listed `["kill", "att", "a"]` as aliases for `attack`.  
**Fix:** Added `"fight"` and `"hit"` to the alias list.

---

### BUG-05 — SAVE and LOAD are stubs ✅ FIXED
**Commands:** `SAVE`, `LOAD`  
**Symptom:** Both printed `"...coming soon."`  
**Fix:** `cmd_save()` now serializes full player state + world state (monster HP/alive/location,
artifact locations) via `save_game_slotted()`. `cmd_load()` restores all of it and calls
`look()` to redraw the room. Uses the existing 3-slot interactive save menu from `save_system.py`.

---

### BUG-06 — REST restores full HP instead of 25% ✅ FIXED
**Command:** `REST`  
**Symptom:** HP jumps to max.  
**Cause:** `cmd_rest()` set `self.player.hp = self.player.hp_max`.  
**Fix:** Now restores `hp_max // 4` HP and `mana_max // 4` mana per rest.

---

### BUG-07 — Proficiency grows by 2%, not 1% ✅ FIXED
**Symptom:** Both weapon proficiency (combat) and spell proficiency grew by 2% per use.  
**Cause:** engine.py used `old_prof + 2` in both the weapon hit path and `_attempt_cast()`.  
**Fix:** Changed to `+= 1` in both locations.

---

### BUG-08 — Critical hit Instant Kill branch missing ✅ FIXED
**Symptom:** Roll of 100 on the crit sub-table had no effect (3× case handled 96–99; 100 fell through).  
**Fix:** Added `else` branch: sets `monster.hp = 0` and prints instant-kill message.

---

### BUG-09 — Movement not blocked by hostile monsters ✅ FIXED
**Symptom:** Player could walk away from hostile monsters.  
**Fix:** Added hostile-monster check at top of `cmd_go()` — returns with warning if any
`Attitude.HOSTILE` monster is alive in the current room.

---

### BUG-10 — Wizard shop spell keys are wrong ✅ FIXED
**Symptom:** `_SPELL_BASE_PRICE` used `light`, `shield`, `fireball` (non-existent spells).  
**Fix:** Replaced with `{"blast": 100, "heal": 50, "speed": 200, "power": 25}`.

---

### BUG-11 — No Fighter / Sorcerer class system ✅ FIXED
**Symptom:** All characters were mechanically identical with no class field.  
**Fixes:**
- Added `character_class: str = "fighter"` to `Character` and `Player` dataclasses.
- `Character.create_interactive()` now asks Fighter vs. Sorcerer before stat rolling.
- Sorcerers display mana in stat summary; Fighters do not.
- Sorcerers choose a starting spell (25–75% proficiency) at creation.
- Wizard shop now filters available spells by class (Fighters can only buy Heal).
- `cmd_attack()` only adds Strength bonus to melee damage for Fighters.
- Character save/load includes `character_class` field.

---

### BUG-12 — No mana system ✅ FIXED
**Symptom:** No mana fields existed; spells never checked/deducted mana.  
**Fixes:**
- Added `mana: int` and `mana_max` (= `intelligence × 2`) to `Player`.
- Added `mana_cost` to each spell in `SPELL_DEFS` (Blast 3, Heal 2, Speed 5, Power 1).
- `_attempt_cast()` checks mana before casting and deducts on success.
- `cmd_health()` now shows `Mana: X/Y`.
- `cmd_spells()` now shows each spell's mana cost and a ✦/✗ affordability indicator.
- `cmd_rest()` now restores `mana_max // 4` mana per rest.
- `_cast_blast()` and `_cast_heal()` add `intelligence_bonus` to damage/healing.
- Engine initializes player with `mana = character.mana_max`.

---

## Additional Fixes (not in original bug list)

- **Agility bonus to damage:** `cmd_attack()` now adds `agility_effective_bonus` to all weapon
  damage (doubled while Speed spell is active).
- **Strength bonus to damage (Fighters only):** `cmd_attack()` adds `strength_bonus` for
  `character_class == "fighter"`.
- **war axe weapon_type:** `characters/fletcher_items.json` was missing `weapon_type: "axe"`;
  fixed so proficiency tracking works for the starting weapon.

---

## Commands — Final Status

| Command | Status |
|---|---|
| N / S / E / W / U / D | ✅ |
| GO \<direction\> | ✅ |
| LOOK / L | ✅ |
| EXAMINE \<x\> / X | ✅ |
| READ \<item\> | ✅ |
| OPEN \<item\> / CLOSE \<item\> | ✅ |
| INVENTORY / I / INV | ✅ |
| GET \<item\> | ✅ |
| GET ALL | ✅ |
| GET ALL \<type\> | ✅ |
| DROP \<item\> | ✅ |
| EQUIP / WEAR / WIELD | ✅ |
| UNEQUIP / REMOVE | ✅ |
| EQUIPMENT / EQ | ✅ |
| ATTACK \<monster\> | ✅ |
| KILL / FIGHT / HIT \<monster\> | ✅ |
| FLEE | ✅ |
| UNLOCK \<direction\> | ✅ |
| TALK TO \<npc\> | ✅ |
| EAT \<food\> | ✅ |
| DRINK \<potion\> | ✅ |
| CAST \<spell\> \[target\] | ✅ |
| SPELLS | ✅ (shows mana cost + affordability) |
| HEALTH / HP | ✅ (shows mana) |
| REST | ✅ (25% HP + 25% mana) |
| SAVE | ✅ (3-slot save menu) |
| LOAD | ✅ (slot selection + room redraw) |
| HELP / ? | ✅ |
| QUIT | ✅ |
