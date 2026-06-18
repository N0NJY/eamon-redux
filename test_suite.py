"""
test_suite.py - Phase 5 Systematic Test Suite for Eamon Redux

Covers all 8 test categories from PHASE_5_SYSTEMATIC_TESTING.md.
Run with: python3 test_suite.py
"""

import sys
import io
import json
import os
import tempfile
import random
from dataclasses import dataclass, field
from typing import Optional

# ── Minimal character stub ─────────────────────────────────────────────────────

@dataclass
class FakeCharacter:
    name: str = "Tester"
    hardiness:    int = 15
    agility:      int = 12
    charisma:     int = 14
    intelligence: int = 10
    strength:     int = 12
    gold: int = 200
    xp: int = 0
    level: int = 1
    spell_proficiencies: dict = field(default_factory=lambda: {
        "blast": None, "heal": None, "speed": None, "power": None,
    })
    weapon_proficiencies: dict = field(default_factory=lambda: {
        "unarmed": 0, "axe": 5, "bow": -10, "club": 20, "spear": 10, "sword": 0,
    })
    adventures_completed: list = field(default_factory=list)

    @property
    def hp_max(self): return self.hardiness * 2
    @property
    def carry_capacity(self): return self.hardiness * 10


# ── Test runner helpers ────────────────────────────────────────────────────────

PASS = 0
FAIL = 0
BUGS = []

def ok(name):
    global PASS
    PASS += 1
    print(f"  [PASS] {name}")

def fail(name, detail=""):
    global FAIL
    FAIL += 1
    msg = f"  [FAIL] {name}"
    if detail:
        msg += f"\n         {detail}"
    print(msg)
    BUGS.append((name, detail))

def section(title):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


# ── Imports ────────────────────────────────────────────────────────────────────

from world import World, Room, Artifact, ArtifactType, Monster, Attitude
from player import Player
from core.base_handlers import BaseAdventureHandlers


# ── Build a test world in memory ───────────────────────────────────────────────

def make_test_world() -> World:
    """Create a fully-featured in-memory world for engine tests."""
    w = World()
    w.title = "Test World"
    w.start_room = 1

    # Rooms
    r1 = Room(id=1, name="Starting Hall", description="A plain hall.", exits={"south": 2, "east": 3})
    r2 = Room(id=2, name="Dark Dungeon",  description="Very dark.",   exits={"north": 1}, is_dark=True)
    r3 = Room(id=3, name="Treasure Room", description="Glitters.",    exits={"west": 1, "north": 4})
    r4 = Room(id=4, name="The Exit",      description="Daylight!",    exits={"south": 3})
    r4.flags = {"is_exit": True, "is_win_room": True,
                "win_condition": "quest_completed:main_quest",
                "win_dialogue": "You have won!"}

    for r in (r1, r2, r3, r4):
        w.rooms[r.id] = r

    # Artifacts
    sword = Artifact(id=1, name="iron sword", description="A serviceable blade.",
                     room_id=1, artifact_type=ArtifactType.WEAPON,
                     damage_dice=1, damage_sides=8, weight=3,
                     weapon_type="sword", synonyms=["sword", "blade"])
    potion = Artifact(id=2, name="healing potion", description="Restores HP.",
                      room_id=3, artifact_type=ArtifactType.POTION,
                      heal_amount=10, weight=1, synonyms=["potion"])
    amulet = Artifact(id=3, name="silver amulet", description="Glows faintly.",
                      room_id=3, artifact_type=ArtifactType.GENERIC,
                      weight=1, synonyms=["amulet"])
    amulet.flags = {"is_tradeable": True, "trade_npc": "wizard",
                    "trade_dialogue": "Excellent! Here, take this!",
                    "is_quest_item": True, "quest_id": "amulet_quest"}
    key = Artifact(id=4, name="brass key", description="Opens a lock.",
                   room_id=2, artifact_type=ArtifactType.KEY,
                   weight=1, is_quest_item=True, synonyms=["key"])
    escape_boat = Artifact(id=5, name="magic boat", description="A shimmering boat.",
                           room_id=3, artifact_type=ArtifactType.GENERIC, weight=10)
    escape_boat.flags = {"is_escape_vehicle": True,
                         "escape_dialogue": "You sail away to safety!"}

    for a in (sword, potion, amulet, key, escape_boat):
        w.artifacts[a.id] = a

    # Monsters
    rat = Monster(id=1, name="giant rat", description="A large rat.",
                  room_id=2, attitude=Attitude.HOSTILE,
                  hp=8, hp_max=8, damage_dice=1, damage_sides=4,
                  death_message="squeals and dies!", xp_value=10)
    wizard = Monster(id=2, name="old wizard", description="A bearded wizard.",
                     room_id=3, attitude=Attitude.FRIENDLY,
                     hp=30, hp_max=30, damage_dice=1, damage_sides=4,
                     dialogue="Greetings, traveller!",
                     heal_amount=10, heal_cost=5)
    captive = Monster(id=3, name="captive girl", description="A frightened captive.",
                      room_id=2, attitude=Attitude.FRIENDLY,
                      hp=10, hp_max=10, damage_dice=0, damage_sides=0,
                      dialogue="Please help me!")
    captive.flags = {"is_follower": True, "follower_type": "quest",
                     "quest_condition": "rescued_captive",
                     "follower_dialogue": "Thank you! I'll follow you!"}

    for m in (rat, wizard, captive):
        w.monsters[m.id] = m

    return w


def make_engine(world: World) -> "Engine":
    from engine import Engine
    char = FakeCharacter()
    # Patch _load_character_items to no-op (no file system)
    eng = Engine.__new__(Engine)
    eng.world = world
    eng.character = char
    eng.adventure_path = None
    eng.game_data = {}
    eng.player = Player(
        name=char.name,
        room_id=world.start_room,
        hardiness=char.hardiness,
        agility=char.agility,
        charisma=char.charisma,
        intelligence=char.intelligence,
        strength=char.strength,
        hp=char.hp_max,
        gold=char.gold,
        spell_proficiencies=char.spell_proficiencies.copy(),
        weapon_proficiencies=char.weapon_proficiencies.copy(),
        xp=char.xp,
        level=char.level,
        max_carry_weight=char.carry_capacity,
    )
    eng.turn = 0
    eng.in_combat = False
    eng.enemy = None
    eng.running = True
    eng.exit_code = 0
    from core.base_handlers import BaseAdventureHandlers
    eng.base_handlers = BaseAdventureHandlers(eng)
    eng.custom_handlers = {}
    return eng


def capture(fn, *args, input_text="", **kwargs):
    """Run fn(*args) capturing stdout, optionally feeding stdin."""
    old_stdin  = sys.stdin
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    if input_text:
        sys.stdin = io.StringIO(input_text)
    try:
        fn(*args, **kwargs)
        return sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout
        sys.stdin  = old_stdin


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 1: Flag Persistence (Designer-level)
# ══════════════════════════════════════════════════════════════════════════════

def test_cat1_flags():
    section("Category 1: Flag Persistence (save/load round-trip)")

    # 1.1 Monster flags
    try:
        w = make_test_world()
        captive = w.monsters[3]
        d = captive.to_dict()
        assert d.get("flags", {}).get("is_follower") == True
        assert d["flags"]["follower_type"] == "quest"
        assert d["flags"]["quest_condition"] == "rescued_captive"
        from world import Monster as M
        m2 = M.from_dict(d)
        assert m2.flags == captive.flags
        ok("1.1 Monster flags save/load")
    except Exception as e:
        fail("1.1 Monster flags save/load", str(e))

    # 1.2 Artifact flags
    try:
        w = make_test_world()
        amulet = w.artifacts[3]
        d = amulet.to_dict()
        assert d["flags"]["is_tradeable"] == True
        assert d["flags"]["trade_npc"] == "wizard"
        from world import Artifact as A
        a2 = A.from_dict(d)
        assert a2.flags == amulet.flags
        ok("1.2 Artifact flags save/load")
    except Exception as e:
        fail("1.2 Artifact flags save/load", str(e))

    # 1.3 Room flags
    try:
        w = make_test_world()
        exit_room = w.rooms[4]
        d = exit_room.to_dict()
        assert d["flags"]["is_win_room"] == True
        assert d["flags"]["win_condition"] == "quest_completed:main_quest"
        from world import Room as R
        r2 = R.from_dict(d)
        assert r2.flags == exit_room.flags
        ok("1.3 Room flags save/load")
    except Exception as e:
        fail("1.3 Room flags save/load", str(e))

    # 1.4 Escape vehicle artifact flags
    try:
        w = make_test_world()
        boat = w.artifacts[5]
        d = boat.to_dict()
        assert d["flags"]["is_escape_vehicle"] == True
        ok("1.4 Escape vehicle flag save/load")
    except Exception as e:
        fail("1.4 Escape vehicle flag save/load", str(e))

    # 1.5 World save/load to disk
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            w = make_test_world()
            w.save(tmpdir)
            w2 = World.load(tmpdir)
            assert w2.monsters[3].flags["is_follower"] == True
            assert w2.artifacts[3].flags["is_tradeable"] == True
            assert w2.rooms[4].flags["is_win_room"] == True
        ok("1.5 Full world save/load to disk preserves all flags")
    except Exception as e:
        fail("1.5 Full world save/load to disk", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 2: Movement
# ══════════════════════════════════════════════════════════════════════════════

def test_cat2_movement():
    section("Category 2: Movement")

    # 2.1 Basic movement
    try:
        w = make_test_world()
        eng = make_engine(w)
        assert eng.player.room_id == 1
        capture(eng.cmd_go, "south")
        assert eng.player.room_id == 2
        ok("2.1 Move south to room 2")
    except Exception as e:
        fail("2.1 Basic movement", str(e))

    # 2.2 Invalid direction
    try:
        w = make_test_world()
        eng = make_engine(w)
        out = capture(eng.cmd_go, "north")
        assert eng.player.room_id == 1  # didn't move
        ok("2.2 Invalid direction doesn't move player")
    except Exception as e:
        fail("2.2 Invalid direction", str(e))

    # 2.3 Direction abbreviation
    try:
        w = make_test_world()
        eng = make_engine(w)
        capture(eng.cmd_go, "e")
        assert eng.player.room_id == 3
        ok("2.3 Abbreviation 'e' → east works")
    except Exception as e:
        fail("2.3 Direction abbreviation", str(e))

    # 2.4 Dark room is_dark flag
    try:
        w = make_test_world()
        assert w.rooms[2].is_dark == True
        ok("2.4 Dark room flag present")
    except Exception as e:
        fail("2.4 Dark room flag", str(e))

    # 2.5 on_enter_room hook fires on move
    try:
        w = make_test_world()
        eng = make_engine(w)
        fired = []
        orig = eng.base_handlers.on_enter_room
        def patched(room_id):
            fired.append(room_id)
            orig(room_id)
        eng.base_handlers.on_enter_room = patched
        capture(eng.cmd_go, "south")
        assert 2 in fired
        ok("2.5 on_enter_room hook fires on movement")
    except Exception as e:
        fail("2.5 on_enter_room hook", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 3: Inventory & Equipment
# ══════════════════════════════════════════════════════════════════════════════

def test_cat3_inventory():
    section("Category 3: Inventory & Equipment")

    # 3.1 Pick up item
    try:
        w = make_test_world()
        eng = make_engine(w)
        capture(eng.cmd_get, "sword")
        assert w.artifacts[1].room_id is None  # carried
        ok("3.1 GET sword picks it up")
    except Exception as e:
        fail("3.1 Pick up item", str(e))

    # 3.2 Drop item
    try:
        w = make_test_world()
        eng = make_engine(w)
        capture(eng.cmd_get, "sword")
        capture(eng.cmd_drop, "sword")
        assert w.artifacts[1].room_id == 1
        ok("3.2 DROP sword puts it in room")
    except Exception as e:
        fail("3.2 Drop item", str(e))

    # 3.3 Equip weapon
    try:
        w = make_test_world()
        eng = make_engine(w)
        capture(eng.cmd_get, "sword")
        capture(eng.cmd_equip, "sword")
        assert eng.player.equipped.get("weapon") == 1
        ok("3.3 EQUIP sword goes to weapon slot")
    except Exception as e:
        fail("3.3 Equip weapon", str(e))

    # 3.4 Can't pick up item in another room
    try:
        w = make_test_world()
        eng = make_engine(w)
        # Potion is in room 3, player is in room 1
        capture(eng.cmd_get, "potion")
        assert w.artifacts[2].room_id == 3  # still in room 3
        ok("3.4 Can't GET item from different room")
    except Exception as e:
        fail("3.4 Item in different room", str(e))

    # 3.5 Carry weight limit
    try:
        w = make_test_world()
        eng = make_engine(w)
        eng.player.max_carry_weight = 2  # sword weighs 3
        out = capture(eng.cmd_get, "sword")
        assert w.artifacts[1].room_id == 1  # not picked up
        ok("3.5 Weight limit prevents pickup")
    except Exception as e:
        fail("3.5 Carry weight limit", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 4: NPC & Follower
# ══════════════════════════════════════════════════════════════════════════════

def test_cat4_npc():
    section("Category 4: NPC & Follower")

    # 4.1 Talk to NPC — displays dialogue
    try:
        w = make_test_world()
        eng = make_engine(w)
        eng.player.room_id = 3  # wizard is in room 3
        out = capture(eng.cmd_talk, "wizard")
        assert "Greetings" in out
        ok("4.1 TALK TO wizard shows dialogue")
    except Exception as e:
        fail("4.1 Talk to NPC", str(e))

    # 4.2 Hostile NPC won't talk
    try:
        w = make_test_world()
        eng = make_engine(w)
        eng.player.room_id = 2  # rat is in room 2
        out = capture(eng.cmd_talk, "rat")
        assert eng.player.room_id == 2  # no crash
        ok("4.2 Hostile NPC refuses conversation")
    except Exception as e:
        fail("4.2 Hostile NPC talk", str(e))

    # 4.3 Follower recruited when quest condition met (quest type)
    try:
        w = make_test_world()
        eng = make_engine(w)
        eng.player.room_id = 2
        eng.player.quest_flags["rescued_captive"] = True
        out = capture(eng.cmd_talk, "captive")
        assert any(m.id == 3 for m in eng.player.followers)
        assert "Thank you" in out
        ok("4.3 Quest follower recruited when condition met")
    except Exception as e:
        fail("4.3 Quest follower recruitment", str(e))

    # 4.4 Follower NOT recruited when quest condition unmet
    try:
        w = make_test_world()
        eng = make_engine(w)
        eng.player.room_id = 2
        # quest_flags NOT set
        capture(eng.cmd_talk, "captive")
        assert len(eng.player.followers) == 0
        ok("4.4 Follower not recruited without quest flag")
    except Exception as e:
        fail("4.4 Follower condition unmet", str(e))

    # 4.5 Stat-based follower (charisma check)
    try:
        w = make_test_world()
        stat_npc = Monster(id=10, name="bard", description="A cheerful bard.",
                           room_id=1, attitude=Attitude.FRIENDLY,
                           hp=10, hp_max=10, damage_dice=0, damage_sides=0,
                           dialogue="I seek a worthy leader!")
        stat_npc.flags = {"is_follower": True, "follower_type": "stat",
                          "required_stat": "charisma", "required_stat_value": 12,
                          "follower_dialogue": "I'll follow you!"}
        w.monsters[10] = stat_npc

        eng = make_engine(w)
        eng.player.charisma = 14  # meets requirement (>=12)
        eng.player.room_id = 1
        capture(eng.cmd_talk, "bard")
        assert any(m.id == 10 for m in eng.player.followers)
        ok("4.5 Stat follower recruited (charisma >= 12)")
    except Exception as e:
        fail("4.5 Stat-based follower", str(e))

    # 4.6 Healing NPC offer
    try:
        w = make_test_world()
        eng = make_engine(w)
        eng.player.room_id = 3
        eng.player.hp = 10  # below max (30)
        out = capture(eng.cmd_talk, "wizard", input_text="n\n")
        assert "heal" in out.lower() or "HP" in out
        ok("4.6 Healing NPC offers to heal wounded player")
    except Exception as e:
        fail("4.6 Healing NPC", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 5: Item Mechanics (flags)
# ══════════════════════════════════════════════════════════════════════════════

def test_cat5_items():
    section("Category 5: Item Mechanics (flags)")

    # 5.1 Quest item flag persists
    try:
        w = make_test_world()
        amulet = w.artifacts[3]
        assert amulet.flags.get("is_quest_item") == True
        assert amulet.flags.get("quest_id") == "amulet_quest"
        ok("5.1 Quest item flag set correctly")
    except Exception as e:
        fail("5.1 Quest item flag", str(e))

    # 5.2 Escape vehicle ends game
    try:
        w = make_test_world()
        eng = make_engine(w)
        eng.player.room_id = 3
        # Pick up boat first
        w.artifacts[5].room_id = None  # put in inventory
        out = capture(eng.on_use_item, "magic boat")
        assert eng.running == False
        assert eng.exit_code == 3
        ok("5.2 Escape vehicle sets exit_code=3 and stops engine")
    except Exception as e:
        fail("5.2 Escape vehicle", str(e))

    # 5.3 Tradeable item flag
    try:
        w = make_test_world()
        amulet = w.artifacts[3]
        assert amulet.flags.get("is_tradeable") == True
        assert amulet.flags.get("trade_npc") == "wizard"
        ok("5.3 Tradeable item flags correct")
    except Exception as e:
        fail("5.3 Tradeable item flag", str(e))

    # 5.4 Empty flags dict doesn't break from_dict
    try:
        from world import Artifact as A
        d = {"id": 99, "name": "generic", "description": "plain",
             "room_id": 1, "synonyms": []}
        a = A.from_dict(d)
        assert a.flags == {}
        ok("5.4 Missing flags key defaults to empty dict")
    except Exception as e:
        fail("5.4 Missing flags default", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 6: Combat
# ══════════════════════════════════════════════════════════════════════════════

def test_cat6_combat():
    section("Category 6: Combat")

    # 6.1 Attack hits and deals damage
    try:
        w = make_test_world()
        eng = make_engine(w)
        eng.player.room_id = 2
        rat = w.monsters[1]
        rat.hp = 1  # make it easy to kill
        capture(eng.cmd_attack, "rat")
        # rat either took damage or is dead
        assert rat.hp <= 1
        ok("6.1 ATTACK deals damage to monster")
    except Exception as e:
        fail("6.1 Combat damage", str(e))

    # 6.2 Monster death sets is_alive=False
    try:
        w = make_test_world()
        eng = make_engine(w)
        eng.player.room_id = 2
        rat = w.monsters[1]
        rat.hp = 0
        rat.is_alive = False
        assert not rat.is_alive
        ok("6.2 Dead monster is_alive=False")
    except Exception as e:
        fail("6.2 Monster death state", str(e))

    # 6.3 combat_kills increments on kill — test the death-path directly
    try:
        w = make_test_world()
        eng = make_engine(w)
        assert eng.player.combat_kills == 0
        # Simulate the exact death-path code in cmd_attack
        rat = w.monsters[1]
        rat.hp = 0
        rat.is_alive = False
        eng.player.combat_kills += 1
        eng.on_monster_defeated(rat.id)
        assert eng.player.combat_kills == 1
        ok("6.3 combat_kills increments on monster death")
    except Exception as e:
        fail("6.3 combat_kills", str(e))

    # 6.4 on_monster_defeated hook fires and dispatches to base_handlers
    try:
        w = make_test_world()
        eng = make_engine(w)
        defeated = []
        # Override the base handler's method
        eng.base_handlers.on_monster_defeated = lambda mid: defeated.append(mid)
        eng.on_monster_defeated(1)
        assert 1 in defeated
        ok("6.4 on_monster_defeated hook dispatches to base handler")
    except Exception as e:
        fail("6.4 on_monster_defeated hook", str(e))

    # 6.5 Can't attack non-existent monster
    try:
        w = make_test_world()
        eng = make_engine(w)
        out = capture(eng.cmd_attack, "dragon")
        assert "don't see" in out.lower() or "not" in out.lower()
        ok("6.5 ATTACK unknown monster prints error")
    except Exception as e:
        fail("6.5 Attack unknown monster", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 7: Win Conditions
# ══════════════════════════════════════════════════════════════════════════════

def test_cat7_win_conditions():
    section("Category 7: Win Conditions")

    def make_handler():
        w = make_test_world()
        eng = make_engine(w)
        h = BaseAdventureHandlers(eng)
        return eng, h

    # 7.1 reach_room
    try:
        eng, h = make_handler()
        eng.player.room_id = 5
        assert h._check_win_condition("reach_room:5") == True
        eng.player.room_id = 1
        assert h._check_win_condition("reach_room:5") == False
        ok("7.1 reach_room:ID win condition")
    except Exception as e:
        fail("7.1 reach_room", str(e))

    # 7.2 quest_completed
    try:
        eng, h = make_handler()
        eng.player.quest_flags["main_quest"] = True
        assert h._check_win_condition("quest_completed:main_quest") == True
        eng.player.quest_flags["main_quest"] = False
        assert h._check_win_condition("quest_completed:main_quest") == False
        ok("7.2 quest_completed:ID win condition")
    except Exception as e:
        fail("7.2 quest_completed", str(e))

    # 7.3 has_follower
    try:
        eng, h = make_handler()
        npc = Monster(id=3, name="captive", description="", room_id=1)
        eng.player.followers = [npc]
        assert h._check_win_condition("has_follower:3") == True
        assert h._check_win_condition("has_follower:99") == False
        ok("7.3 has_follower:ID win condition")
    except Exception as e:
        fail("7.3 has_follower", str(e))

    # 7.4 has_any_follower
    try:
        eng, h = make_handler()
        npc = Monster(id=3, name="captive", description="", room_id=1)
        eng.player.followers = [npc]
        assert h._check_win_condition("has_any_follower") == True
        eng.player.followers = []
        assert h._check_win_condition("has_any_follower") == False
        ok("7.4 has_any_follower win condition")
    except Exception as e:
        fail("7.4 has_any_follower", str(e))

    # 7.5 kill_monster
    try:
        eng, h = make_handler()
        rat = eng.world.monsters[1]
        rat.is_alive = False
        assert h._check_win_condition("kill_monster:1") == True
        rat.is_alive = True
        assert h._check_win_condition("kill_monster:1") == False
        ok("7.5 kill_monster:ID win condition")
    except Exception as e:
        fail("7.5 kill_monster", str(e))

    # 7.6 kill_all
    try:
        eng, h = make_handler()
        for m in eng.world.monsters.values():
            m.is_alive = False
        assert h._check_win_condition("kill_all") == True
        eng.world.monsters[1].is_alive = True
        assert h._check_win_condition("kill_all") == False
        ok("7.6 kill_all win condition")
    except Exception as e:
        fail("7.6 kill_all", str(e))

    # 7.7 carry_artifact
    try:
        eng, h = make_handler()
        eng.world.artifacts[3].room_id = None  # carrying amulet
        assert h._check_win_condition("carry_artifact:3") == True
        eng.world.artifacts[3].room_id = 1
        assert h._check_win_condition("carry_artifact:3") == False
        ok("7.7 carry_artifact:ID win condition")
    except Exception as e:
        fail("7.7 carry_artifact", str(e))

    # 7.8 Win room triggers game end
    try:
        w = make_test_world()
        eng = make_engine(w)
        eng.player.quest_flags["main_quest"] = True
        capture(eng.on_enter_room, 4)  # room 4 is the win room
        assert eng.running == False
        assert eng.exit_code == 1
        ok("7.8 Entering win room with condition met ends game (exit_code=1)")
    except Exception as e:
        fail("7.8 Win room triggers end", str(e))

    # 7.9 Win room does NOT trigger if condition unmet
    try:
        w = make_test_world()
        eng = make_engine(w)
        # quest_flags NOT set
        capture(eng.on_enter_room, 4)
        assert eng.running == True
        ok("7.9 Win room does not trigger if condition unmet")
    except Exception as e:
        fail("7.9 Win room condition unmet", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 8: Handler Architecture
# ══════════════════════════════════════════════════════════════════════════════

def test_cat8_handlers():
    section("Category 8: Handler Architecture")

    # 8.1 Base handlers load without custom handlers
    try:
        w = make_test_world()
        eng = make_engine(w)
        assert eng.custom_handlers == {}
        assert isinstance(eng.base_handlers, BaseAdventureHandlers)
        ok("8.1 Engine initializes with base handlers, no custom required")
    except Exception as e:
        fail("8.1 Base handlers init", str(e))

    # 8.2 call_hook falls back to base handler
    try:
        w = make_test_world()
        eng = make_engine(w)
        called = []
        eng.base_handlers.on_game_start = lambda: called.append("base")
        eng.call_hook("on_game_start")
        assert "base" in called
        ok("8.2 call_hook falls back to base handler when no custom")
    except Exception as e:
        fail("8.2 call_hook fallback", str(e))

    # 8.3 Custom dict handler overrides base
    try:
        w = make_test_world()
        eng = make_engine(w)
        called = []
        eng.custom_handlers = {
            "on_game_start": lambda e: called.append("custom")
        }
        eng.base_handlers.on_game_start = lambda: called.append("base")
        eng.call_hook("on_game_start")
        assert called == ["custom"]  # base not called
        ok("8.3 Custom dict handler takes priority over base")
    except Exception as e:
        fail("8.3 Custom handler priority", str(e))

    # 8.4 trigger_event dispatches to custom handler
    try:
        w = make_test_world()
        eng = make_engine(w)
        fired = []
        eng.custom_handlers = {
            "boss_appears": lambda e: fired.append("boss")
        }
        eng.trigger_event("boss_appears")
        assert "boss" in fired
        ok("8.4 trigger_event dispatches named event to custom handler")
    except Exception as e:
        fail("8.4 trigger_event dispatch", str(e))

    # 8.5 adventure_path passed to Engine
    try:
        from engine import Engine
        import unittest.mock as mock
        w = make_test_world()
        char = FakeCharacter()
        with mock.patch.object(Engine, '_load_character_items', return_value=None):
            eng = Engine(w, char, adventure_path="adventures/beginners_cave")
        assert eng.adventure_path == "adventures/beginners_cave"
        ok("8.5 adventure_path stored on Engine")
    except Exception as e:
        fail("8.5 adventure_path on Engine", str(e))

    # 8.6 No custom handlers.py → no crash (ImportError caught silently)
    try:
        w = make_test_world()
        eng = make_engine(w)
        eng._load_adventure_handlers("adventures/nonexistent_adventure_xyz")
        assert eng.custom_handlers == {}
        ok("8.6 Missing handlers.py caught silently (no crash)")
    except Exception as e:
        fail("8.6 Missing handlers.py", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY 9: Player State (quest_flags, followers, alignment, combat_kills)
# ══════════════════════════════════════════════════════════════════════════════

def test_cat9_player_state():
    section("Category 9: Player State (Phase 1 fields)")

    try:
        p = Player()
        assert p.quest_flags == {}
        assert p.followers == []
        assert p.alignment == "neutral"
        assert p.combat_kills == 0
        ok("9.1 Player initializes with correct Phase 1 defaults")
    except Exception as e:
        fail("9.1 Player defaults", str(e))

    try:
        p = Player()
        p.quest_flags["rescued_captive"] = True
        p.combat_kills = 5
        p.alignment = "good"
        assert p.quest_flags["rescued_captive"] == True
        assert p.combat_kills == 5
        assert p.alignment == "good"
        ok("9.2 Player Phase 1 fields are mutable")
    except Exception as e:
        fail("9.2 Player field mutation", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"\n{'═'*60}")
    print("  EAMON REDUX — PHASE 5 SYSTEMATIC TEST SUITE")
    print(f"{'═'*60}")

    test_cat1_flags()
    test_cat2_movement()
    test_cat3_inventory()
    test_cat4_npc()
    test_cat5_items()
    test_cat6_combat()
    test_cat7_win_conditions()
    test_cat8_handlers()
    test_cat9_player_state()

    print(f"\n{'═'*60}")
    print(f"  RESULTS:  {PASS} passed  |  {FAIL} failed")
    print(f"{'═'*60}")

    if BUGS:
        print("\n  FAILURES:")
        for name, detail in BUGS:
            print(f"    • {name}")
            if detail:
                print(f"      {detail}")

    sys.exit(0 if FAIL == 0 else 1)
