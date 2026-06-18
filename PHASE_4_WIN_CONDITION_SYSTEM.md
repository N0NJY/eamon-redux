# PHASE 4: Win Condition System

**Status**: Ready for Claude Code implementation  
**Dependency**: Phases 1-3 completed  
**Estimated Time**: 1-2 hours

---

## Objective

Make win condition checking **generic and flag-based** instead of hardcoded.

Currently: Engine checks for specific room IDs  
After Phase 4: Engine reads `win_condition` flags from rooms and evaluates them dynamically

---

## Current State

**engine.py _check_win()** (somewhere around line 1045):
```python
def _check_win(self) -> bool:
    """Hardcoded win condition check."""
    # Specific to each adventure
    # This is NOT flexible
```

**What we need:**
- Generic win condition evaluation
- Support for multiple condition types
- Extensible via adventure handlers

---

## Win Condition Types

Based on flags in adventure.json, support these types:

### **Type 1: kill_monster**
```json
"win_condition": "kill_monster:5"
// Player must defeat monster with id=5
```

### **Type 2: kill_all**
```json
"win_condition": "kill_all"
// Player must defeat all monsters in adventure
```

### **Type 3: reach_room**
```json
"win_condition": "reach_room:10"
// Player must reach room with id=10
```

### **Type 4: carry_artifact**
```json
"win_condition": "carry_artifact:7"
// Player must carry artifact with id=7
```

### **Type 5: has_rescued_girl** (Custom)
```json
"win_condition": "has_rescued_girl"
// Player must have girl follower (set by base_handlers)
```

### **Type 6: quest_completed**
```json
"win_condition": "quest_completed:main_quest"
// Specific quest flag must be set
```

---

## Implementation

### **Part 1: Add to BaseAdventureHandlers**

**In core/base_handlers.py**, update `_check_win_condition()`:

```python
def _check_win_condition(self, condition_str: Optional[str]) -> bool:
    """
    Evaluate generic win conditions.
    Format: "type:param" or "type"
    
    Examples:
    - "kill_monster:5" → Must kill monster id=5
    - "kill_all" → Must kill all monsters
    - "reach_room:10" → Must reach room id=10
    - "carry_artifact:7" → Must carry artifact id=7
    - "has_rescued_girl" → Must have girl follower
    - "quest_completed:main_quest" → Must complete quest
    """
    if not condition_str:
        return False
    
    # Parse condition: "type:param"
    parts = condition_str.split(":", 1)
    cond_type = parts[0].strip()
    param = parts[1].strip() if len(parts) > 1 else None
    
    # ─────────────────────────────────────────────────────────────
    # kill_monster:ID
    # ─────────────────────────────────────────────────────────────
    if cond_type == "kill_monster" and param:
        try:
            monster_id = int(param)
            monster = self.engine.world.monsters.get(monster_id)
            if monster:
                return monster.hp <= 0
        except ValueError:
            pass
    
    # ─────────────────────────────────────────────────────────────
    # kill_all
    # ─────────────────────────────────────────────────────────────
    elif cond_type == "kill_all":
        # All monsters must be dead
        all_monsters = self.engine.world.monsters.values()
        return all(m.hp <= 0 for m in all_monsters)
    
    # ─────────────────────────────────────────────────────────────
    # reach_room:ID
    # ─────────────────────────────────────────────────────────────
    elif cond_type == "reach_room" and param:
        try:
            room_id = int(param)
            return self.engine.player.room_id == room_id
        except ValueError:
            pass
    
    # ─────────────────────────────────────────────────────────────
    # carry_artifact:ID
    # ─────────────────────────────────────────────────────────────
    elif cond_type == "carry_artifact" and param:
        try:
            artifact_id = int(param)
            carried = self.engine.world.artifacts_carried()
            return any(a.id == artifact_id for a in carried)
        except ValueError:
            pass
    
    # ─────────────────────────────────────────────────────────────
    # has_rescued_girl (custom example)
    # ─────────────────────────────────────────────────────────────
    elif cond_type == "has_rescued_girl":
        return any(f.get('id') == 'girl' for f in self.engine.player.followers)
    
    # ─────────────────────────────────────────────────────────────
    # quest_completed:QUEST_ID
    # ─────────────────────────────────────────────────────────────
    elif cond_type == "quest_completed" and param:
        return self.engine.player.quest_flags.get(param, False)
    
    # ─────────────────────────────────────────────────────────────
    # Unknown type
    # ─────────────────────────────────────────────────────────────
    return False
```

---

### **Part 2: Update on_enter_room() in BaseAdventureHandlers**

Already done in Phase 3, but verify it calls `_check_win_condition()`:

```python
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
            return  # Stop further processing
    
    # Trigger room events
    if flags.get('triggers_event'):
        event_id = flags['triggers_event']
        self.engine.trigger_event(event_id)
```

---

### **Part 3: Allow Adventure Handlers to Override**

In **adventures/001-beginners-cave/handlers.py**, adventure authors can override:

```python
class BeginnersCaveHandlers(BaseAdventureHandlers):
    """Beginner's Cave custom handlers."""
    
    def _check_win_condition(self, condition_str: str) -> bool:
        """Override to handle adventure-specific conditions."""
        
        # Custom logic here
        if condition_str == "secret_win_condition":
            return self.engine.game_data.get('secret_achieved', False)
        
        # Fall back to generic conditions
        return super()._check_win_condition(condition_str)
```

---

## Testing Checklist

- [ ] Update BaseAdventureHandlers._check_win_condition() with all types
- [ ] Test kill_monster:ID
- [ ] Test kill_all
- [ ] Test reach_room:ID
- [ ] Test carry_artifact:ID
- [ ] Test has_rescued_girl (custom)
- [ ] Test quest_completed:QUEST_ID
- [ ] Verify on_enter_room() calls _check_win_condition()
- [ ] Test with Beginner's Cave
- [ ] Test adventure handler override works

---

## Example: Beginner's Cave Setup

In **adventures/001-beginners-cave/adventure.json**, the main win room should have:

```json
{
  "id": 10,
  "name": "The Exit",
  "description": "You see daylight ahead!",
  "exits": {},
  "is_dark": false,
  "flags": {
    "is_exit": true,
    "is_win_room": true,
    "win_condition": "has_rescued_girl",
    "win_dialogue": "You escape with the girl! You have won the Beginner's Cave!"
  }
}
```

When player enters room 10:
1. Engine calls `on_enter_room(10)`
2. BaseAdventureHandlers checks `is_win_room: true`
3. Calls `_check_win_condition("has_rescued_girl")`
4. Checks if any follower has id='girl'
5. If true, prints victory message and exits

---

## Claude Code Session Start

```
I'm implementing Phase 4: Generic Win Condition System for Eamon Redux.

PHASE 4: Win Condition System

Current situation:
- Phases 1-3 completed ✅
- base_handlers.py exists with generic handlers
- on_enter_room() calls _check_win_condition()
- But _check_win_condition() only supports one condition type

Deliverable:
Extend _check_win_condition() to support multiple condition types:
- kill_monster:ID
- kill_all
- reach_room:ID
- carry_artifact:ID
- has_rescued_girl
- quest_completed:QUEST_ID

Repository: ~/git/Eamon/eamon-redux/

Steps:
1. View core/base_handlers.py _check_win_condition() method
2. I'll provide the complete implementation
3. Apply changes
4. Test: Load Beginner's Cave, verify win condition works

Let's start: View the current _check_win_condition() method.
```

---

**After Phase 4**: Full win condition system works  
**Next**: Phase 5 - Testing & Polish  
**Then**: Done! 🎉
