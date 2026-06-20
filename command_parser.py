"""
Command Parser for Eamon Redux
Handles fuzzy matching, aliases, and partial command matching.
Supports case-insensitive matching with minimum character requirements.
"""

from typing import Tuple, Optional, List

# ============================================================================
# ENGINE COMMANDS
# ============================================================================

ENGINE_COMMANDS = {
    # Movement — cardinal
    "north":      {"aliases": ["n"],                               "min_chars": 1, "category": "movement"},
    "south":      {"aliases": ["s"],                               "min_chars": 1, "category": "movement"},
    "east":       {"aliases": ["e"],                               "min_chars": 1, "category": "movement"},
    "west":       {"aliases": ["w"],                               "min_chars": 1, "category": "movement"},
    "up":         {"aliases": ["u"],                               "min_chars": 1, "category": "movement"},
    "down":       {"aliases": ["d"],                               "min_chars": 1, "category": "movement"},
    # Movement — diagonal
    "northeast":  {"aliases": ["ne"],                              "min_chars": 2, "category": "movement"},
    "northwest":  {"aliases": ["nw"],                              "min_chars": 2, "category": "movement"},
    "southeast":  {"aliases": ["se"],                              "min_chars": 2, "category": "movement"},
    "southwest":  {"aliases": ["sw"],                              "min_chars": 2, "category": "movement"},
    "go":         {"aliases": ["g"],                               "min_chars": 1, "category": "movement"},
    # Flee — also accepts "run" and "escape"
    "flee":       {"aliases": ["fl", "run", "escape"],             "min_chars": 2, "category": "movement"},

    # Examination & Interaction
    "look":       {"aliases": ["l"],                               "min_chars": 1, "category": "examine"},
    "examine":    {"aliases": ["x", "ex", "exa"],                  "min_chars": 2, "category": "examine"},
    "read":       {"aliases": ["rea"],                             "min_chars": 3, "category": "examine"},
    # talk/ask/request all address an NPC
    "talk":       {"aliases": ["ta", "ask", "request"],            "min_chars": 2, "category": "interact"},
    # say broadcasts to the room (no target required)
    "say":        {"aliases": ["yell", "shout"],                   "min_chars": 3, "category": "interact"},
    "smile":      {"aliases": ["grin", "wave", "bow"],             "min_chars": 4, "category": "interact"},
    "free":       {"aliases": ["release"],                         "min_chars": 4, "category": "interact"},

    # Inventory
    "inventory":  {"aliases": ["i", "inv", "in"],                  "min_chars": 1, "category": "inventory"},
    "get":        {"aliases": ["ge", "take", "pick"],              "min_chars": 2, "category": "inventory"},
    "getall":     {"aliases": ["ga"],                              "min_chars": 2, "category": "inventory"},
    "drop":       {"aliases": ["dr", "place"],                     "min_chars": 2, "category": "inventory"},
    "put":        {"aliases": ["pu"],                              "min_chars": 2, "category": "inventory"},
    "give":       {"aliases": ["gi"],                              "min_chars": 2, "category": "inventory"},
    "open":       {"aliases": ["op"],                              "min_chars": 2, "category": "inventory"},
    "close":      {"aliases": ["cl"],                              "min_chars": 2, "category": "inventory"},
    "use":        {"aliases": ["us"],                              "min_chars": 2, "category": "inventory"},
    "light":      {"aliases": ["ignite"],                          "min_chars": 3, "category": "inventory"},

    # Equipment — "ready" is classic Eamon synonym for equip
    "equip":      {"aliases": ["wear", "wield", "eq", "ready", "wea"], "min_chars": 2, "category": "equipment"},
    "unequip":    {"aliases": ["remove", "un", "doff"],            "min_chars": 2, "category": "equipment"},
    "equipment":  {"aliases": ["equ"],                             "min_chars": 3, "category": "equipment"},

    # Combat
    "attack":     {"aliases": ["kill", "fight", "hit", "att", "a"], "min_chars": 1, "category": "combat"},
    "cast":       {"aliases": ["ca"],                              "min_chars": 2, "category": "combat"},
    # Standalone spell shortcuts — bypass "cast" prefix
    "blast":      {"aliases": ["bla"],                             "min_chars": 3, "category": "combat"},
    "heal":       {"aliases": ["hea"],                             "min_chars": 3, "category": "combat"},
    "speed":      {"aliases": ["spee"],                            "min_chars": 4, "category": "combat"},
    "power":      {"aliases": ["pow"],                             "min_chars": 3, "category": "combat"},

    # Status
    "character":  {"aliases": ["char", "ch", "status", "sheet", "v", "cha"], "min_chars": 2, "category": "status"},
    "health":     {"aliases": ["hp"],                              "min_chars": 1, "category": "status"},
    "rest":       {"aliases": ["res"],                             "min_chars": 3, "category": "status"},
    "spells":     {"aliases": ["spell", "sp"],                     "min_chars": 2, "category": "status"},

    # Item use
    "eat":        {"aliases": ["ea"],                              "min_chars": 2, "category": "items"},
    "drink":      {"aliases": ["dri"],                             "min_chars": 3, "category": "items"},
    "unlock":     {"aliases": ["ul"],                              "min_chars": 2, "category": "items"},

    # Game Control
    "save":       {"aliases": ["sa"],                              "min_chars": 2, "category": "control"},
    "load":       {"aliases": ["lo", "restore"],                   "min_chars": 2, "category": "control"},
    "help":       {"aliases": ["h", "?"],                          "min_chars": 1, "category": "control"},
    "quit":       {"aliases": ["q", "exit", "bye"],                "min_chars": 1, "category": "control"},

    # Special (adventure-specific hook — falls through to call_hook)
    "trollsfire": {"aliases": ["tf"],                              "min_chars": 4, "category": "special"},
}

# ============================================================================
# TAVERN COMMANDS
# ============================================================================

TAVERN_COMMANDS = {
    # Navigation
    "north":     {"aliases": ["n"],                                   "min_chars": 1, "category": "navigation"},
    "south":     {"aliases": ["s"],                                   "min_chars": 1, "category": "navigation"},
    "east":      {"aliases": ["e"],                                   "min_chars": 1, "category": "navigation"},
    "west":      {"aliases": ["w"],                                   "min_chars": 1, "category": "navigation"},
    "northeast": {"aliases": ["ne"],                                  "min_chars": 2, "category": "navigation"},
    "northwest": {"aliases": ["nw"],                                  "min_chars": 2, "category": "navigation"},
    "southeast": {"aliases": ["se"],                                  "min_chars": 2, "category": "navigation"},
    "southwest": {"aliases": ["sw"],                                  "min_chars": 2, "category": "navigation"},
    "go":        {"aliases": ["g"],                                   "min_chars": 1, "category": "navigation"},

    # Character Management
    "character": {"aliases": ["sheet", "char", "ch", "cha", "v", "status"], "min_chars": 2, "category": "character"},
    "inventory": {"aliases": ["i", "inv", "in"],                     "min_chars": 1, "category": "character"},
    "spells":    {"aliases": ["spell", "sp"],                        "min_chars": 2, "category": "character"},
    "equipment": {"aliases": ["eq", "equ"],                          "min_chars": 2, "category": "character"},
    "equip":     {"aliases": ["wear", "wield", "ready", "wea"],      "min_chars": 2, "category": "character"},
    "unequip":   {"aliases": ["remove", "un", "doff"],               "min_chars": 2, "category": "character"},

    # Main Hall Actions
    "look":      {"aliases": ["l"],                                   "min_chars": 1, "category": "explore"},
    "talk":      {"aliases": ["ta"],                                  "min_chars": 2, "category": "explore"},
    "give":      {"aliases": ["gi"],                                  "min_chars": 2, "category": "explore"},
    "buy":       {"aliases": ["b"],                                   "min_chars": 1, "category": "shop"},
    "sell":      {"aliases": [],                                      "min_chars": 4, "category": "shop"},
    "marcus":    {"aliases": ["cavielli", "shop", "ma"],             "min_chars": 2, "category": "shop"},
    "wizard":    {"aliases": ["aldric", "magic", "wiz", "mage"],    "min_chars": 3, "category": "shop"},
    "marie":     {"aliases": ["witch", "laveau"],                    "min_chars": 3, "category": "shop"},

    # Bank
    "bank":      {"aliases": ["ba"],                                  "min_chars": 2, "category": "bank"},
    "deposit":   {"aliases": ["dep"],                                 "min_chars": 3, "category": "bank"},
    "withdraw":  {"aliases": ["with", "wd"],                         "min_chars": 4, "category": "bank"},
    "balance":   {"aliases": ["bal"],                                 "min_chars": 3, "category": "bank"},

    # Adventures
    "adventure": {"aliases": ["a", "adv", "ad"],                     "min_chars": 1, "category": "adventure"},
    "resume":    {"aliases": ["r", "load", "res"],                   "min_chars": 1, "category": "adventure"},
    "new":       {"aliases": ["ne"],                                  "min_chars": 2, "category": "character"},

    # Game Control
    "save":      {"aliases": ["sa"],                                  "min_chars": 2, "category": "control"},
    "leave":     {"aliases": ["le", "exit", "bye", "outside"],       "min_chars": 2, "category": "control"},
    "help":      {"aliases": ["h", "?"],                              "min_chars": 1, "category": "control"},
    "quit":      {"aliases": ["q"],                                   "min_chars": 1, "category": "control"},
}


def parse_command(raw_input: str, context: str = "engine") -> Tuple[Optional[str], str, Optional[List[str]]]:
    """
    Parse user input and match to a valid command.
    
    Args:
        raw_input: Raw user input (e.g., "nor", "NORTH", "N")
        context: "engine" or "tavern"
    
    Returns:
        Tuple of (matched_command, status, suggestions)
        - matched_command: The canonical command name, or None
        - status: "exact", "partial", "ambiguous", "not_found"
        - suggestions: List of possible commands if ambiguous/not_found
    
    Examples:
        parse_command("N", "engine") → ("north", "exact", None)
        parse_command("nor", "engine") → ("north", "partial", None)
        parse_command("l", "engine") → ("look", "exact", None)
        parse_command("xyz", "engine") → (None, "not_found", None)
    """
    
    # Get the command set for this context
    commands = ENGINE_COMMANDS if context == "engine" else TAVERN_COMMANDS
    
    # Normalize input
    raw_input = raw_input.strip().lower()
    
    if not raw_input:
        return (None, "empty", None)
    
    # Extract just the command part (before space)
    cmd_input = raw_input.split()[0]
    
    # ────────────────────────────────────────────────────────────────
    # Try exact match first
    # ────────────────────────────────────────────────────────────────
    if cmd_input in commands:
        return (cmd_input, "exact", None)
    
    # ────────────────────────────────────────────────────────────────
    # Try alias match
    # ────────────────────────────────────────────────────────────────
    for cmd_name, cmd_info in commands.items():
        if cmd_input in cmd_info["aliases"]:
            return (cmd_name, "exact", None)
    
    # ────────────────────────────────────────────────────────────────
    # Try partial match (at least min_chars)
    # ────────────────────────────────────────────────────────────────
    matches = []
    
    for cmd_name, cmd_info in commands.items():
        min_chars = cmd_info["min_chars"]
        
        # Check if input matches start of command
        if len(cmd_input) >= min_chars and cmd_name.startswith(cmd_input):
            matches.append(cmd_name)
        
        # Check if input matches start of any alias
        for alias in cmd_info["aliases"]:
            if len(cmd_input) >= min_chars and alias.startswith(cmd_input):
                if cmd_name not in matches:
                    matches.append(cmd_name)
    
    if len(matches) == 1:
        return (matches[0], "partial", None)
    elif len(matches) > 1:
        return (None, "ambiguous", matches)
    
    # ────────────────────────────────────────────────────────────────
    # No match found
    # ────────────────────────────────────────────────────────────────
    # Find close matches for suggestions
    suggestions = []
    for cmd_name in commands.keys():
        if cmd_name.startswith(cmd_input[:2]) or cmd_input in cmd_name:
            suggestions.append(cmd_name)
    
    return (None, "not_found", suggestions if suggestions else None)


def get_command_help(cmd_name: str, context: str = "engine") -> Optional[str]:
    """Get help text for a specific command."""
    commands = ENGINE_COMMANDS if context == "engine" else TAVERN_COMMANDS
    
    if cmd_name in commands:
        aliases = commands[cmd_name]["aliases"]
        alias_str = f" ({', '.join(aliases)})" if aliases else ""
        return f"{cmd_name.upper()}{alias_str}"
    
    return None


def get_all_commands(context: str = "engine") -> dict:
    """Get all commands for a context, organized by category."""
    commands = ENGINE_COMMANDS if context == "engine" else TAVERN_COMMANDS
    
    organized = {}
    for cmd_name, cmd_info in commands.items():
        cat = cmd_info["category"]
        if cat not in organized:
            organized[cat] = []
        organized[cat].append(cmd_name)
    
    return organized
