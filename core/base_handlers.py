"""
base_handlers.py - Generic adventure event handlers

These handlers work for ANY adventure by reading flags from JSON.
Behavior is data-driven, not hardcoded.

Supports:
- NPC recruitment (is_follower flag)
- Item trading (is_tradeable flag)
- Quest completion (quest_condition flag)
- Win conditions (is_win_room flag)
- Event triggers (triggers_event flag)
"""

import random
from typing import Optional, Tuple


class BaseAdventureHandlers:
    """Generic event handlers that read flags to determine behavior."""

    def __init__(self, engine):
        self.engine = engine

    # ──────────────────────────────────────────────────────────────────────────
    # CORE HOOKS
    # ──────────────────────────────────────────────────────────────────────────

    def on_game_start(self) -> None:
        """Called when adventure starts."""
        self.engine.game_data = {}

    def on_enter_room(self, room_id: int) -> None:
        """Called when player enters a room."""
        room = self.engine.world.get_room(room_id)
        if not room:
            return

        flags = room.flags or {}

        if flags.get("is_win_room"):
            if self._check_win_condition(flags.get("win_condition")):
                dialogue = flags.get("win_dialogue", "You have won!")
                print(f"\n{dialogue}")
                self.engine.exit_code = 1
                self.engine.running = False
                return

        if flags.get("triggers_event"):
            self.engine.trigger_event(flags["triggers_event"])

    def on_talk_to_npc(self, npc_name: str) -> None:
        """Called when player talks to an NPC."""
        room = self.engine.world.get_room(self.engine.player.room_id)
        if not room:
            return

        npc = self.engine.world.find_monster_by_name(
            npc_name, self.engine.world.monsters_in_room(room.id)
        )
        if not npc:
            return

        if npc.dialogue:
            print()
            print(self.engine.tc(npc.dialogue, "desc"))
            print()
        else:
            print(self.engine.tc(f"The {npc.name} has nothing to say.", "sys"))

        flags = npc.flags or {}
        if flags.get("is_follower"):
            can_recruit, dialogue = self._check_follower_conditions(npc, flags)
            if can_recruit:
                self.engine.player.followers.append(npc)
                print(self.engine.tc(dialogue, "desc"))
                return

        if npc.heal_amount > 0 and npc.heal_cost > 0:
            self._offer_healing(npc)

    def on_use_item(self, artifact_name: str, target: Optional[str] = None) -> bool:
        """Called when player uses an item. Returns True if handled."""
        room = self.engine.world.get_room(self.engine.player.room_id)
        pool = (self.engine.world.artifacts_in_room(room.id)
                + self.engine.world.artifacts_carried())

        artifact = self.engine.world.find_artifact_by_name(artifact_name, pool)
        if not artifact:
            return False

        flags = artifact.flags or {}

        if flags.get("is_escape_vehicle"):
            dialogue = flags.get("escape_dialogue", "You escape!")
            print(self.engine.tc(dialogue, "spell"))
            self.engine.exit_code = 3
            self.engine.running = False
            return True

        if flags.get("triggers_event"):
            self.engine.trigger_event(flags["triggers_event"])
            return True

        return False

    def on_monster_defeated(self, monster_id: int) -> None:
        """Called when a monster is defeated. Override in adventure handlers."""
        pass

    # ──────────────────────────────────────────────────────────────────────────
    # HELPER METHODS
    # ──────────────────────────────────────────────────────────────────────────

    def _check_follower_conditions(self, npc, flags: dict) -> Tuple[bool, str]:
        """Check if NPC recruitment conditions are met."""
        follower_type = flags.get("follower_type")
        default_dialogue = f"{npc.name} joins you!"

        if follower_type == "quest":
            condition = flags.get("quest_condition")
            if self.engine.player.quest_flags.get(condition, False):
                return True, flags.get("follower_dialogue", default_dialogue)

        elif follower_type == "trade":
            required_item = flags.get("required_item")
            if required_item and self._player_has_item(required_item):
                return True, flags.get("follower_dialogue", default_dialogue)

        elif follower_type == "stat":
            required_stat = flags.get("required_stat")
            required_value = flags.get("required_stat_value", 10)
            if required_stat:
                player_stat = getattr(self.engine.player, required_stat, 0)
                if player_stat >= required_value:
                    return True, flags.get("follower_dialogue", default_dialogue)

        elif follower_type == "chance":
            base_chance = flags.get("chance_base", 0.5)
            stat_mod = flags.get("stat_modifier")
            chance = base_chance
            if stat_mod:
                stat_value = getattr(self.engine.player, stat_mod, 0)
                chance += stat_value * 0.01
            if random.random() < chance:
                return True, flags.get("follower_dialogue", default_dialogue)

        elif follower_type == "combat":
            required_kills = flags.get("requires_kills", 5)
            if self.engine.player.combat_kills >= required_kills:
                return True, flags.get("follower_dialogue", default_dialogue)

        elif follower_type == "alignment":
            required_align = flags.get("requires_alignment", "good")
            if self.engine.player.alignment == required_align:
                return True, flags.get("follower_dialogue", default_dialogue)

        return False, ""

    def _check_win_condition(self, condition_str: Optional[str]) -> bool:
        """
        Evaluate a win condition string.
        Format: "type:param" or bare "type".

        Supported types:
          kill_monster:ID       - monster with given id must be dead
          kill_all              - every monster in the adventure must be dead
          reach_room:ID         - player must currently be in that room
          carry_artifact:ID     - player must be carrying that artifact
          has_follower:ID       - player has a follower with the given monster id
          has_any_follower      - player has recruited at least one follower
          quest_completed:ID    - quest_flags[ID] must be True
        """
        if not condition_str:
            return False

        parts = condition_str.split(":", 1)
        cond_type = parts[0].strip()
        param = parts[1].strip() if len(parts) > 1 else None

        # ── kill_monster:ID ───────────────────────────────────────────────────
        if cond_type == "kill_monster" and param:
            try:
                monster = self.engine.world.monsters.get(int(param))
                return bool(monster and not monster.is_alive)
            except ValueError:
                pass

        # ── kill_all ──────────────────────────────────────────────────────────
        elif cond_type == "kill_all":
            monsters = list(self.engine.world.monsters.values())
            return bool(monsters) and all(not m.is_alive for m in monsters)

        # ── reach_room:ID ─────────────────────────────────────────────────────
        elif cond_type == "reach_room" and param:
            try:
                return self.engine.player.room_id == int(param)
            except ValueError:
                pass

        # ── carry_artifact:ID ─────────────────────────────────────────────────
        elif cond_type == "carry_artifact" and param:
            try:
                artifact_id = int(param)
                return any(a.id == artifact_id
                           for a in self.engine.world.artifacts_carried())
            except ValueError:
                pass

        # ── has_follower:ID ───────────────────────────────────────────────────
        elif cond_type == "has_follower" and param:
            try:
                follower_id = int(param)
                return any(m.id == follower_id
                           for m in self.engine.player.followers)
            except ValueError:
                pass

        # ── has_any_follower ──────────────────────────────────────────────────
        elif cond_type == "has_any_follower":
            return len(self.engine.player.followers) > 0

        # ── quest_completed:ID ────────────────────────────────────────────────
        elif cond_type == "quest_completed" and param:
            return bool(self.engine.player.quest_flags.get(param, False))

        # ── bare quest flag (backward compat) ─────────────────────────────────
        return bool(self.engine.player.quest_flags.get(condition_str, False))

    def _player_has_item(self, item_name: str) -> bool:
        """Check if player carries an item matching item_name."""
        carried = self.engine.world.artifacts_carried()
        return any(a.name.lower() == item_name.lower() for a in carried)

    def _offer_healing(self, npc) -> None:
        """Offer healing service from a friendly NPC."""
        missing = self.engine.player.hp_max - self.engine.player.hp

        if missing <= 0:
            print(self.engine.tc(f"{npc.name} says: \"You look healthy enough.\"", "desc"))
            return

        cost = missing * npc.heal_cost
        print(self.engine.tc(
            f"{npc.name} offers to heal {missing} HP "
            f"for {npc.heal_cost} gold/HP ({cost} gold total).", "desc"
        ))
        print(self.engine.tc(f"You have {self.engine.player.gold} gold.", "stat"))

        answer = input("  Accept? (y/n): ").strip().lower()
        if answer == "y":
            if self.engine.player.gold >= cost:
                self.engine.player.gold -= cost
                self.engine.player.hp = self.engine.player.hp_max
                print(self.engine.tc(f"{npc.name} tends your wounds. You feel much better!", "heal"))
                print(self.engine.tc(f"Gold remaining: {self.engine.player.gold}", "stat"))
            else:
                print(self.engine.tc(
                    f"Not enough gold. (Need {cost}, have {self.engine.player.gold})", "error"
                ))
        else:
            print(self.engine.tc("You decline.", "sys"))
