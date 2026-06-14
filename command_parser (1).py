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
    # Movement (allow 1 char for cardinal directions)
    "north": {"aliases": ["n"], "min_chars": 1, "category": "movement"},
    "south": {"aliases": ["s"], "min_chars": 1, "category": "movement"},
    "east": {"aliases": ["e"], "min_chars": 1, "category": "movement"},
    "west": {"aliases": ["w"], "min_chars": 1, "category": "movement"},
    "go": {"aliases": [], "min_chars": 2, "category": "movement"},
    
    # Examination & Interaction
    "look": {"aliases": ["l"], "min_chars": 1, "category": "examine"},
    "examine": {"aliases": ["x", "exa"], "min_chars": 1, "category": "examine"},
    "read": {"aliases": [], "min_chars": 3, "category": "examine"},
    "talk": {"aliases": [], "min_chars": 3, "category": "interact"},
    
    # Inventory
    "inventory": {"aliases": ["i", "inv"], "min_chars": 1, "category": "inventory"},
    "get": {"aliases": [], "min_chars": 2, "category": "inventory"},
    "drop": {"aliases": [], "min_chars": 3, "category": "inventory"},
    "open": {"aliases": [], "min_chars": 3, "category": "inventory"},
    "close": {"aliases": [], "min_chars": 3, "category": "inventory"},
    
    # Equipment
    "equip": {"aliases": ["wear", "wield"], "min_chars": 2, "category": "equipment"},
    "unequip": {"aliases": ["remove"], "min_chars": 3, "category": "equipment"},
    "equipment": {"aliases": ["eq"], "min_chars": 2, "category": "equipment"},
    
    # Combat
    "attack": {"aliases": ["kill"], "min_chars": 2, "category": "combat"},
    "flee": {"aliases": [], "min_chars": 3, "category": "combat"},
    "cast": {"aliases": [], "min_chars": 3, "category": "combat"},
    
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
# TAVERN COMMANDS
# ============================================================================

TAVERN_COMMANDS = {
    # Navigation
    "north": {"aliases": ["n"], "min_chars": 1, "category": "navigation"},
    "south": {"aliases": ["s"], "min_chars": 1, "category": "navigation"},
    "east": {"aliases": ["e"], "min_chars": 1, "category": "navigation"},
    "west": {"aliases": ["w"], "min_chars": 1, "category": "navigation"},
    
    # Character Management
    "character": {"aliases": ["sheet", "c", "ch"], "min_chars": 1, "category": "character"},
    "inventory": {"aliases": ["i", "inv"], "min_chars": 1, "category": "character"},
    "spells": {"aliases": ["spell"], "min_chars": 3, "category": "character"},
    
    # Tavern Actions
    "look": {"aliases": ["l"], "min_chars": 1, "category": "explore"},
    "talk": {"aliases": [], "min_chars": 3, "category": "explore"},
    "buy": {"aliases": ["b"], "min_chars": 1, "category": "shop"},
    "sell": {"aliases": ["s"], "min_chars": 1, "category": "shop"},
    
    # Adventures
    "adventure": {"aliases": ["a", "adv"], "min_chars": 1, "category": "adventure"},
    "resume": {"aliases": ["r", "load"], "min_chars": 1, "category": "adventure"},
    "new": {"aliases": ["n"], "min_chars": 1, "category": "character"},
    
    # Game Control
    "help": {"aliases": ["h", "?"], "min_chars": 1, "category": "control"},
    "quit": {"aliases": ["q"], "min_chars": 1, "category": "control"},
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
        parse_command("l", "engine") → (None, "ambiguous", ["look", "load"])
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
