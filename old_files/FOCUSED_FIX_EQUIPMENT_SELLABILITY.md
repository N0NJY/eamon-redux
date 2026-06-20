# Equipment Display & Item Sellability Fixes

**Status**: Ready for Claude Code implementation  
**Issues**: Non-sellable items, no equipment display, no tavern equipment management  
**Estimated Time**: 1-2 hours total (3 independent parts)

---

## Part 1: Fix Artifacts.json Corruption

**Problem**: Book (id:9) has corrupted `is_quest_item` flag repeated 9 times, preventing sale.

**Solution**: Use the cleaned artifacts_FIXED.json file.

### Command Structure 1

```
PART 1: FIX ARTIFACTS JSON CORRUPTION

Problem:
- adventures/beginners_cave/artifacts.json has book (id:9) with 
  "is_quest_item": true repeated 9 times
- This breaks JSON parsing and prevents item from being sellable

Solution:
Replace artifacts.json with the cleaned artifacts_FIXED.json

Steps:
1. View adventures/beginners_cave/artifacts_FIXED.json (first 50 lines)
2. Confirm it has clean JSON (no repeated fields)
3. Replace artifacts.json with artifacts_FIXED.json content
4. Verify the book entry is now clean
5. Test: python3 tavern.py, enter adventure, GET bottle, exit, try to sell

Expected result:
- Book entry has no repeated is_quest_item fields
- Bottle, book, sack of coins can all be sold to Horace
- No JSON parsing errors
```

---

## Part 2: Add Equipment Display to Tavern Character Sheet

**Problem**: When viewing character in tavern, equipped items are invisible.

**Solution**: Add equipment section to character sheet display.

### Current State

**tavern.py view_character()** shows stats but NOT equipped items:
```python
print(f" Armor: {player.armor}")
print(f" HP: {player.hp}/{player.hp_max}")
# ... but NO equipped items shown
```

### Code to Add

**In tavern.py, update view_character() method:**

After the stat display section, add this before returning to menu:

```python
        # Show equipped items
        print(f"\n {self.hr('─', 40)}")
        print(f" EQUIPPED ITEMS")
        print(f" {self.hr('─', 40)}")
        
        if player.equipped:
            for slot, item_name in player.equipped.items():
                print(f" {slot.upper()}: {item_name}")
        else:
            print(" (nothing equipped)")
```

### Command Structure 2

```
PART 2: ADD EQUIPMENT DISPLAY TO TAVERN CHARACTER SHEET

Problem:
- tavern.py view_character() shows stats but NOT equipped items
- Player can't see what's equipped without entering adventure

Solution:
Add equipment section to character sheet display in tavern

Repository: ~/git/Eamon/eamon-redux/

Steps:
1. View tavern.py view_character() method (around line 300-350)
2. Find where stat info is printed (armor, hp, etc.)
3. After that section, I'll provide code to add equipment display
4. The code shows all items in player.equipped dict
5. Test: python3 tavern.py, VIEW CHARACTER, verify equipped items show

Expected result:
- Character sheet shows:
  * Stats (level, hp, armor, etc.)
  * EQUIPPED ITEMS section
  * List of equipped items by slot (weapon, armor, etc.)
  * Or "(nothing equipped)" if empty
```

---

## Part 3: Add EQUIPMENT Command to Tavern Menu

**Problem**: No way to manage equipment (view/unequip) without entering adventure.

**Solution**: Add EQUIPMENT command available in tavern main menu.

### Current State

**tavern.py main_menu()** has options like:
- ADVENTURES, CHARACTER, SPELLS, GOLD, etc.
- But NO EQUIPMENT option

### Code to Add

**In tavern.py, add new method:**

```python
def cmd_equipment(self) -> None:
    """Manage character equipment in the tavern."""
    player = self.current_player
    
    print(f"\n EQUIPMENT MANAGEMENT")
    print(f" {self.hr('─', 40)}")
    
    if not player.equipped:
        print(" You have no equipped items.")
        return
    
    print(" Current equipment:")
    for idx, (slot, item_name) in enumerate(player.equipped.items(), 1):
        print(f" {idx}. {slot.upper()}: {item_name}")
    
    print(f"\n {self.hr('─', 40)}")
    choice = input(" Unequip which? (1-{}, or 0 to cancel): ".format(len(player.equipped))).strip()
    
    if choice == "0":
        return
    
    try:
        idx = int(choice) - 1
        slots = list(player.equipped.keys())
        if 0 <= idx < len(slots):
            slot = slots[idx]
            item_name = player.equipped[slot]
            del player.equipped[slot]
            print(f" {item_name} unequipped.")
            self.save_player()
        else:
            print(" Invalid choice.")
    except ValueError:
        print(" Invalid input.")
```

**In tavern.py main_menu(), add to command aliases:**

Find the section with command aliases (around line 450-500) and add:

```python
            elif cmd == "equipment" or cmd == "eq":
                self.cmd_equipment()
```

Also add to the menu display. Find where it prints available commands and add:

```python
print(" equipment (eq) — Manage equipped items")
```

### Command Structure 3

```
PART 3: ADD EQUIPMENT COMMAND TO TAVERN MENU

Problem:
- No way to manage equipment (unequip items) in the tavern
- Equipment can only be managed inside adventure
- Player wants to view/change equipment before choosing adventure

Solution:
Add EQUIPMENT (EQ) command to tavern main menu

Repository: ~/git/Eamon/eamon-redux/

Steps:
1. View tavern.py main_menu() method
2. Find the command dispatch section (where CHARACTER, SPELLS, etc. are handled)
3. I'll provide:
   a) New cmd_equipment() method
   b) Command alias registration (equipment / eq)
   c) Menu help text
4. Test: python3 tavern.py, EQUIPMENT, unequip an item, verify it works

Expected result:
- EQUIPMENT command available in tavern menu
- Shows all equipped items with numbers
- Can unequip by selecting number
- EQ shortcut works
- Changes persist to character file
```

---

## Full Test Sequence

After all 3 parts are implemented:

```bash
# Test 1: Item Sellability
python3 tavern.py
# Create/load Thoran
# Play Beginner's Cave
# Get bottle, book, empty bottle, sack of coins
# Exit adventure
# Try to sell each item to Horace
# Result: All should be sellable

# Test 2: Equipment Display
python3 tavern.py
# Load Thoran (has equipped items from adventure)
# CHARACTER command
# Verify EQUIPPED ITEMS section shows current equipment
# Result: All equipped items visible on character sheet

# Test 3: Equipment Management
python3 tavern.py
# Load Thoran
# EQUIPMENT command
# View current equipment
# Unequip an item
# CHARACTER command
# Verify item is no longer equipped
# Result: Equipment changes persist
```

---

## Claude Code Session Start

```
I'm implementing 3 related fixes for Eamon Redux:
1. Fix corrupted artifacts.json
2. Add equipment display to tavern character sheet
3. Add EQUIPMENT command to tavern menu

FOCUSED FIX: Equipment Display & Item Sellability

Repository: ~/git/Eamon/eamon-redux/

PART 1: Fix artifacts.json
- Book (id:9) has "is_quest_item" repeated 9 times (corrupted)
- Use artifacts_FIXED.json (clean version)
- Replace artifacts.json with fixed version

PART 2: Add equipment display to character sheet
- tavern.py view_character() shows stats but NOT equipped items
- Add equipment section showing what's equipped by slot

PART 3: Add EQUIPMENT command to tavern
- No way to manage equipment in tavern currently
- Add cmd_equipment() method
- Register EQUIPMENT/EQ command in main menu
- Allow unequipping items

All three parts work together for complete equipment management.

Let's start with PART 1: Replace artifacts.json with artifacts_FIXED.json
```

---

## Summary

| Part | What | Time | Status |
|------|------|------|--------|
| 1 | Fix artifacts.json corruption | 5 mins | ✓ Copy file |
| 2 | Equipment display on character sheet | 20 mins | ✓ Add method |
| 3 | Equipment management in tavern | 30 mins | ✓ Add cmd + menu |

**After completion**: Full equipment management + item sellability working ✅
