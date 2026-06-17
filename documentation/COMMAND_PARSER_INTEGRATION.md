# Command Parser Integration Guide

## Overview

The `command_parser.py` module provides fuzzy command matching for both engine.py and tavern.py.

**Features:**
- Case-insensitive matching
- Partial command matching (e.g., "nor" → "north")
- Alias support (e.g., "n" → "north")
- Ambiguity detection (e.g., "l" matches both "look" and "load")
- Suggestions for misspelled commands

---

## Usage Examples

### Basic Command Parsing

```python
from command_parser import parse_command

# Exact match
cmd, status, suggestions = parse_command("NORTH", "engine")
# Returns: ("north", "exact", None)

# Partial match
cmd, status, suggestions = parse_command("nor", "engine")
# Returns: ("north", "partial", None)

# Ambiguous match (need 3+ chars)
cmd, status, suggestions = parse_command("l", "engine")
# Returns: (None, "ambiguous", ["look", "load"])

# Not found
cmd, status, suggestions = parse_command("xyz", "engine")
# Returns: (None, "not_found", ["spell", "inventory"])  # suggestions
```

---

## Integration Pattern for Engine.py

### Current Structure
```python
def handle(self, raw_input):
    parts = raw_input.split(maxsplit=1)
    cmd = parts[0].lower()
    noun = parts[1] if len(parts) > 1 else ""
    
    actions = {
        "north": lambda: self.cmd_move("north"),
        "south": lambda: self.cmd_move("south"),
        ...
        "quit": lambda: self.cmd_quit(),
    }
    
    action = actions.get(cmd)
    if action:
        action()
    else:
        print("Unknown command")
```

### New Structure with Parser

```python
from command_parser import parse_command

def handle(self, raw_input):
    # Parse command with fuzzy matching
    cmd, status, suggestions = parse_command(raw_input, "engine")
    
    # Extract noun if present
    parts = raw_input.split(maxsplit=1)
    noun = parts[1] if len(parts) > 1 else ""
    
    # Handle parsing results
    if status == "exact" or status == "partial":
        # Valid command found
        self._execute_command(cmd, noun)
    
    elif status == "ambiguous":
        # Multiple matches - ask user to be more specific
        print(f"Ambiguous command. Did you mean one of these?")
        for suggestion in suggestions:
            print(f"  • {suggestion.upper()}")
        print("\nPlease use at least 3 letters or use full command name.")
    
    elif status == "not_found":
        print(f"Unknown command: '{raw_input}'")
        if suggestions:
            print(f"Did you mean: {', '.join(s.upper() for s in suggestions)}?")
        print("Type HELP for a list of commands.")
    
    elif status == "empty":
        print("Please enter a command.")


def _execute_command(self, cmd, noun):
    """Execute a parsed command."""
    actions = {
        "north": lambda: self.cmd_move("north"),
        "south": lambda: self.cmd_move("south"),
        "east": lambda: self.cmd_move("east"),
        "west": lambda: self.cmd_move("west"),
        "go": lambda: self.cmd_move(noun),
        "look": lambda: self.describe_room(),
        "examine": lambda: self.cmd_examine(noun),
        "read": lambda: self.cmd_read(noun),
        "talk": lambda: self.cmd_talk(noun),
        "inventory": lambda: self.cmd_inventory(),
        "get": lambda: self.cmd_get(noun),
        "drop": lambda: self.cmd_drop(noun),
        "open": lambda: self.cmd_open(noun),
        "close": lambda: self.cmd_close(noun),
        "equip": lambda: self.cmd_equip(noun),
        "unequip": lambda: self.cmd_unequip(noun),
        "equipment": lambda: self.cmd_equipment(),
        "attack": lambda: self.cmd_attack(noun),
        "flee": lambda: self.cmd_flee(),
        "cast": lambda: self.cmd_cast(noun),
        "health": lambda: self.cmd_health(),
        "rest": lambda: self.cmd_rest(),
        "spells": lambda: self.cmd_spellbook(),
        "eat": lambda: self.cmd_eat(noun),
        "drink": lambda: self.cmd_drink(noun),
        "unlock": lambda: self.cmd_unlock(noun),
        "save": lambda: self.cmd_save(noun),
        "load": lambda: self.cmd_load(noun),
        "help": lambda: self.cmd_help(),
        "quit": lambda: self.cmd_quit_with_confirm(),
    }
    
    action = actions.get(cmd)
    if action:
        action()
    else:
        print(f"Command not implemented: {cmd}")
```

---

## Improved QUIT Command for Engine

```python
def cmd_quit_with_confirm(self):
    """Quit to tavern with confirmation and optional save."""
    print()
    print("You are about to return to the tavern.")
    
    # Check if there are unsaved changes
    has_changes = True  # You'd detect this based on game state
    
    if has_changes:
        print()
        print("Would you like to:")
        print("  1. Save and return to tavern")
        print("  2. Return to tavern without saving")
        print("  3. Continue adventure")
        print()
        choice = input("Choice (1-3): ").strip()
        
        if choice == "1":
            self.cmd_save("")  # Save to current slot
            print()
            print("Game saved. Returning to tavern...")
            sys.exit(0)  # Return to tavern
        elif choice == "2":
            print("Returning to tavern without saving...")
            sys.exit(0)
        elif choice == "3":
            print("Continuing adventure...")
            return
        else:
            print("Invalid choice. Continuing adventure...")
            return
    else:
        print()
        response = input("Are you sure? (yes/no): ").strip().lower()
        if response in ["yes", "y"]:
            print("Returning to tavern...")
            sys.exit(0)
        else:
            print("Continuing adventure...")
            return
```

---

## Integration Pattern for Tavern.py

Similar approach:

```python
from command_parser import parse_command

def handle_tavern_input(self, raw_input):
    """Handle tavern commands with fuzzy matching."""
    cmd, status, suggestions = parse_command(raw_input, "tavern")
    
    parts = raw_input.split(maxsplit=1)
    noun = parts[1] if len(parts) > 1 else ""
    
    if status in ["exact", "partial"]:
        self._execute_tavern_command(cmd, noun)
    elif status == "ambiguous":
        print(f"Ambiguous: {', '.join(s.upper() for s in suggestions)}")
    elif status == "not_found":
        print(f"Unknown command. Type HELP for options.")
    elif status == "empty":
        pass  # Just show prompt again
```

---

## Key Benefits

✅ **User-Friendly**
- "N" works for "NORTH"
- "NOR" works for "NORTH"
- Case-insensitive
- Helpful suggestions for typos

✅ **Consistent**
- Same behavior in both tavern and engine
- Easy to maintain command list

✅ **Flexible**
- Easy to add new commands
- Easy to add aliases
- Configurable minimum character requirements

✅ **Safe**
- Detects ambiguity
- Prevents wrong command execution
- Clear error messages

---

## Next Steps

1. Copy `command_parser.py` to project root
2. Update `engine.py` to use `parse_command()` in `handle()`
3. Update `tavern.py` to use `parse_command()` in command handling
4. Replace `cmd_quit()` with `cmd_quit_with_confirm()`
5. Test with various inputs: "N", "nor", "NORTH", "l", etc.

---

## Testing Examples

```bash
# In game:
> N           # Works → NORTH
> nor         # Works → NORTH  
> north       # Works → NORTH
> NORTH       # Works → NORTH
> l           # Error → Ambiguous (LOOK or LOAD)
> loo         # Works → LOOK
> loa         # Works → LOAD
> xyz         # Error → Not found (maybe did you mean SPELLS?)
> quit        # Shows save confirmation
> sav         # Works → SAVE
```
