# TAVERN.PY - IMPLEMENTATION GUIDE
## Changes for Magic System Rewrite

---

## OVERVIEW

Three main changes to tavern.py:

1. **Remove class selection** from `Character.create_interactive()`
2. **Update Aldric** (Back Room) to have a spell shop
3. **Update stat display** to show weapon/spell proficiencies instead of class

---

## CHANGE 1: Character Creation (Character class)

### IN: character.py `create_interactive()` method

**DELETE:** Entire class selection section (~30 lines)

From:
```python
        # ── Class selection ───────────────────────────────────────────────────
        print()
        print(tc("  ┌─────────────────────────────────────────────────┐", "border"))
        print(tc("  │  Choose your class:                             │", "title"))
        # ... all the Fighter/Sorcerer UI ...
        print(tc("  └─────────────────────────────────────────────────┘", "border"))
        print()

        while True:
            choice = input(tc("  Choose class (1/2): ", "prompt")).strip()
            if choice == "1":
                char_class = CharClass.FIGHTER
                break
            elif choice == "2":
                char_class = CharClass.SORCERER
                break
            print(tc("  Please enter 1 or 2.", "error"))
```

**DELETE:** The entire spell selection section (~25 lines)

From:
```python
        # ── Spell selection for sorcerers ─────────────────────────────────────
        if char_class == CharClass.SORCERER:
            print()
            print(tc("  ┌─────────────────────────────────────────────────┐", "border"))
            # ... all the spell selection UI ...
            print(tc("  └─────────────────────────────────────────────────┘", "border"))
```

**UPDATE:** Final message

From:
```python
        ch.save()
        print(tc(f"\n  Character '{name}' saved. Good luck out there.", "sys"))
        return ch
```

To:
```python
        ch.save()
        print(tc(f"\n  Character '{name}' saved!", "sys"))
        print(tc(f"  Starting gold: {ch.gold} (learn spells at Aldric in the tavern)", "sys"))
        return ch
```

---

## CHANGE 2: Aldric's Spell Shop (in tavern.py)

### LOCATION: Find the function that handles Aldric (likely `shop_aldric()` or similar)

**Current Aldric function likely:**
- Allows buying magical items
- Allows selling potions/readables

**NEW Aldric function should:**
- Show list of all 4 spells with:
  - Name
  - Cost (gold)
  - Current status (Not learned / Proficiency %)
  - Brief description
- Buy/learn interface: `B <number>`
- Sell interface: `S <number>` (keep potions/readables)
- Check gold
- Call `character.learn_spell(spell_key)`

### PSEUDOCODE:

```python
def shop_aldric(world, player, character, tc):
    """
    Aldric's Arcane Emporium - Buy spells and magical items.
    """
    from character import SPELL_DEFS
    
    while True:
        print()
        print(tc("  ┌─────────────────────────────────────────────────────┐", "border"))
        print(tc("  │  Aldric's Arcane Emporium                           │", "title"))
        print(tc("  ├─────────────────────────────────────────────────────┤", "border"))
        
        # Show all spells
        spell_num = 1
        spell_list = []
        for spell_key, spell_info in SPELL_DEFS.items():
            spell_list.append(spell_key)
            prof = character.spell_proficiencies.get(spell_key)
            if prof is None:
                status = f"Not learned ({spell_info['cost']} gold)"
            else:
                status = f"Proficiency: {prof}%"
            print(tc(f"  │  {spell_num}. {spell_info['name']:<10} {status:<27}│", "stat"))
            spell_num += 1
        
        print(tc("  ├─────────────────────────────────────────────────────┤", "border"))
        print(tc(f"  │  Gold: {character.gold:<47}│", "stat"))
        print(tc("  ├─────────────────────────────────────────────────────┤", "border"))
        print(tc("  │  B <number> = Buy/Learn spell                       │", "desc"))
        print(tc("  │  DONE = Leave                                       │", "desc"))
        print(tc("  └─────────────────────────────────────────────────────┘", "border"))
        
        choice = input(tc("  > ", "prompt")).strip().lower()
        
        if choice == "done":
            break
        
        if choice.startswith("b "):
            try:
                spell_num = int(choice.split()[1]) - 1
                if 0 <= spell_num < len(spell_list):
                    spell_key = spell_list[spell_num]
                    success, msg = character.learn_spell(spell_key)
                    if success:
                        print(tc(f"  {msg}", "success"))
                        player.spell_proficiencies = character.spell_proficiencies.copy()
                    else:
                        print(tc(f"  {msg}", "error"))
                else:
                    print(tc("  Invalid spell number.", "error"))
            except (ValueError, IndexError):
                print(tc("  Try: B 1, B 2, etc.", "error"))
        else:
            print(tc("  Unknown command. Try B <number> or DONE.", "error"))
```

---

## CHANGE 3: Tavern Character Display

### LOCATION: Find where character stats are shown in the tavern

Likely in a function that displays character sheet or in the main game loop display.

**FROM:** Shows character class and mana
```
Fighter — Melee combat bonus
Mana: 20/20
```

**TO:** Show only stats and proficiencies (via `character.stat_summary()`)

The `character.stat_summary()` method in character_NEW.py already does this! Just call:
```python
print(character.stat_summary())
```

No custom display code needed in tavern.py.

---

## CHANGE 4: Update TAVERN_COMMANDS (command_parser.py)

### Add spell shop commands if not already present:

In `TAVERN_COMMANDS`, ensure these exist:
```python
    "wizard": {"aliases": ["aldric", "magic"], "min_chars": 1, "category": "shop"},
    "spell": {"aliases": ["learn"], "min_chars": 3, "category": "shop"},
```

These allow:
- `WIZARD` or `ALDRIC` to access the shop
- `SPELL` to show current proficiencies

---

## CHANGE 5: Ensure Aldric is Accessible

### In tavern.py initialization (world setup):

Verify Aldric is placed in the Back Room as a friendly NPC.

If not already in world definition, add to tavern world/rooms:
```
Room: Back Room (east of Bar)
NPC: Aldric the Wizard (friendly, offers spell shop)
```

---

## TESTING CHECKLIST FOR TAVERN

- [ ] Create new character: No class selection screen
- [ ] Character starts with 200 gold
- [ ] Go to Back Room (EAST from Bar)
- [ ] Talk to Aldric (WIZARD / ALDRIC command)
- [ ] Spell shop shows all 4 spells
- [ ] Spells show cost if not learned
- [ ] Spells show proficiency if learned
- [ ] B 1 to learn Blast (costs 3000)
  - [ ] Gold decreases
  - [ ] Proficiency shows as 25-75%
- [ ] B 1 again: "Already know Blast" error
- [ ] Insufficient gold: "Need 1000 gold" error
- [ ] Learn another spell
- [ ] Character sheet (CHARACTER command) shows all proficiencies
- [ ] Exit adventure, return to tavern
- [ ] Spell proficiencies persist

---

## CODE LOCATIONS IN CURRENT TAVERN.PY

Search for these patterns to find what to modify:

1. **Aldric NPC definition:** Search for `"aldric"` or `"Aldric"`
2. **Shop functions:** Search for `shop_` or `_shop_aldric`
3. **Character creation:** Already in character.py, not tavern.py
4. **Display character:** Search for `character.stat_summary()` or similar display code

---

## FILES THAT HANDLE TAVERN

1. **tavern.py** - Main tavern code
2. **character.py** - Character creation (already updated in character_NEW.py)
3. **command_parser.py** - Commands (update per command_parser_UPDATES.py)
4. **player.py** - Runtime state (already updated in player_NEW.py)

---

## SUMMARY OF ALL TAVERN CHANGES

| Component | Change | Lines |
|-----------|--------|-------|
| Character creation | Remove class selection | -55 |
| Character creation | Remove spell selection | -25 |
| Aldric shop | Add spell learning UI | +60 |
| Character display | Use stat_summary() | 0 (no change, already done) |
| Final message | Update to mention spell learning | +1 |

**Total net change:** ~20 lines (more added for spell shop than removed)

---

## NEXT STEPS

1. Apply these changes to tavern.py
2. Verify character creation flow
3. Test Aldric spell shop
4. Ensure proficiencies sync to player during adventure
5. Ensure proficiencies persist when returning to tavern
