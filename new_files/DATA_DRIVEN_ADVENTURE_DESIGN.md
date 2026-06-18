# Eamon Redux — Data-Driven Adventure Design System

**Design Date**: June 18, 2026  
**Status**: Architecture Phase  
**Approach**: Flags & Metadata (No Hardcoding)

---

## Core Principle

Instead of hardcoding adventure-specific logic, use **metadata flags** on objects. The designer.py tool allows creators to set flags, and the engine reads those flags to determine behavior.

**This means:**
- Girl to rescue? → Set flag on NPC: `"is_rescueable": true`
- Hermit to befriend? → Set flag: `"is_follower": true`
- Boat for escape? → Set flag on artifact: `"is_escape_vehicle": true`
- Priest is evil? → Set flag on NPC: `"is_boss": true`

No code changes needed between adventures. Just different flag configurations.

---

## Flag System: Object Metadata

### **NPC/Monster Flags**

```json
{
  "id": 1,
  "name": "The Girl",
  "description": "A young woman in distress",
  "hp": 15,
  "strength": 8,
  
  "flags": {
    "is_follower": true,
    "follower_type": "quest",
    "quest_condition": "rescued_from_evil_priest",
    "follower_dialogue": "Thank you! I'll follow you!",
    "can_fight": false,
    "can_die": false
  }
}
```

### **NPC Flag Types:**

| Flag | Type | Purpose | Example |
|------|------|---------|---------|
| `is_follower` | bool | Can be recruited as follower | true |
| `follower_type` | string | Condition type | "quest", "trade", "chance", "stat" |
| `quest_condition` | string | Quest flag needed | "rescued_from_priest" |
| `required_item` | string | Item needed to follow | "silver_amulet" |
| `required_stat` | string | Stat needed | "charisma" |
| `required_stat_value` | int | Minimum stat value | 15 |
| `chance_base` | float | Random chance 0-1 | 0.5 |
| `is_boss` | bool | Story-critical NPC | true |
| `is_questgiver` | bool | Gives quests | true |
| `quest_id` | string | Quest they give | "rescue_girl" |
| `follower_combat_help` | bool | Helps in combat | true |
| `can_die` | bool | Can be killed | true/false |
| `is_invulnerable` | bool | Can't be killed | false |

---

## **Artifact/Item Flags**

```json
{
  "id": 5,
  "name": "Silver Amulet",
  "description": "A glowing silver amulet",
  "value": 50,
  
  "flags": {
    "is_tradeable": true,
    "trade_npc": "henrich",
    "trade_dialogue": "Ah! The amulet! I'll join you!",
    "is_escape_vehicle": false,
    "is_quest_item": true,
    "quest_id": "amulet_for_henrich",
    "triggers_event": "unlock_secret_door",
    "can_use": true
  }
}
```

### **Artifact Flag Types:**

| Flag | Type | Purpose | Example |
|------|------|---------|---------|
| `is_tradeable` | bool | Can trade to NPC | true |
| `trade_npc` | string | Which NPC | "henrich" |
| `is_escape_vehicle` | bool | Allows escape | true |
| `escape_dialogue` | string | Escape message | "You board the boat..." |
| `is_quest_item` | bool | Needed for quest | true |
| `quest_id` | string | Which quest | "find_amulet" |
| `triggers_event` | string | Event triggered | "open_secret_door" |
| `can_use` | bool | Can use/consume | true |
| `use_dialogue` | string | Use message | "You drink the potion..." |
| `can_give` | bool | Can give away | true |

---

## **Room Flags**

```json
{
  "id": 10,
  "name": "The Exit",
  "description": "You see a way out!",
  "exits": {"up": 1},
  
  "flags": {
    "is_exit": true,
    "is_win_room": true,
    "win_condition": "has_rescued_girl",
    "win_dialogue": "You've escaped with the girl! You've won!"
  }
}
```

### **Room Flag Types:**

| Flag | Type | Purpose | Example |
|------|------|---------|---------|
| `is_exit` | bool | Way out | true |
| `is_win_room` | bool | Victory location | true |
| `win_condition` | string | What's needed | "has_rescued_girl" |
| `is_start_room` | bool | Starting location | true |
| `is_boss_room` | bool | Final battle | true |
| `triggers_event` | string | Event on enter | "encounter_boss" |

---

## Designer.py Interface

The designer tool allows adventure creators to **set these flags without coding**:

```
$ python designer.py

=== Eamon Adventure Designer ===

1. Create New Adventure
2. Edit Existing Adventure
3. Edit NPCs
4. Edit Items
5. Edit Rooms
6. Set Flags
7. Test Adventure

> 3

=== Edit NPCs ===

1. The Girl (id: 1)
2. Evil Priest (id: 2)
3. Henrich (id: 3)

> 1

=== Editing: The Girl ===

Basic Info:
  Name: The Girl
  Description: A young woman in distress
  HP: 15
  
Flags:
  [✓] is_follower: true
  [✓] quest_condition: rescued_from_evil_priest
  [ ] is_boss
  [ ] can_die: false
  [ ] is_questgiver
  
  Save? (y/n): y
```

---

## Generic Event Handler System

Instead of adventure-specific code, one **generic event handler** reads the flags:

### **adventures/<name>/event_handlers.py**

```python
class AdventureEventHandlers:
    """
    Generic event handler that works for ANY adventure.
    Behavior defined by flags in rooms.json, artifacts.json, monsters.json
    """
    
    def __init__(self, engine, adventure_data):
        self.engine = engine
        self.adventure = adventure_data
        self.npcs = {m['id']: m for m in adventure_data['monsters']}
        self.items = {a['id']: a for a in adventure_data['artifacts']}
        self.rooms = {r['id']: r for r in adventure_data['rooms']}
    
    def on_talk_to_npc(self, engine, npc_name, player):
        """Talk to NPC - check flags to determine behavior"""
        # Find NPC by name
        npc = self._find_npc_by_name(npc_name)
        if not npc:
            print(f"There is no '{npc_name}' here.")
            return False
        
        # Check if this NPC is a follower
        if npc.get('flags', {}).get('is_follower'):
            return self._handle_follower_recruitment(npc, player)
        
        # Check if this NPC is a quest giver
        if npc.get('flags', {}).get('is_questgiver'):
            quest_id = npc.get('flags', {}).get('quest_id')
            print(f"This NPC gives quest: {quest_id}")
            return True
        
        # Default: NPC doesn't respond
        print(f"{npc['name']} doesn't respond.")
        return False
    
    def _handle_follower_recruitment(self, npc, player):
        """Generic follower recruitment based on flags"""
        flags = npc.get('flags', {})
        follower_type = flags.get('follower_type')
        
        # Quest-based
        if follower_type == "quest":
            condition = flags.get('quest_condition')
            if player.quest_flags.get(condition, False):
                dialogue = flags.get('follower_dialogue', f"{npc['name']} joins you!")
                print(dialogue)
                self._add_follower(npc, player)
                return True
            return False
        
        # Trade-based
        elif follower_type == "trade":
            required_item = flags.get('required_item')
            if self._player_has_item(player, required_item):
                dialogue = flags.get('follower_dialogue', f"{npc['name']} joins you!")
                print(dialogue)
                self._remove_item(player, required_item)
                self._add_follower(npc, player)
                return True
            print(f"You need to give them {required_item}.")
            return False
        
        # Stat-based
        elif follower_type == "stat":
            required_stat = flags.get('required_stat')
            required_value = flags.get('required_stat_value', 10)
            player_stat = getattr(player, required_stat, 0)
            if player_stat >= required_value:
                dialogue = flags.get('follower_dialogue', f"{npc['name']} joins you!")
                print(dialogue)
                self._add_follower(npc, player)
                return True
            print(f"You need {required_stat} >= {required_value}.")
            return False
        
        # Chance-based
        elif follower_type == "chance":
            chance = flags.get('chance_base', 0.5)
            if random.random() < chance:
                dialogue = flags.get('follower_dialogue', f"{npc['name']} joins you!")
                print(dialogue)
                self._add_follower(npc, player)
                return True
            print(f"{npc['name']} declines.")
            return False
        
        return False
    
    def on_use_item(self, engine, artifact_name, target, player):
        """Use item - check flags for special behavior"""
        item = self._find_item_by_name(artifact_name)
        if not item:
            return False
        
        flags = item.get('flags', {})
        
        # Escape vehicle
        if flags.get('is_escape_vehicle'):
            dialogue = flags.get('escape_dialogue', "You escape!")
            print(dialogue)
            return "escape"  # Signal escape
        
        # Quest item
        if flags.get('is_quest_item'):
            quest_id = flags.get('quest_id')
            player.quest_flags[quest_id] = True
            print(f"Quest complete: {quest_id}")
            return True
        
        # Generic use
        if flags.get('can_use'):
            dialogue = flags.get('use_dialogue', f"You use the {item['name']}.")
            print(dialogue)
            return True
        
        return False
    
    def on_enter_room(self, engine, room_id, player):
        """Enter room - check flags for events"""
        room = self.rooms.get(room_id)
        if not room:
            return False
        
        flags = room.get('flags', {})
        
        # Check win condition
        if flags.get('is_win_room'):
            if self._check_win_condition(flags.get('win_condition'), player):
                dialogue = flags.get('win_dialogue', "You've won!")
                print(dialogue)
                return "win"
        
        # Trigger event
        if flags.get('triggers_event'):
            event_id = flags['triggers_event']
            print(f"Event triggered: {event_id}")
        
        return False
    
    def _check_win_condition(self, condition_string, player):
        """Check if win condition is met"""
        # Parse condition string: "has_rescued_girl"
        if condition_string == "has_rescued_girl":
            return any(f.get('id') == 'girl' for f in player.followers)
        
        # Add more conditions as needed...
        return False
    
    def _find_npc_by_name(self, name):
        """Find NPC by name (case-insensitive)"""
        name_lower = name.lower()
        for npc_id, npc in self.npcs.items():
            if npc['name'].lower() == name_lower:
                return npc
        return None
    
    def _find_item_by_name(self, name):
        """Find item by name"""
        name_lower = name.lower()
        for item_id, item in self.items.items():
            if item['name'].lower() == name_lower:
                return item
        return None
    
    def _add_follower(self, npc, player):
        """Add NPC as follower"""
        if npc not in player.followers:
            player.followers.append(npc)
    
    def _player_has_item(self, player, item_name):
        """Check if player has item"""
        # Simplified - check actual artifact logic
        return any(a.name.lower() == item_name.lower() 
                  for a in player.inventory)
    
    def _remove_item(self, player, item_name):
        """Remove item from player inventory"""
        player.inventory = [a for a in player.inventory 
                           if a.name.lower() != item_name.lower()]
```

---

## Designer.py Features

### **What the Designer Tool Does:**

1. **Create/Edit Adventure**
   - Set adventure name, intro, win conditions
   - Create rooms, NPCs, items

2. **Edit NPCs**
   - Name, description, stats
   - **Set flags**: is_follower, quest_condition, required_item, etc.
   - No coding required

3. **Edit Items**
   - Name, description, value
   - **Set flags**: is_tradeable, is_escape_vehicle, triggers_event, etc.

4. **Edit Rooms**
   - Connections, descriptions
   - **Set flags**: is_exit, is_win_room, win_condition, etc.

5. **Auto-Generate Event Handlers**
   - Based on flags, creates basic event_handlers.py
   - Adventures with no special mechanics = no custom code needed

---

## Examples: Same Engine, Different Adventures

### **Adventure A: Rescue Quest**
```json
// NPC flags:
{"is_follower": true, "quest_condition": "rescued", ...}

// Room flags:
{"is_win_room": true, "win_condition": "has_rescued_girl", ...}

// Item flags: none special

// Engine behavior: Generic handler reads flags
//                  Girl follows when rescued
//                  Win at exit with girl
```

### **Adventure B: Trading Quest**
```json
// NPC flags:
{"is_follower": true, "follower_type": "trade", "required_item": "amulet", ...}

// Room flags: none special

// Item flags:
{"is_tradeable": true, "trade_npc": "henrich", ...}

// Engine behavior: Generic handler reads flags
//                  Give item → NPC follows
//                  No custom code needed
```

### **Adventure C: Escape Mechanics**
```json
// NPC flags: none special

// Room flags:
{"is_win_room": true, "win_condition": "escaped", ...}

// Item flags:
{"is_escape_vehicle": true, "escape_dialogue": "You board the boat...", ...}

// Engine behavior: Generic handler reads flags
//                  Use boat → escape signal
//                  Win at exit after escape
```

---

## No More Hardcoding!

**Old Way (Hardcoded):**
```python
def on_talk_to_npc(self, engine, npc_name, player):
    if npc_name == "girl":        # HARDCODED
        # Special girl logic
    elif npc_name == "henrich":   # HARDCODED
        # Special henrich logic
    elif npc_name == "hermit":    # HARDCODED
        # Special hermit logic
```

**New Way (Flag-Based):**
```python
def on_talk_to_npc(self, engine, npc_name, player):
    npc = self._find_npc_by_name(npc_name)
    if npc.get('flags', {}).get('is_follower'):
        return self._handle_follower_recruitment(npc, player)
    # Works for ANY follower, ANY adventure
```

---

## Advantages

✅ **Zero hardcoding** per adventure  
✅ **Designer tool** makes it visual/easy  
✅ **Reusable** - same engine for all adventures  
✅ **Data-driven** - behavior in JSON, not code  
✅ **Extensible** - add new flags = new behaviors  
✅ **Testable** - each flag type tested once  
✅ **Non-programmers** can design adventures  

---

## Implementation Path

1. **Design flag schema** (what flags exist)
2. **Implement generic event handlers** (reads flags)
3. **Build designer.py** (sets flags)
4. **Test with Beginner's Cave** (set flags, verify behavior)
5. **Expand to other adventures** (different flag combinations)

---

**Status**: Ready for implementation  
**Complexity**: Medium-High (but very powerful)  
**Payoff**: Infinite adventure flexibility
