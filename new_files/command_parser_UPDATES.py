"""
COMMAND_PARSER_UPDATES.py - Changes needed to command_parser.py

Just copy this into the ENGINE_COMMANDS dict where indicated.
These are ALIASES for the existing CAST command and SPELLS command.
"""

# ADD THESE LINES to the ENGINE_COMMANDS dict in command_parser.py
# Insert into the "# Combat" section (around line 30):

"""
    # Magic Casting (aliases for 'cast')
    "blast":  {"aliases": ["b"], "min_chars": 3, "category": "magic"},    # NEW
    "heal":   {"aliases": ["h"], "min_chars": 3, "category": "magic"},    # NEW  
    "speed":  {"aliases": ["sp"], "min_chars": 3, "category": "magic"},   # NEW
    "power":  {"aliases": ["pw"], "min_chars": 3, "category": "magic"},   # NEW
"""

# ============================================================================
# UPDATED ENGINE_COMMANDS (COMPLETE)
# ============================================================================

UPDATED_ENGINE_COMMANDS = {
    # Movement (allow 1 char for cardinal directions)
    "north": {"aliases": ["n"], "min_chars": 1, "category": "movement"},
    "south": {"aliases": ["s"], "min_chars": 1, "category": "movement"},
    "east": {"aliases": ["e"], "min_chars": 1, "category": "movement"},
    "west": {"aliases": ["w"], "min_chars": 1, "category": "movement"},
    "up": {"aliases": ["u"], "min_chars": 1, "category": "movement"},
    "down": {"aliases": ["d"], "min_chars": 1, "category": "movement"},
    "go": {"aliases": [], "min_chars": 2, "category": "movement"},
    
    # Examination & Interaction
    "look": {"aliases": ["l"], "min_chars": 1, "category": "examine"},
    "examine": {"aliases": ["x", "exa"], "min_chars": 1, "category": "examine"},
    "read": {"aliases": [], "min_chars": 3, "category": "examine"},
    "talk": {"aliases": [], "min_chars": 3, "category": "interact"},
    
    # Inventory
    "inventory": {"aliases": ["i", "inv"], "min_chars": 1, "category": "inventory"},
    "get": {"aliases": [], "min_chars": 2, "category": "inventory"},
    "getall": {"aliases": ["get all"], "min_chars": 2, "category": "inventory"},
    "drop": {"aliases": [], "min_chars": 3, "category": "inventory"},
    "open": {"aliases": [], "min_chars": 3, "category": "inventory"},
    "close": {"aliases": [], "min_chars": 3, "category": "inventory"},
    
    # Equipment
    "equip": {"aliases": ["wear", "wield"], "min_chars": 2, "category": "equipment"},
    "unequip": {"aliases": ["remove"], "min_chars": 3, "category": "equipment"},
    "equipment": {"aliases": ["eq"], "min_chars": 2, "category": "equipment"},
    
    # Combat
    "attack": {"aliases": ["kill", "hit", "fight", "stab"], "min_chars": 2, "category": "combat"},
    "flee": {"aliases": [], "min_chars": 3, "category": "combat"},
    
    # Magic (NEW spells)
    "cast": {"aliases": [], "min_chars": 3, "category": "magic"},
    "blast": {"aliases": ["b"], "min_chars": 3, "category": "magic"},
    "heal": {"aliases": ["h"], "min_chars": 3, "category": "magic"},
    "speed": {"aliases": ["sp"], "min_chars": 3, "category": "magic"},
    "power": {"aliases": ["pw"], "min_chars": 3, "category": "magic"},
    
    # Status
    "health": {"aliases": ["hp"], "min_chars": 1, "category": "status"},
    "rest": {"aliases": [], "min_chars": 3, "category": "status"},
    "spells": {"aliases": ["spell"], "min_chars": 3, "category": "status"},
    
    # Items
    "eat": {"aliases": [], "min_chars": 2, "category": "items"},
    "drink": {"aliases": [], "min_chars": 3, "category": "items"},
    "unlock": {"aliases": [], "min_chars": 3, "category": "items"},
    
    # Game Control
    "save": {"aliases": [], "min_chars": 2, "category": "control"},
    "load": {"aliases": [], "min_chars": 2, "category": "control"},
    "help": {"aliases": ["h", "?"], "min_chars": 1, "category": "control"},
    "quit": {"aliases": ["q", "exit", "bye"], "min_chars": 1, "category": "control"},
}

# ============================================================================
# TAVERN_COMMANDS - NO CHANGES NEEDED
# ============================================================================
# Keep TAVERN_COMMANDS exactly as is. Only ENGINE_COMMANDS changes.

# ============================================================================
# IMPLEMENTATION NOTES
# ============================================================================
"""
1. Replace the ENGINE_COMMANDS dict in command_parser.py with UPDATED_ENGINE_COMMANDS above

2. The new spell commands map to existing CAST logic in engine.py:
   - User types: BLAST arg
   - Parser returns: ("blast", "exact", None)
   - Engine calls: cmd_blast(args) which internally calls _attempt_cast("blast", args)

3. These are NOT separate commands - they just parse to spell names
   The engine.py needs to handle:
   - cmd_cast(args) → main CAST command
   - cmd_blast(args) → alias for CAST BLAST
   - cmd_heal(args) → alias for CAST HEAL
   - cmd_speed(args) → alias for CAST SPEED
   - cmd_power(args) → alias for CAST POWER

4. Existing commands that DON'T change:
   - "cast" still exists as the formal command
   - "spells" still shows spell list
   - All other commands unchanged

5. Help text can be updated to mention:
   BLAST, HEAL, SPEED, POWER are shortcuts for CAST SPELL_NAME
"""
