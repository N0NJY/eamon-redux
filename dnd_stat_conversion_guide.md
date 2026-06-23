# Eamon Redux — D&D Stat Conversion Guide

## Overview

This guide specifies the complete conversion from Eamon's current 5-stat system
(Hardiness, Agility, Strength, Intelligence, Charisma) to a 6-stat D&D-style
system (STR, DEX, CON, INT, WIS, CHA).

The formulas remain d100 / linear-bonus-based (not THAC0 or lookup tables).
The bonus formula throughout is `(stat - 10) // 2`, identical to d20/3e.
Ascending AC is kept (higher AC = harder to hit).

No character classes are added. The system stays classless — any character
can learn any spell or weapon skill. The D&D stat names and meanings are
adopted while preserving Eamon's open structure.

---

## The Six Stats

### STR — Strength
- **Governs:** Melee damage, carrying capacity
- **Bonus formula:** `(str - 10) // 2`
- **Default:** 10
- **Replaces:** The former Strength stat (no rename needed — already correct)
- **Change from current:** STR bonus is ONLY added to melee damage.
  DEX is no longer added to melee damage (see below).
  Carrying capacity moves from CON to STR.

| STR | Bonus | Carry (gronds) | Notes |
|-----|-------|----------------|-------|
|  6  |  -2   |   60           |       |
|  8  |  -1   |   80           |       |
| 10  |   0   |  100           | default |
| 12  |  +1   |  120           |       |
| 14  |  +2   |  140           |       |
| 16  |  +3   |  160           |       |
| 18  |  +4   |  180           |       |

Carry capacity formula: `str * 10` gronds.

### DEX — Dexterity
- **Governs:** Melee hit chance, ranged hit chance, AC bonus (defensive),
  Speed spell multiplier, flee/escape defense
- **Bonus formula:** `(dex - 10) // 2`
- **Default:** 10
- **Replaces:** Agility (renamed)
- **Change from current:** DEX bonus is REMOVED from melee damage.
  Previously agility added to both hit AND damage. Now only STR adds to damage.
  DEX remains the "hit chance" and "defense" stat.

| DEX | Bonus | Notes |
|-----|-------|-------|
|  6  |  -2   |       |
|  8  |  -1   |       |
| 10  |   0   | default |
| 12  |  +1   |       |
| 14  |  +2   |       |
| 16  |  +3   |       |
| 18  |  +4   | Speed spell: effective DEX 36, bonus +13 |

Speed spell doubles DEX (not just agility_bonus), same as current.

### CON — Constitution
- **Governs:** HP pool, HP max calculation
- **Bonus formula:** `(con - 10) // 2` (used in display/equipment bonuses)
- **HP formula:** `con * 2` (unchanged from current hardiness * 2)
- **Default:** 10
- **Replaces:** Hardiness (renamed)
- **Change from current:** Name only. Carrying capacity moves to STR.

| CON | HP Max | Notes |
|-----|--------|-------|
|  6  |   12   |       |
|  8  |   16   |       |
| 10  |   20   | default |
| 12  |   24   |       |
| 14  |   28   |       |
| 16  |   32   |       |
| 18  |   36   |       |

### INT — Intelligence
- **Governs:** Mana pool, spell power (Blast damage, Heal healing)
- **Bonus formula:** `(int - 10) // 2`
- **Mana formula:** `int * 2` (unchanged)
- **Default:** 10
- **No change from current** — stat name and role unchanged.

| INT | Mana Max | Spell Bonus | Notes |
|-----|----------|-------------|-------|
|  6  |   12     |     -2      |       |
|  8  |   16     |     -1      |       |
| 10  |   20     |      0      | default |
| 12  |   24     |     +1      |       |
| 14  |   28     |     +2      |       |
| 16  |   32     |     +3      |       |
| 18  |   36     |     +4      |       |

### WIS — Wisdom  *(NEW STAT)*
- **Governs:** Saving throws (vs. magic, fear, paralysis, charm, poison),
  spell resistance (monster spells targeting player),
  Heal spell bonus (wise characters heal more effectively),
  future: perception/hidden doors
- **Bonus formula:** `(wis - 10) // 2`
- **Default:** 10 (for all existing characters on migration)
- **No equivalent in current system** — this is a new addition.

| WIS | Bonus | Save% bonus | Heal bonus |
|-----|-------|-------------|------------|
|  6  |  -2   |   -10%      |    -2      |
|  8  |  -1   |    -5%      |    -1      |
| 10  |   0   |     0%      |     0      | default |
| 12  |  +1   |    +5%      |    +1      |       |
| 14  |  +2   |   +10%      |    +2      |       |
| 16  |  +3   |   +15%      |    +3      |       |
| 18  |  +4   |   +20%      |    +4      |       |

Save% bonus = `wis_bonus * 5` (converts to d100 system).
Heal bonus = `wis_bonus` added to Heal spell restoration (same as int_bonus
on Blast), so Heal = `1d10 + int_bonus + wis_bonus`.

### CHA — Charisma
- **Governs:** NPC reactions (Marie Laveau), shop pricing discounts,
  follower loyalty (future)
- **Bonus formula:** `(cha - 10) // 2`
- **Default:** 10
- **No change from current** — stat name and role unchanged.

---

## Derived Values Summary

| Stat | Derived Value | Formula |
|------|---------------|---------|
| STR  | Melee damage bonus | `(str - 10) // 2` |
| STR  | Carry capacity | `str * 10` gronds |
| DEX  | Melee hit bonus | `(dex - 10) // 2` |
| DEX  | Ranged hit bonus | `(dex - 10) // 2` |
| DEX  | AC bonus (player defense) | `(dex - 10) // 2` |
| DEX  | Speed spell multiplier | `dex * 2` (then bonus recalculated) |
| CON  | HP max | `con * 2` |
| INT  | Mana max | `int * 2` |
| INT  | Blast/Heal power bonus | `(int - 10) // 2` |
| WIS  | Saving throw bonus | `(wis - 10) // 2 * 5` (%) |
| WIS  | Heal bonus | `(wis - 10) // 2` |
| WIS  | Spell resistance | `(wis - 10) // 2 * 5` (%) |
| CHA  | Marie Laveau attitude | +1 if CHA ≥ 16, -1 if CHA ≤ 7 |
| CHA  | Shop price modifier | discount if CHA ≥ 15, surcharge if CHA ≤ 8 |

---

## Combat Formulas (Old → New)

### Player attacks monster

**OLD:**
```
hit_chance = 50 + agility_effective_bonus + weapon_prof - monster_ac
damage = weapon_roll + agility_effective_bonus + strength_bonus
```

**NEW:**
```
hit_chance = 50 + dex_effective_bonus + weapon_prof - monster_ac
damage = weapon_roll + str_bonus
```

Key change: DEX no longer contributes to damage. STR_bonus is the sole
damage modifier. A high-DEX, low-STR character will hit often but hit
lighter. A high-STR, low-DEX character hits hard but less reliably.

### Monster attacks player

**OLD:**
```
hit_chance = 50 - player.agility_effective_bonus - player.armor_class
```

**NEW:**
```
hit_chance = 50 - player.dex_effective_bonus - player.armor_class
```

No formula change — just the property name changes.

### Carrying capacity

**OLD:** `carry_capacity = hardiness * 10`

**NEW:** `carry_capacity = str * 10`

---

## Saving Throw System (New)

Saving throws use the existing d100 framework (roll-under = success).

### Base save chance
```
save_chance = 50 + (wis - 10) // 2 * 5
```
WIS 10 = 50% base. WIS 16 = 65%. WIS 6 = 40%.
Clamped to [5, 95] same as hit chance.

### When saves trigger
Triggered by monster special attack types. These are adventure-defined
via monster flags or room events. Suggested categories:

| Category | Examples |
|----------|---------|
| `save_magic`    | Monster casts Blast, sleep, hex |
| `save_fear`     | Dragon roar, undead aura, demon presence |
| `save_paralysis`| Ghoul touch, hold person |
| `save_poison`   | Snake bite, spider venom, poisoned dart |
| `save_charm`    | Sirens, enchantments, NPC persuasion |

### Save outcomes
- **Success (roll ≤ save_chance):** Effect halved or negated (per category).
- **Failure (roll > save_chance):** Full effect applied.

### Implementation in engine
When a monster special attack triggers, call:
```python
def attempt_save(self, category: str) -> bool:
    wis_bonus = (self.player.wis - 10) // 2
    save_chance = max(5, min(95, 50 + wis_bonus * 5))
    return random.randint(1, 100) <= save_chance
```
Return True = save successful (resist), False = save failed (affected).

### Spell resistance (WIS vs monster spells)
When a monster uses a spell-type attack against the player, the player
gets a `save_magic` check automatically. This replaces any fixed
resistance the monster might have had. No separate "spell resistance"
stat is needed — WIS handles it.

---

## Spell System

### INT role (unchanged)
- `mana_max = int * 2`
- `int_bonus = (int - 10) // 2` added to Blast damage and Heal healing
- Spell proficiency gain/success: unchanged (proficiency %, not INT-gated)

### WIS role (new)
- `wis_bonus = (wis - 10) // 2` added to Heal healing
  (Heal = `1d10 + int_bonus + wis_bonus`)
- WIS saving throw applies when monsters use magical attacks
- Power spell (adventure-specific): WIS can gate adventure-defined effects
  (e.g., WIS ≥ 12 required to see through an illusion)

### Updated spell effects

| Spell | Cost | Mana | Effect |
|-------|------|------|--------|
| Blast | 1000g | 3 | `1d6 + int_bonus` damage, bypasses armor |
| Heal  | 500g  | 2 | `1d10 + int_bonus + wis_bonus` HP restored |
| Speed | 4000g | 5 | DEX doubled for 11-20 rounds |
| Power | 100g  | 1 | Adventure-specific (WIS may affect outcome) |

---

## Character Sheet Display

The `stat_summary()` output should show stats in D&D order:

```
STR: 14    DEX: 12    CON: 16    INT: 10    WIS: 13    CHA: 11

  HP:  32/32    Mana: 20/20    XP:  500    Level: 2

  Carry: 140 gronds max
  Melee dmg bonus: +2 (STR)    Hit bonus: +1 (DEX)
  Save bonus: +5% (WIS)
```

Equipment bonus format unchanged: `14+2` when item active.

---

## File-by-File Change Inventory

### character.py

| Change | Detail |
|--------|--------|
| Rename field `hardiness` → `con` | Rename everywhere |
| Rename field `agility` → `dex` | Rename everywhere |
| Keep field `strength` | Already correct name (`str` is a Python builtin — keep `strength` as the field name, expose as STR in display) |
| Keep field `intelligence` | No change |
| Add field `wis: int = 10` | New stat |
| Keep field `charisma` | No change |
| `hp_max`: change `self.hardiness * 2` → `self.con * 2` | |
| `mana_max`: no change | |
| `carry_capacity`: change `self.hardiness * 10` → `self.strength * 10` | Move from CON to STR |
| `intelligence_bonus`: no change | |
| Add `wis_bonus` property: `(self.wis - 10) // 2` | New |
| `stat_summary()`: rename labels, add WIS row, update derived displays | Show STR/DEX/CON/INT/WIS/CHA |
| `_STATS` tuple: update to include `'wis'`, remove `'hardiness'`/`'agility'` | |
| `to_dict()` / `from_dict()`: rename keys, add wis | |
| `learn_spell()`: no change | |

Note: avoid naming the field `str` (Python builtin). Keep field name
`strength` but display label as "STR".

### player.py

| Change | Detail |
|--------|--------|
| Rename field `hardiness` → `con` | |
| Rename field `agility` → `dex` | |
| Keep field `strength` | |
| Add field `wis: int = 10` | |
| `hp_max`: `self.con * 2` | |
| `mana_max`: no change (`self.intelligence * 2`) | |
| `agility_bonus` → `dex_bonus`: `(self.dex - 10) // 2` | |
| `agility_effective` → `dex_effective`: speed spell doubles `self.dex` | |
| `agility_effective_bonus` → `dex_effective_bonus` | |
| `strength_bonus`: no change | |
| `intelligence_bonus`: no change | |
| Add `wis_bonus`: `(self.wis - 10) // 2` | |
| `max_carry_weight`: remove hardcoded 100 — derive from strength in `__post_init__` | |
| `_STATS` in equipment bonus loop: add `'wis'`, rename others | |
| `_apply_stat_bonuses()`: already generic — works if stat field names match | |

### engine.py

| Change | Detail |
|--------|--------|
| Engine init: pass `wis=character.wis` when building Player | |
| `cmd_status()`: add `wis` to effective_stats dict | |
| Player attack formula: `agility_effective_bonus` → `dex_effective_bonus` | line ~1428 |
| Player damage: REMOVE `self.player.agility_effective_bonus` from damage | line ~1498 |
| Monster attack formula: `agility_effective_bonus` → `dex_effective_bonus` | line ~1639 |
| Add `attempt_save(category)` method | New |
| `_cast_heal()`: add `wis_bonus` to healing | line ~1343 |
| `_cast_speed()`: rename internal `agility` refs to `dex` | |
| `_apply_save_data()`: add `wis` to fields restored | |
| `cmd_status()`: add `wis` to effective stats shown | |

### tavern.py

| Change | Detail |
|--------|--------|
| `_STATS` list: `["strength", "dex", "con", "intelligence", "wis", "charisma"]` | |
| `_STAT_NAMES` dict: update display labels | |
| `_STAT_ALIASES` dict: add `"wis"`, `"wi"`, `"con"`, `"co"`, `"dex"`, `"de"` | |
| `_marie_total_attitude()`: `character.charisma` ref — no change needed | |
| `_tavern_effective_stats()`: add `'wis'` to stat list | |
| `show_character_sheet()`: passes effective_stats — no change to call site | |
| Marie/Aldric stat boost options: add WIS as purchasable stat | |

### adventures/*/artifacts.json

Any artifact with `stat_bonuses` using old stat names must be updated:

| Old key | New key |
|---------|---------|
| `"hardiness"` | `"con"` |
| `"agility"` | `"dex"` |
| `"strength"` | `"strength"` (no change) |
| `"intelligence"` | `"intelligence"` (no change) |
| `"charisma"` | `"charisma"` (no change) |

Currently only these adventures have stat_bonuses artifacts:
- `beginners_cave/artifacts.json` — ring with `"intelligence": 2` (no change needed)
- `lair-of-the-minotaur/artifacts.json` — morning star with `"strength": 2` (no change needed)

### stored_characters/*.json

Character JSON files use the old field names. Migration required:

| Old field | New field | Action |
|-----------|-----------|--------|
| `"hardiness"` | `"con"` | rename |
| `"agility"` | `"dex"` | rename |
| `"strength"` | `"strength"` | no change |
| `"intelligence"` | `"intelligence"` | no change |
| `"charisma"` | `"charisma"` | no change |
| *(absent)* | `"wis"` | add with value 10 |

---

## Old Character Migration

Two options:

**Option A — Lazy migration (recommended):**
Update `Character.from_dict()` to accept both old and new field names:
```python
self.con = data.get('con', data.get('hardiness', 10))
self.dex = data.get('dex', data.get('agility', 10))
self.wis = data.get('wis', 10)
```
Old character files load correctly without modification. On next save,
the file is written with new field names. Clean, zero manual work.

**Option B — Migration script:**
Write a one-shot script that reads all `stored_characters/*.json`,
renames fields, adds `wis: 10`, and overwrites. Run once.

---

## New Character Creation

### Stat generation (tavern.py `create_character`)
Add WIS to stat rolling. Existing roll method (3d6 or point-buy) applies.

### Stat order on character creation screen
```
STR (Strength)       Roll or enter value
DEX (Dexterity)      Roll or enter value
CON (Constitution)   Roll or enter value
INT (Intelligence)   Roll or enter value
WIS (Wisdom)         Roll or enter value
CHA (Charisma)       Roll or enter value
```

### Default values
All stats default to 10 if not set. WIS = 10 for any character lacking the field.

---

## Balance Notes

### DEX removed from melee damage — impact
Current: DEX 16 character gets +3 to hit AND +3 to damage.
After: DEX 16 character gets +3 to hit only. STR 16 needed for +3 damage.

Characters built around agility alone will hit more reliably but deal
base damage. This is the correct D&D model and creates a meaningful
STR vs DEX tradeoff.

Existing characters with high agility/low strength will see a damage
reduction in-game. This is intentional and improves character
differentiation.

### WIS at default 10 — no immediate effect
All existing characters migrate with WIS 10 (bonus = 0). Save chance is
50%. Only characters who visit Marie Laveau to raise WIS, or who equip
WIS-boosting items, will see a difference. Safe to introduce.

### CON → carry_capacity → STR change
A character with CON 16 and STR 10 currently carries 160 gronds. After
conversion they carry 100 gronds. A CON 16, STR 10 character took a
carrying capacity nerf. Worth noting for existing characters, but
reflects proper D&D semantics (muscle carries things, not constitution).

---

## Implementation Order

Recommended sequence to minimise breakage at each step:

1. `character.py` — rename fields, add WIS, update all methods
2. `player.py` — rename fields, add WIS, update all properties
3. `engine.py` — update combat formulas, add `attempt_save()`, update
   spell effects, update `_apply_save_data()`
4. `tavern.py` — rename all references, add WIS to stat menus
5. Run the game, verify character sheet shows correct labels
6. Test combat: verify DEX not in damage, STR is
7. Test Heal: verify WIS bonus applies
8. Test save/resume: verify WIS persists
9. Adventures: update any artifact stat_bonus keys if needed
10. Old character files: lazy migration via `from_dict()` fallback

---

## Open Questions

These items are not resolved by this guide and need a decision before
implementing:

1. **Initiative system?** DEX is listed as governing initiative, but
   we have no initiative roll. First strike is always the player. Add
   a DEX vs. monster DEX roll to determine who acts first? Or leave
   player-always-first as-is for now?

2. **WIS and perception?** Listed as a future feature. Not implementing
   now — but should hidden doors/traps be flagged with a WIS DC in room
   data for later?

3. **Ranged weapons?** Bows exist as artifact type. We have no separate
   ranged attack formula. DEX should govern ranged to-hit. Implement now
   or stub?

4. **Follower loyalty (CHA)?** Listed in CHA definition. Currently
   followers exist in code but loyalty isn't CHA-linked. Future work?

5. **Marie Laveau WIS price?** She can already boost any stat. WIS will
   just appear as a purchasable option — no special handling needed beyond
   adding it to her stat list.
