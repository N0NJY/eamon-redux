"""
core/data_validator.py - Validate character, world, and save file integrity.
Detects corruption and repairs common issues.
"""

import json
from typing import Tuple, List, Dict, Any


class ValidationError(Exception):
    """Raised when data validation fails and can't auto-repair."""
    pass


class CharacterValidator:
    """Validate and repair character data."""

    REQUIRED_FIELDS = [
        "name", "hardiness", "agility", "charisma", "intelligence", "strength",
        "hp", "gold", "spell_proficiencies", "weapon_proficiencies",
        "xp", "level", "is_beginner", "adventures_completed", "equipped"
    ]

    STAT_BOUNDS = {
        "hardiness":    (3, 18),
        "agility":      (3, 18),
        "charisma":     (3, 18),
        "intelligence": (3, 18),
        "strength":     (3, 18),
    }

    @staticmethod
    def validate(char_dict: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Validate character dict. Returns (is_valid, error_list, repaired_dict).

        Args:
            char_dict: Character data dictionary

        Returns:
            (is_valid, [errors], repaired_dict)
            - is_valid: True if no critical issues
            - errors: List of issues found and fixed
            - repaired_dict: Corrected character data
        """
        repairs = []
        char = dict(char_dict)  # Copy to avoid mutating original

        # ── Missing required fields ──────────────────────────────────────────
        for field in CharacterValidator.REQUIRED_FIELDS:
            if field not in char:
                repairs.append(f"Missing field '{field}' — using default")
                char[field] = CharacterValidator._default_value(field)

        # ── Stat bounds checking ─────────────────────────────────────────────
        for stat, (min_val, max_val) in CharacterValidator.STAT_BOUNDS.items():
            if stat in char:
                try:
                    val = int(char[stat])
                    if val < min_val:
                        repairs.append(f"Stat {stat} was {val} (below {min_val}) — set to {min_val}")
                        char[stat] = min_val
                    elif val > max_val:
                        repairs.append(f"Stat {stat} was {val} (above {max_val}) — set to {max_val}")
                        char[stat] = max_val
                except (ValueError, TypeError):
                    repairs.append(f"Stat {stat} was non-numeric — reset to 10")
                    char[stat] = 10

        # ── HP validation ────────────────────────────────────────────────────
        if "hp" in char and "hardiness" in char:
            hp_max = int(char.get("hardiness", 10)) * 2
            try:
                hp = int(char["hp"])
                if hp > hp_max:
                    repairs.append(f"HP ({hp}) exceeds max ({hp_max}) — capped")
                    char["hp"] = hp_max
                elif hp < 0:
                    repairs.append(f"HP was negative — set to 0")
                    char["hp"] = 0
            except (ValueError, TypeError):
                repairs.append(f"HP was non-numeric — reset to max")
                char["hp"] = hp_max

        # ── Gold validation ──────────────────────────────────────────────────
        if "gold" in char:
            try:
                gold = int(char["gold"])
                if gold < 0:
                    repairs.append(f"Gold was negative ({gold}) — set to 0")
                    char["gold"] = 0
                elif gold > 999999:
                    repairs.append(f"Gold was excessive ({gold}) — capped at 999999")
                    char["gold"] = 999999
            except (ValueError, TypeError):
                repairs.append(f"Gold was non-numeric — reset to 0")
                char["gold"] = 0

        # ── Spell proficiencies validation ───────────────────────────────────
        if "spell_proficiencies" in char:
            spell_profs = char["spell_proficiencies"]
            if not isinstance(spell_profs, dict):
                repairs.append("spell_proficiencies was not a dict — reset")
                char["spell_proficiencies"] = {
                    "blast": None, "heal": None, "speed": None, "power": None
                }
            else:
                for spell_key in spell_profs:
                    prof = spell_profs[spell_key]
                    if prof is not None:
                        try:
                            prof_int = int(prof)
                            if prof_int < 0 or prof_int > 100:
                                repairs.append(f"Spell {spell_key} proficiency was {prof_int} — clamped to 0–100")
                                spell_profs[spell_key] = max(0, min(100, prof_int))
                        except (ValueError, TypeError):
                            repairs.append(f"Spell {spell_key} proficiency was non-numeric — reset to None")
                            spell_profs[spell_key] = None

        # ── Weapon proficiencies validation ──────────────────────────────────
        if "weapon_proficiencies" in char:
            wpn_profs = char["weapon_proficiencies"]
            if not isinstance(wpn_profs, dict):
                repairs.append("weapon_proficiencies was not a dict — reset")
                char["weapon_proficiencies"] = {
                    "unarmed": 0, "axe": 5, "bow": -10, "club": 20, "spear": 10, "sword": 0
                }
            else:
                for wpn_key in wpn_profs:
                    prof = wpn_profs[wpn_key]
                    try:
                        prof_int = int(prof)
                        if prof_int < -50 or prof_int > 100:
                            repairs.append(f"Weapon {wpn_key} proficiency was {prof_int} — clamped to -50–100")
                            wpn_profs[wpn_key] = max(-50, min(100, prof_int))
                    except (ValueError, TypeError):
                        repairs.append(f"Weapon {wpn_key} proficiency was non-numeric — reset to 0")
                        wpn_profs[wpn_key] = 0

        # ── Level/XP consistency ─────────────────────────────────────────────
        if "level" in char and "xp" in char:
            try:
                level = int(char.get("level", 1))
                xp = int(char.get("xp", 0))
                if level < 1:
                    repairs.append("Level was < 1 — set to 1")
                    char["level"] = 1
                if xp < 0:
                    repairs.append("XP was negative — set to 0")
                    char["xp"] = 0
            except (ValueError, TypeError):
                repairs.append("Level/XP were non-numeric — reset")
                char["level"] = 1
                char["xp"] = 0

        is_valid = len(repairs) == 0
        return is_valid, repairs, char

    @staticmethod
    def _default_value(field: str) -> Any:
        """Return safe default for a missing field."""
        defaults = {
            "name":                 "Adventurer",
            "hardiness":            10,
            "agility":              10,
            "charisma":             10,
            "intelligence":         10,
            "strength":             10,
            "hp":                   20,
            "gold":                 200,
            "spell_proficiencies":  {"blast": None, "heal": None, "speed": None, "power": None},
            "weapon_proficiencies": {"unarmed": 0, "axe": 5, "bow": -10, "club": 20, "spear": 10, "sword": 0},
            "xp":                   0,
            "level":                1,
            "is_beginner":          True,
            "adventures_completed": [],
            "equipped":             {},
            "bank_balance":         0,
            "marie_attitude":       0,
        }
        return defaults.get(field)


class WorldValidator:
    """Validate world/adventure data integrity."""

    @staticmethod
    def validate_room(room_id: int, room: Dict[str, Any], all_rooms: Dict) -> Tuple[bool, List[str]]:
        """
        Validate a single room.

        Returns: (is_valid, [errors])
        """
        errors = []

        # Check exit references
        if "exits" in room and isinstance(room["exits"], dict):
            for direction, dest_id in room["exits"].items():
                if dest_id != "EXIT_TAVERN" and dest_id not in all_rooms:
                    errors.append(f"Room {room_id}: exit '{direction}' → nonexistent room {dest_id}")

        # Check locked exits reference valid keys
        if "locked_exits" in room and isinstance(room["locked_exits"], dict):
            for direction, key_id in room["locked_exits"].items():
                # Note: artifacts may not exist yet, so skip validation for now
                pass

        return len(errors) == 0, errors

    @staticmethod
    def validate_monster(
        monster_id: int,
        monster: Dict[str, Any],
        all_monsters: Dict,
        all_rooms: Dict
    ) -> Tuple[bool, List[str]]:
        """
        Validate a single monster.

        Returns: (is_valid, [errors])
        """
        errors = []

        # Check room exists
        room_id = monster.get("room_id")
        if room_id and room_id not in all_rooms:
            errors.append(f"Monster {monster_id}: in nonexistent room {room_id}")

        # Check HP bounds
        hp = monster.get("hp", 0)
        hp_max = monster.get("hp_max", 10)
        if hp < 0 or hp > hp_max:
            errors.append(f"Monster {monster_id}: HP {hp} invalid (max {hp_max})")

        return len(errors) == 0, errors


class SaveFileValidator:
    """Validate save file integrity."""

    @staticmethod
    def validate(save_data: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Validate a save file.

        Returns: (is_valid, [errors], repaired_data)
        """
        errors = []
        data = dict(save_data)

        # Check top-level structure
        if "player" not in data:
            errors.append("Missing 'player' section in save file")
            data["player"] = {}

        if "world" not in data:
            errors.append("Missing 'world' section in save file")
            data["world"] = {}

        # Validate player state
        player_state = data.get("player", {})
        if "room_id" in player_state:
            if not isinstance(player_state["room_id"], (int, str)):
                errors.append("player.room_id is invalid type")
                player_state["room_id"] = 1

        if "hp" in player_state:
            try:
                hp = int(player_state["hp"])
                if hp < 0:
                    errors.append(f"player.hp was negative ({hp}) — reset to 0")
                    player_state["hp"] = 0
            except (ValueError, TypeError):
                errors.append("player.hp was non-numeric — reset")
                player_state["hp"] = 10

        # Validate world state
        world_state = data.get("world", {})
        # (More complex checks as needed)

        is_valid = len(errors) == 0
        return is_valid, errors, data
