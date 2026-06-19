# PHASE 3: Engine Refactoring with Handler Architecture

**Status**: Ready for Claude Code implementation  
**Dependency**: Phase 2c completed, Phases 1-2 in place  
**Estimated Time**: 4-5 hours (split into sub-phases if needed)

---

## Objective

Refactor engine.py to support two-tier event system:
1. **Tier 1 (BaseAdventureHandlers)**: Generic handlers that read flags
2. **Tier 2 (custom handlers.py)**: Per-adventure custom logic

Transform from hardcoded behavior to flag-based + hook-based system.

---

## Phase 3 Structure (Sub-Phases)

| Sub-Phase | What | Time |
|-----------|------|------|
| **3.1** | Create base_handlers.py | 1.5 hrs |
| **3.2** | Refactor engine.py hooks | 2 hrs |
| **3.3** | Update cmd_talk() to use handlers | 1 hr |
| **3.4** | Test with Beginner's Cave | 0.5 hrs |

---

## Phase 3.1: Create base_handlers.py

**Create NEW file**: `core/base_handlers.py`

```python
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
    
    # ──────────────────────────────────────────────────────────────────
    # CORE HOOKS
    # ──────────────────────────────────────────────────────────────────
    
    def on_game_start(self) -> None:
        """Called when adventure starts."""
        self.engine.game_data = {}
    
    def on_enter_room(self, room_id: int) -> None:
        """Called when player enters a room."""
        room = self.engine.world.get_room(room_id)
        if not room:
            return
        
        flags = room.flags or {}
        
        # Check win condition
        if flags.get('is_win_room'):
            if self._check_win_condition(flags.get('win_condition')):
                dialogue = flags.get('win_dialogue', 'You have won!')
                print(f"\n{dialogue}")
                self.engine.exit_code = 1  # Win signal
                self.engine.running = False
        
        # Trigger room events
        if flags.get('triggers_event'):
            event_id = flags['triggers_event']
            self.engine.trigger_event(event_id)
    
    def on_talk_to_npc(self, npc_name: str) -> None:
        """Called when player talks to NPC."""
        room = self.engine.world.get_room(self.engine.player.room_id)
        npc = self.engine.world.find_monster_by_name(npc_name, 
                                                     self.engine.world.monsters_in_room(room.id))
        if not npc:
            return
        
        # Show dialogue
        if npc.dialogue:
            print(f"\n{npc.name} says: \"{npc.dialogue}\"")
        
        # Check follower recruitment
        flags = npc.flags or {}
        if flags.get('is_follower'):
            can_recruit, dialogue = self._check_follower_conditions(npc, flags)
            if can_recruit:
                self.engine.player.followers.append(npc)
                print(f"{dialogue}")
                return
        
        # Check healing service (legacy support)
        if npc.heal_amount > 0 and npc.heal_cost > 0:
            self._offer_healing(npc)
    
    def on_use_item(self, artifact_name: str, target: Optional[str] = None) -> bool:
        """Called when player uses an item. Returns True if handled."""
        room = self.engine.world.get_room(self.engine.player.room_id)
        pool = self.engine.world.artifacts_in_room(room.id) + \
               self.engine.world.artifacts_carried()
        
        artifact = self.engine.world.find_artifact_by_name(artifact_name, pool)
        if not artifact:
            return False
        
        flags = artifact.flags or {}
        
        # Check if escape vehicle
        if flags.get('is_escape_vehicle'):
            dialogue = flags.get('escape_dialogue', "You escape!")
            print(dialogue)
            self.engine.exit_code = 3  # Escape signal
            self.engine.running = False
            return True
        
        # Check if triggers event
        if flags.get('triggers_event'):
            event_id = flags['triggers_event']
            self.engine.trigger_event(event_id)
            return True
        
        return False
    
    def on_monster_defeated(self, monster_id: int) -> None:
        """Called when a monster is defeated."""
        # Can be overridden by adventure handlers
        pass
    
    # ──────────────────────────────────────────────────────────────────
    # HELPER METHODS
    # ──────────────────────────────────────────────────────────────────
    
    def _check_follower_conditions(self, npc: dict, flags: dict) -> Tuple[bool, str]:
        """Check if NPC recruitment conditions are met."""
        follower_type = flags.get('follower_type')
        
        if follower_type == "quest":
            condition = flags.get('quest_condition')
            if self.engine.player.quest_flags.get(condition, False):
                return True, flags.get('follower_dialogue', 
                                      f"{npc['name']} joins you!")
        
        elif follower_type == "trade":
            required_item = flags.get('required_item')
            if self._player_has_item(required_item):
                return True, flags.get('follower_dialogue', 
                                      f"{npc['name']} joins you!")
        
        elif follower_type == "stat":
            required_stat = flags.get('required_stat')
            required_value = flags.get('required_stat_value', 10)
            player_stat = getattr(self.engine.player, required_stat, 0)
            if player_stat >= required_value:
                return True, flags.get('follower_dialogue', 
                                      f"{npc['name']} joins you!")
        
        elif follower_type == "chance":
            base_chance = flags.get('chance_base', 0.5)
            stat_mod = flags.get('stat_modifier')
            chance = base_chance
            if stat_mod:
                stat_value = getattr(self.engine.player, stat_mod, 0)
                # +1% per stat point
                chance += (stat_value * 0.01)
            
            if random.random() < chance:
                return True, flags.get('follower_dialogue', 
                                      f"{npc['name']} joins you!")
        
        elif follower_type == "combat":
            required_kills = flags.get('requires_kills', 5)
            if self.engine.player.combat_kills >= required_kills:
                return True, flags.get('follower_dialogue', 
                                      f"{npc['name']} joins you!")
        
        elif follower_type == "alignment":
            required_align = flags.get('requires_alignment', 'good')
            if self.engine.player.alignment == required_align:
                return True, flags.get('follower_dialogue', 
                                      f"{npc['name']} joins you!")
        
        return False, ""
    
    def _check_win_condition(self, condition_str: Optional[str]) -> bool:
        """Check if win condition is met."""
        if not condition_str:
            return False
        
        # Generic conditions
        if condition_str == "has_rescued_girl":
            return any(f.get('id') == 'girl' for f in self.engine.player.followers)
        
        # Add more generic conditions as needed...
        # Adventures can override for custom conditions
        
        return False
    
    def _player_has_item(self, item_name: str) -> bool:
        """Check if player carries an item by name."""
        carried = self.engine.world.artifacts_carried()
        return any(a.name.lower() == item_name.lower() for a in carried)
    
    def _offer_healing(self, npc: dict) -> None:
        """Offer healing service (legacy NPC mechanic)."""
        missing = self.engine.player.hp_max - self.engine.player.hp
        
        if missing <= 0:
            print(f"\n{npc['name']} says: \"You look healthy enough.\"")
            return
        
        cost = missing * npc.get('heal_cost', 1)
        print(f"\n{npc['name']} offers to heal {missing} HP "
              f"for {npc.get('heal_cost', 1)} gold/HP ({cost} gold total).")
        print(f"You have {self.engine.player.gold} gold.")
        
        answer = input("Accept? (y/n): ").strip().lower()
        if answer == "y":
            if self.engine.player.gold >= cost:
                self.engine.player.gold -= cost
                self.engine.player.hp = self.engine.player.hp_max
                print(f"{npc['name']} tends your wounds.")
                print(f"Gold remaining: {self.engine.player.gold}")
            else:
                print(f"Not enough gold. (Need {cost}, have {self.engine.player.gold})")
        else:
            print("You decline.")
    
    def trigger_event(self, event_id: str) -> None:
        """Trigger a named event (can be overridden by adventure)."""
        # Base implementation does nothing
        # Adventures override to handle specific events
        pass
```

---

## Phase 3.2: Refactor engine.py

**Modify engine.py __init__():**

```python
import importlib
from core.base_handlers import BaseAdventureHandlers

class Engine:
    def __init__(self, world: World, player: Player, adventure_path: str = None):
        self.world = world
        self.player = player
        self.adventure_path = adventure_path
        self.running = True
        self.exit_code = 0
        self.light_active = False
        self.game_data = {}  # Adventure-specific state
        
        # Initialize handlers (Tier 1: generic)
        self.base_handlers = BaseAdventureHandlers(self)
        
        # Load adventure handlers (Tier 2: custom)
        self.custom_handlers = {}
        if adventure_path:
            self._load_adventure_handlers(adventure_path)
    
    def _load_adventure_handlers(self, adventure_path: str) -> None:
        """Dynamically load adventure-specific handlers if they exist."""
        try:
            adventure_name = adventure_path.rstrip('/').split('/')[-1]
            module = importlib.import_module(f"adventures.{adventure_name}.handlers")
            
            # Get the handlers dict or handlers class
            if hasattr(module, 'HANDLERS'):
                self.custom_handlers = getattr(module, 'HANDLERS')
            elif hasattr(module, 'AdventureHandlers'):
                # Could also use a class-based approach
                handlers_class = getattr(module, 'AdventureHandlers')
                self.custom_handlers = handlers_class(self)
        except ImportError:
            # No custom handlers — that's OK, use generic only
            self.custom_handlers = {}
        except Exception as e:
            print(f"Warning: Could not load adventure handlers: {e}")
            self.custom_handlers = {}
    
    def trigger_event(self, event_id: str) -> None:
        """Trigger a named event."""
        # First check custom handlers
        if isinstance(self.custom_handlers, dict):
            handler = self.custom_handlers.get(event_id)
            if handler and callable(handler):
                handler(self)
                return
        
        # Fall back to custom class method or base method
        if hasattr(self.custom_handlers, event_id):
            method = getattr(self.custom_handlers, event_id)
            if callable(method):
                method(self)
```

**Add these hook-calling methods to Engine:**

```python
    def call_hook(self, hook_name: str, *args, **kwargs):
        """Call a hook, checking custom handlers first, then base handlers."""
        # Custom handlers take priority
        if isinstance(self.custom_handlers, dict):
            handler = self.custom_handlers.get(hook_name)
            if handler and callable(handler):
                return handler(self, *args, **kwargs)
        elif hasattr(self.custom_handlers, hook_name):
            method = getattr(self.custom_handlers, hook_name)
            if callable(method):
                return method(self, *args, **kwargs)
        
        # Fall back to base handlers
        if hasattr(self.base_handlers, hook_name):
            method = getattr(self.base_handlers, hook_name)
            if callable(method):
                return method(*args, **kwargs)
    
    def on_game_start(self):
        self.call_hook('on_game_start')
    
    def on_enter_room(self, room_id: int):
        self.call_hook('on_enter_room', room_id)
    
    def on_talk_to_npc(self, npc_name: str):
        self.call_hook('on_talk_to_npc', npc_name)
    
    def on_use_item(self, artifact_name: str, target: str = None) -> bool:
        result = self.call_hook('on_use_item', artifact_name, target)
        return result if result is not None else False
    
    def on_monster_defeated(self, monster_id: int):
        self.call_hook('on_monster_defeated', monster_id)
```

---

## Phase 3.3: Update cmd_talk()

**Replace current cmd_talk() with:**

```python
def cmd_talk(self, noun: str) -> None:
    if not noun:
        print(c(C.ERROR, "Talk to whom?"))
        return

    room = self.world.get_room(self.player.room_id)
    npc = self.world.find_monster_by_name(noun, self.world.monsters_in_room(room.id))

    if npc is None:
        print(c(C.ERROR, f"There is no {noun} here to talk to."))
        return

    if npc.attitude == Attitude.HOSTILE:
        print(c(C.WARN, f"The {npc.name} doesn't seem interested in conversation."))
        return

    # Call the handler — it handles dialogue, recruitment, healing, etc.
    self.on_talk_to_npc(npc.name)
    
    self._tick_shield()
    self.monster_round()
```

---

## Phase 3.4: Update cmd_go() to call hook

**In cmd_go(), after moving to new room:**

```python
    # ... existing movement code ...
    
    self.player.room_id = dest_id
    self.describe_room()
    
    # Call hook for room entry
    self.on_enter_room(dest_id)
    
    self.monster_round()
```

---

## Phase 3.5: Update cmd_attack() to track kills

**In cmd_attack(), after monster is defeated:**

```python
    # ... existing combat code ...
    
    if monster.hp <= 0:
        # Mark quest completion if needed
        self.player.combat_kills += 1
        
        # Call hook for monster defeat
        self.on_monster_defeated(monster.id)
        
        # ... rest of defeat logic ...
```

---

## Testing Checklist

- [ ] Create/view base_handlers.py
- [ ] Add imports to engine.py
- [ ] Add handler loading to __init__()
- [ ] Add hook-calling methods
- [ ] Update cmd_talk(), cmd_go(), cmd_attack()
- [ ] Test existing game works (no custom handlers)
- [ ] Test with Beginner's Cave (should work unchanged)
- [ ] Verify flags are being read correctly
- [ ] Verify hooks are being called

---

## Sample Adventure handlers.py (For Testing)

After Phase 3, verify you can create **adventures/001-beginners-cave/handlers.py**:

```python
"""
Beginner's Cave - Custom Adventure Handlers

Examples of adventure-specific custom logic.
"""

HANDLERS = {}

def on_game_start(engine):
    """Initialize adventure state."""
    engine.game_data['secret_revealed'] = False
    print("Welcome to the Beginner's Cave!")

def on_defeat_monster(engine, monster_id: int):
    """Handle monster defeats."""
    if monster_id == 3:  # Evil priest ID
        # Mark quest complete
        engine.player.quest_flags['rescued_from_priest'] = True
        print("\nThe priest falls! The girl is free!")

def on_enter_room(engine, room_id: int):
    """Handle room entry."""
    if room_id == 5:  # Secret corridor
        if not engine.game_data.get('secret_revealed'):
            print("\nYou discover a hidden passage!")
            engine.game_data['secret_revealed'] = True

# Register handlers
HANDLERS['on_game_start'] = on_game_start
HANDLERS['on_defeat_monster'] = on_defeat_monster
HANDLERS['on_enter_room'] = on_enter_room
```

---

## Claude Code Session Start

```
I'm implementing Phase 3: Engine Refactoring with Handler Architecture for Eamon Redux.

PHASE 3: Engine Refactoring with Handler Architecture

Reference documents:
- PHASE_3_ENGINE_REFACTORING.md (complete)
- INTEGRATED_FLAG_HANDLER_ARCHITECTURE.md (architecture overview)

Current situation:
- Phases 1-2c completed ✅
- base_handlers.py needs to be created
- engine.py needs hook system refactoring
- cmd_talk(), cmd_go(), cmd_attack() need updating

Deliverables:
1. Create core/base_handlers.py (generic handlers reading flags)
2. Refactor engine.py to support hooks and dynamic handler loading
3. Update cmd_talk() to use on_talk_to_npc hook
4. Update cmd_go() to use on_enter_room hook
5. Update cmd_attack() to use on_monster_defeated hook
6. Test with existing game (no custom handlers)

Repository: ~/git/Eamon/eamon-redux/

Let's start:
1. Create base_handlers.py from the code above
2. Then modify engine.py to add handler system

Proceed with creating base_handlers.py first.
```

---

**After Phase 3**: Run full game test with Beginner's Cave  
**Next**: Phase 4 - Win condition system  
**Then**: Phase 5 - Testing & Polish
