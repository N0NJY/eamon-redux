# Eamon Redux: Code vs. Spec Gap Analysis

**Date**: June 18, 2026  
**Status**: Current code examined against DATA_DRIVEN_ADVENTURE_DESIGN.md spec

---

## Executive Summary

**Current State**: Designer and engine are **procedural** (hardcoded logic).  
**Designed State**: Should be **data-driven** (flags in JSON, engine reads flags).

**Major Gaps**: 
1. Designer has NO flag/metadata editing system
2. Engine has NO flag-reading behavior system
3. NPC/monster editing completely missing from designer
4. No quest tracking infrastructure
5. No follower recruitment system
6. No generic event handler support

**Complexity**: Medium-High (requires refactoring engine and designer, but follows clear pattern)

---

## File-by-File Analysis

### DESIGNER.PY

#### Current State (620 lines)

**What works:**
- ✅ Menu navigation (adventure settings, rooms, artifacts)
- ✅ Room CRUD with exits management
- ✅ Artifact CRUD with basic properties
- ✅ ASCII map display
- ✅ Test play launcher

**What's missing:**

| Feature | Spec Requirement | Current Code | Gap |
|---------|------------------|--------------|-----|
| NPC/Monster editing | Menu option 4 to edit monsters | **MISSING** | No monsters menu in designer |
| Flag system | Metadata editing (is_follower, required_stat, etc.) | **MISSING** | Only basic artifact properties |
| Quest condition setup | Set follower_type, quest_condition in JSON | Manual JSON edit | Designer can't set flags |
| Trade mechanics | Set trade_npc, required_item flags | Manual JSON edit | Designer can't set flags |
| Stat requirements | Set required_stat, required_stat_value | Manual JSON edit | Designer can't set flags |
| Chance-based followers | Set chance_base, stat_modifier | Manual JSON edit | Designer can't set flags |
| Boss flags | Set is_boss, invulnerable | Manual JSON edit | Designer can't set flags |
| Event triggers | Set triggers_event on rooms/items | Manual JSON edit | Designer can't set flags |
| Escape vehicles | Set is_escape_vehicle, escape_dialogue | Manual JSON edit | Designer can't set flags |

#### Specific Code Gaps

**Missing: Monsters Menu**
```python
# Current designer.py line ~350 — main menu:
print(" 1. Adventure settings")
print(" 2. Rooms")
print(" 3. Artifacts (objects)")
print(" 4. View map")
print(" 5. Save")
print(" 6. Test play")
print(" 0. Quit")

# SHOULD HAVE:
# 4. Monsters & NPCs  ← MISSING
```

**Missing: Flag Editing**
```python
# Current artifact editing (line ~450):
a.name = prompt("Name", a.name)
a.description = prompt("Description", a.description)
a.weight = prompt_int("Weight", a.weight)
# ... basic properties only

# SHOULD INCLUDE:
# Flags section:
if prompt_bool("Is this tradeable?", False):
    a.trade_npc = prompt("Trade with NPC:", "")
    a.trade_dialogue = prompt("Dialogue when traded:", "")
# ... and many more flag prompts
```

**Missing: Artifact Type Completeness**
```python
# Current types (line ~480):
types = [ArtifactType.GENERIC, ArtifactType.WEAPON, ArtifactType.ARMOR,
         ArtifactType.CONTAINER, ArtifactType.READABLE, ArtifactType.LIGHT]

# Missing: POTION, FOOD, KEY, SPELLBOOK, SHIELD, RING, CLOAK
# These are defined in world.py but designer doesn't create them
```

---

### ENGINE.PY

#### Current State (1202 lines)

**What works:**
- ✅ Game loop and command dispatch
- ✅ Monster combat
- ✅ Inventory/equipment system
- ✅ Spellcasting basics
- ✅ Room/artifact navigation
- ✅ cmd_talk() exists

**What's missing for flag-based behavior:**

| Feature | Spec Requirement | Current Code | Gap |
|---------|------------------|--------------|-----|
| Player.quest_flags | Track quest completion | `self.player.quest_flags` **MISSING** | Player class needs quest tracking |
| Player.followers | List of follower NPCs | `self.player.followers` **MISSING** | Player class needs followers list |
| Generic event handlers | on_talk_to_npc, on_use_item, etc. | **MISSING** | No event handler system |
| Flag-based NPC behavior | Read is_follower, follower_type, etc. | **HARDCODED** | cmd_talk() only does healing |
| Follower recruitment | Check conditions, add to followers | **MISSING** | No recruitment logic |
| Dynamic dialogue | Based on NPC flags | Hardcoded healing dialogue | Can't change dynamically |
| Quest completion | Mark quests done via flags | **MISSING** | No quest completion system |
| Win condition checking | Read flags from rooms/quests | Hardcoded (line ~1045) | Can't check dynamic conditions |

#### Specific Code Gaps

**Current cmd_talk() - HARDCODED FOR HEALING ONLY (line ~850)**
```python
def cmd_talk(self, noun: str) -> None:
    # ... finds NPC ...
    
    if npc.dialogue:
        print(f'\n {npc.name} says: "{npc.dialogue}"')
    else:
        print(f" The {npc.name} regards you silently.")
    
    # HARDCODED: Only healing mechanic supported
    if npc.heal_amount > 0 and npc.heal_cost > 0:
        # ... healing transaction ...
```

**Should be:**
```python
def cmd_talk(self, noun: str) -> None:
    # ... finds NPC ...
    
    # Call event handler
    if self.event_handlers:
        self.event_handlers.on_talk_to_npc(self, npc.name, self.player)
        # Handler determines recruitment, dialogue, healing, etc.
```

**Missing: Player quest/follower tracking (player.py)**
```python
# Current Player class - should have:
class Player:
    def __init__(self):
        self.hp = ...
        self.gold = ...
        # MISSING:
        # self.quest_flags = {}        # {"rescued_girl": True, ...}
        # self.followers = []          # [npc1, npc2, ...]
```

**Missing: Event handler infrastructure**
```python
# engine.py __init__ currently:
def __init__(self, world: World, player: Player):
    self.world = world
    self.player = player
    self.running = True
    self.exit_code = 0
    self.light_active = False
    
    # MISSING:
    # self.event_handlers = AdventureEventHandlers(self, world)
```

**Hardcoded win condition check (line ~1045)**
```python
def _check_win(self) -> bool:
    """Currently checks for specific room ID."""
    # This is tied to adventure.json's win_condition
    # But there's no generic flag-based checking
    # Should read room.flags["is_win_room"] and room.flags["win_condition"]
```

**Missing: Consumed item deletion**
```python
def _consume(self, noun: str, atype: str, verb: str) -> None:
    # ...
    target.room_id = -999  # "consumed" via magic number
    
    # Should delete: del self.world.artifacts[target.id]
    # Or set a consumed_flag
```

---

## Player Class Gap

### Current player.py

```python
class Player:
    def __init__(self, character_data=None):
        self.room_id = ...
        self.hp = ...
        self.mana = ...
        self.gold = ...
        self.equipped = {}
        self.char_class = ...
        # ... many stats ...
```

**Missing Fields:**
```python
        self.quest_flags = {}      # Track completed quests
        self.followers = []        # List of NPC/Monster objects
        self.alignment = "neutral" # good/neutral/evil
        self.combat_kills = 0      # For combat-based followers
```

---

## World Class / Artifact JSON Gap

### Artifact JSON currently supports:

```json
{
  "id": 1,
  "name": "...",
  "description": "...",
  "room_id": 1,
  "artifact_type": "weapon",
  "weight": 3,
  "damage_dice": 1,
  "damage_sides": 6,
  "value": 15,
  "is_quest_item": false,
  "synonyms": [...]
}
```

**Missing: flags object for metadata**
```json
{
  "id": 1,
  "name": "silver amulet",
  ...
  "flags": {
    "is_tradeable": true,
    "trade_npc": "henrich",
    "trade_dialogue": "Ah! The amulet! I'll join you!",
    "is_quest_item": true,
    "quest_id": "amulet_for_henrich"
  }
}
```

### Monster/NPC JSON currently supports:

```json
{
  "id": 1,
  "name": "giant rat",
  "attitude": "hostile",
  "hp": 8,
  "dialogue": "",
  "heal_amount": 0,
  "heal_cost": 0,
  ...
}
```

**Missing: flags object for follower/NPC behavior**
```json
{
  "id": 1,
  "name": "the girl",
  ...
  "flags": {
    "is_follower": true,
    "follower_type": "quest",
    "quest_condition": "rescued_from_priest",
    "follower_dialogue": "Thank you! I'll follow you!",
    "can_fight": false,
    "can_die": false
  }
}
```

### Room JSON currently supports:

```json
{
  "id": 1,
  "name": "...",
  "description": "...",
  "exits": { "north": 2 },
  "locked_exits": { "north": 5 },
  "is_dark": false
}
```

**Missing: flags object for room behavior**
```json
{
  "id": 1,
  ...
  "flags": {
    "is_exit": true,
    "is_win_room": true,
    "win_condition": "has_rescued_girl",
    "win_dialogue": "You've escaped with the girl! You've won!",
    "triggers_event": "encounter_boss"
  }
}
```

---

## Implementation Path

### Phase 1: Data Model Updates (Core)
- [ ] Add `flags` dict to Artifact, Monster, Room in world.py
- [ ] Add `quest_flags`, `followers`, `alignment`, `combat_kills` to Player
- [ ] Update JSON loaders to read flags (with defaults for backward compat)

### Phase 2: Designer Enhancements  
- [ ] Add "4. Monsters & NPCs" menu to designer.py
- [ ] Add flag-editing submenu for artifacts (is_tradeable, trade_npc, etc.)
- [ ] Add flag-editing submenu for monsters (is_follower, follower_type, etc.)
- [ ] Add flag-editing submenu for rooms (is_exit, is_win_room, etc.)
- [ ] Auto-generate followers.json from monster flags

### Phase 3: Engine Event Handler System
- [ ] Create `event_handlers.py` with generic AdventureEventHandlers class
- [ ] Implement `on_talk_to_npc()` — reads flags, recruits followers
- [ ] Implement `on_use_item()` — reads flags, triggers events/escapes
- [ ] Implement `on_enter_room()` — reads room flags
- [ ] Replace hardcoded cmd_talk() with event handler
- [ ] Add follower recruitment logic with condition checking
- [ ] Add quest completion tracking

### Phase 4: Win Condition / Quest System
- [ ] Make win condition checks generic (read room/quest flags)
- [ ] Implement quest_flags in Player
- [ ] Create `_mark_quest_complete(quest_id)` method
- [ ] Hook quest completion into appropriate game events

### Phase 5: Testing & Polish
- [ ] Test with Beginner's Cave (girl rescue)
- [ ] Test with different follower types (trade, chance, stat, etc.)
- [ ] Verify backward compatibility with existing adventures
- [ ] Create template event_handlers.py for new adventures

---

## Code Modification Summary

### Files to Modify

| File | Changes | Complexity |
|------|---------|------------|
| world.py | Add flags dicts to Artifact, Monster, Room; update JSON loaders | Medium |
| player.py | Add quest_flags, followers, alignment, combat_kills | Low |
| designer.py | Add monsters menu, flag-editing UI | High |
| engine.py | Integrate event handlers, replace hardcoded cmd_talk() | High |
| NEW: event_handlers.py | Generic adventure event system | Medium |
| NEW: adventures/{name}/event_handlers.py | Adventure-specific overrides | Low |

### Effort Estimate

- **Phase 1 (Data)**: 1-2 hours
- **Phase 2 (Designer)**: 3-4 hours
- **Phase 3 (Engine)**: 3-4 hours
- **Phase 4 (Quests)**: 1-2 hours
- **Phase 5 (Testing)**: 1-2 hours

**Total**: ~10-15 hours of development

---

## Key Decisions Needed

1. **Backward Compatibility**: Keep old adventure JSON working? (Recommend: yes, with defaults)
2. **Event Handler Location**: Global `event_handlers.py` or per-adventure?  
   (Recommend: per-adventure with fallback to generic)
3. **Flag Validation**: Designer checks flags on save, or runtime validation?  
   (Recommend: both, but start with runtime)
4. **Consumed Items**: Delete from world or mark with flag?  
   (Recommend: delete, clean up memory)
5. **Follower Persistence**: Save followers in character file? (Recommend: yes, between adventures)

---

## Summary: Current Code is Functional but Not Extensible

The current designer and engine work well for **basic adventure creation**, but they **hardcode** specific mechanics (healing NPCs, fixed win conditions, etc.). The flag-based system makes it possible to support **any** adventure mechanics without code changes.

**This gap is by design** — the current code is simple and works. The data-driven design is the next level of sophistication, enabling infinite adventure variety with the same engine.

---

**Next Step**: Review this analysis, decide which phases to implement, then work through them in order. Phase 1 (data model) is prerequisite for everything else.
