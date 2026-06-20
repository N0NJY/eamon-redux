# Eamon Redux — Adventure-Specific Mechanics & Event System

**Issue Date**: June 18, 2026  
**Status**: Design Phase  
**Priority**: HIGH (blocks proper NPC/quest implementation)

---

## Problems Identified

### 1. **NPC Followers Not Working**
- NPCs like Henrich, hermits, rescued girls don't follow player
- No "follower" system in engine
- Followers should move with player, appear in room descriptions
- Example: Rescue girl → she follows → reach exit → WIN

### 2. **Talk Command Does Nothing**
- `talk to <npc>` registered but not dispatched (Bug #7)
- No dialogue system implemented
- Adventure-specific dialogue needs to vary per adventure
- Examples:
  - Henrich helps with guidance
  - Hermit assists in combat
  - Girl requests rescue

### 3. **Special Mechanics Not Implemented**
- Boat in "Pirate's Den" allows escape (adventure-specific exit)
- No system for adventure-defined special commands or items
- Each adventure may have unique interactions

### 4. **Dead Body Display Bug** ⚠️
- Dead bodies appear in rooms where NPCs are still alive
- Should ONLY appear after NPC is killed
- Indicates monster "is_dead" state not being checked on room entry
- Likely issue in room description generation

---

## Current Architecture Issues

### **Engine.py `look()` function:**
```python
def look(self):
    # Show room description
    # Show monsters/NPCs - BUT: Are we filtering dead ones?
    # Show items
    # Show exits
```

**Problem**: When displaying monsters, code probably doesn't check if monster is dead.

### **Suggested Fix (Investigation needed):**
```python
def look(self):
    # ... room description ...
    
    # Show LIVING monsters only
    living_monsters = [m for m in self.world.monsters_in_room(self.player.room_id) 
                       if m.hp > 0]  # Only show alive NPCs
    for m in living_monsters:
        print(f"A {m.name} is here.")
    
    # Show dead bodies ONLY if they were killed
    dead_bodies = [m for m in self.world.monsters_in_room(self.player.room_id) 
                   if m.hp <= 0]
    for m in dead_bodies:
        print(f"The dead body of {m.name} lies here.")
```

---

## Solution Architecture: Event Handler System

Similar to **Eamon Remastered**, each adventure needs its own event handlers file:

### **Directory Structure:**
```
adventures/001-beginners-cave/
├── rooms.json
├── artifacts.json
├── monsters.json
├── effects.json
└── event_handlers.py          # NEW: Adventure-specific handlers
```

### **Event Handler System (event_handlers.py):**

```python
"""
Event handlers for: The Beginner's Cave
Defines custom NPC behavior, dialogue, special mechanics
"""

class AdventureEventHandlers:
    """
    Called by engine at specific points in gameplay.
    Each method can override default behavior.
    """
    
    def on_talk_to_npc(self, engine, npc_name, player):
        """Handle 'talk to <npc>' command"""
        if npc_name.lower() == "henrich":
            print("Henrich says: 'Follow me, I know the way!'")
            # Add Henrich to player's followers
            player.followers.append(npc_name)
            return True
        
        elif npc_name.lower() == "girl":
            print("The girl says: 'Please help me escape this place!'")
            return True
        
        return False  # No handler found
    
    def on_pick_up_item(self, engine, artifact_name, player):
        """Handle picking up special items"""
        # Could be used for flags, special events, etc.
        return False
    
    def on_use_item(self, engine, artifact_name, target, player):
        """Handle 'use <item>' command - special mechanics"""
        if artifact_name.lower() == "boat":
            print("You board the boat and row away from the dungeon!")
            print("You've escaped to safety!")
            return "escape"  # Special exit code
        
        return False
    
    def on_attack_npc(self, engine, npc_name, player):
        """Handle attacking an NPC - consequences"""
        if npc_name.lower() == "girl":
            print("The girl screams! You monster!")
            # Could set flag that player is evil, lose XP, etc.
        return False
    
    def on_room_enter(self, engine, room_id, player):
        """Called when player enters a room"""
        # Could trigger room-specific events
        if room_id == 5:  # Special room
            print("You hear mysterious whispers...")
        return False
    
    def on_win_condition(self, engine, player):
        """Check if player has won (adventure-specific)"""
        # Beginner's Cave: Rescue the girl
        if "girl" in player.followers:
            print("The girl is safe! You've succeeded!")
            return True
        return False
```

---

## Implementation Plan

### **Phase 1: Core System** (High Priority)
- [ ] Add `followers` list to Player class
- [ ] Create `event_handlers.py` template
- [ ] Implement event handler loading in Engine
- [ ] Fix dead body display bug (filter by hp > 0)

### **Phase 2: NPC System** (High Priority)
- [ ] `on_talk_to_npc()` - dialogue
- [ ] `on_add_follower()` - add NPC to followers list
- [ ] Followers move with player
- [ ] Followers appear in `look()` output
- [ ] Example: Girl follower in Beginner's Cave

### **Phase 3: Special Mechanics** (Medium Priority)
- [ ] `on_use_item()` - boat escape, special interactions
- [ ] `on_enter_room()` - room-specific events
- [ ] `on_win_condition()` - adventure-defined win state
- [ ] Example: Boat in Pirate's Den

### **Phase 4: Advanced** (Low Priority)
- [ ] `on_attack_npc()` - NPC combat reactions
- [ ] Quest flags system
- [ ] NPC combat assistance (Hermit helps in battle)
- [ ] Dynamic NPC behavior

---

## Data Structure Changes Needed

### **Player class additions:**
```python
class Player:
    def __init__(self, ...):
        # ... existing code ...
        self.followers = []  # List of NPC names following player
        self.quest_flags = {}  # Adventure-specific flags
```

### **Monster class considerations:**
```python
class Monster:
    def __init__(self, ...):
        # ... existing code ...
        # Ensure hp field exists and is checked
        self.hp = hp
        
    def is_alive(self):
        """Check if monster is still alive"""
        return self.hp > 0
```

---

## Example: Beginner's Cave Implementation

### **Event Handlers:**
```python
def on_talk_to_npc(self, engine, npc_name, player):
    """The Beginner's Cave dialogue"""
    npc = npc_name.lower()
    
    if npc == "girl":
        print("The girl says: 'Please! Help me escape from this place!'")
        print("She looks frightened but hopeful.")
        return True
    
    elif npc == "henrich":
        print("Henrich nods wisely and agrees to guide you.")
        if "henrich" not in player.followers:
            player.followers.append("henrich")
            print("Henrich joins your party!")
        return True
    
    return False

def on_win_condition(self, engine, player):
    """Win: Rescue the girl and reach the exit"""
    if "girl" in player.followers:
        return True  # Victory!
    return False
```

### **Usage in Engine:**
```python
# In Engine.cmd_talk(noun):
if hasattr(self, 'event_handlers'):
    if self.event_handlers.on_talk_to_npc(self, noun, self.player):
        return  # Handler took care of it
    
# Fallback if no handler
print(f"The {noun} doesn't respond.")
```

---

## Questions for Discussion

1. **Dead Body Bug**: Should we filter monsters by `hp > 0` in `look()`? Or is there a flag we should check?

2. **Follower System**: Should followers auto-attack alongside player? Or just follow?

3. **Event Handler Loading**: Should we dynamically import from `adventures/<name>/event_handlers.py`?

4. **Win Conditions**: Should these be defined in:
   - Event handlers (current proposal)
   - Artifacts/room data (alternative)
   - Both?

5. **Dialogue System**: Should dialogue be:
   - Hardcoded in event_handlers.py (current proposal)
   - Pulled from JSON (more data-driven)

---

## Next Steps

1. **Identify dead body bug** - Check `look()` implementation
2. **Design event handler interface** - Decide on method signatures
3. **Test with Beginner's Cave** - Implement NPC follower system
4. **Document adventure creation guide** - How to write event_handlers.py

---

**Status**: Ready for implementation after bug fixes complete  
**Estimated Effort**: 6-8 hours (depending on complexity)  
**Complexity**: Medium (requires careful state management)
