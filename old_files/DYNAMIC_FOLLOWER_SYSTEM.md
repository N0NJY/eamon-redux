# Eamon Redux — Dynamic NPC Follower System

**Design Date**: June 18, 2026  
**Status**: Architecture Phase  
**Flexibility**: HIGH - Supports all follower types

---

## Overview

The follower system should be **dynamic and conditional**, not automatic. Different NPCs follow based on different conditions:

- **Girl**: Follows if RESCUED from evil priest (quest condition)
- **Henrich**: Follows if you GIVE him something (trade condition)
- **Hermit**: Might follow RANDOMLY or based on CHARISMA (chance + stat condition)
- **Dwarf**: Follows if you SOLVE his problem (quest condition)
- **Tavern Wench**: Follows if CHARISMA > X (stat-based condition)

---

## Follower Conditions (Types)

### **1. Quest Condition**
Follower joins after completing a task or quest objective.

```python
{
    "type": "quest",
    "condition": "rescued_girl",
    "dialogue": "Thank you! I'll follow you!"
}
```

### **2. Trade Condition**
Follower joins if you give them an item.

```python
{
    "type": "trade",
    "requires_item": "amulet",
    "dialogue": "This amulet! Yes, I'll join you!"
}
```

### **3. Stat Condition**
Follower joins if player has sufficient stat value.

```python
{
    "type": "stat",
    "stat": "charisma",
    "min_value": 15,
    "dialogue": "Your charm is irresistible. I'll follow you."
}
```

### **4. Chance Condition**
Follower joins randomly, optionally modified by a stat.

```python
{
    "type": "chance",
    "base_chance": 0.5,  # 50% base chance
    "stat_modifier": "charisma",  # +1% per charisma point
    "dialogue": "Sure, why not? I'll come with you."
}
```

### **5. Combat Condition**
Follower joins after you prove yourself in combat.

```python
{
    "type": "combat",
    "requires_kills": 3,
    "dialogue": "You're skilled! I'll join your party."
}
```

### **6. Alignment Condition**
Follower joins based on your actions/choices.

```python
{
    "type": "alignment",
    "requires_alignment": "good",  # or "evil", "neutral"
    "dialogue": "You're a force for good. I'll help you."
}
```

---

## Data Structure: Follower Metadata

Each adventure defines follower details in JSON:

### **adventures/001-beginners-cave/followers.json**

```json
{
  "followers": [
    {
      "id": "girl",
      "name": "The Girl",
      "description": "A young woman trapped by the evil priest",
      "conditions": [
        {
          "type": "quest",
          "condition": "rescued_from_priest",
          "dialogue": "Thank you! I owe you my life. I'll follow you!"
        }
      ],
      "stats": {
        "hp": 15,
        "strength": 8,
        "agility": 12,
        "hardiness": 10
      },
      "abilities": {
        "can_fight": false,
        "can_cast_spells": false
      }
    },
    {
      "id": "henrich",
      "name": "Henrich the Wise",
      "description": "An old wizard",
      "conditions": [
        {
          "type": "trade",
          "requires_item": "silver_amulet",
          "dialogue": "Ah, the amulet! Yes, I'll join your quest."
        }
      ],
      "stats": {
        "hp": 20,
        "strength": 10,
        "agility": 10,
        "hardiness": 12
      },
      "abilities": {
        "can_fight": true,
        "can_cast_spells": true
      }
    },
    {
      "id": "hermit",
      "name": "The Hermit",
      "description": "A mysterious hermit living in the woods",
      "conditions": [
        {
          "type": "chance",
          "base_chance": 0.5,
          "stat_modifier": "charisma",
          "dialogue": "Sure, I could use some company. Let's go."
        }
      ],
      "stats": {
        "hp": 25,
        "strength": 14,
        "agility": 11,
        "hardiness": 13
      },
      "abilities": {
        "can_fight": true,
        "can_cast_spells": false
      }
    }
  ]
}
```

---

## Implementation: Engine Changes

### **1. Player Class Enhancement**

```python
class Player:
    def __init__(self, character_data=None):
        # ... existing code ...
        self.followers = []          # List of Follower objects
        self.potential_followers = {}  # Cache of available followers
        self.quest_flags = {}        # Track quest completions
        self.trades_completed = []   # Track traded items
        self.combat_kills = 0        # Track combat performance
        self.alignment = "neutral"   # good, neutral, evil

class Follower:
    """Represents an NPC follower"""
    def __init__(self, follower_dict):
        self.id = follower_dict['id']
        self.name = follower_dict['name']
        self.hp = follower_dict['stats']['hp']
        self.strength = follower_dict['stats']['strength']
        self.agility = follower_dict['stats']['agility']
        self.hardiness = follower_dict['stats']['hardiness']
        self.can_fight = follower_dict['abilities']['can_fight']
        self.can_cast_spells = follower_dict['abilities']['can_cast_spells']
```

### **2. Event Handler: Check Follower Conditions**

```python
class AdventureEventHandlers:
    
    def __init__(self, engine):
        self.engine = engine
        self.follower_data = self.load_followers()  # Load from followers.json
    
    def load_followers(self):
        """Load follower definitions for this adventure"""
        try:
            with open('followers.json', 'r') as f:
                return json.load(f)
        except:
            return {"followers": []}
    
    def can_recruit_follower(self, npc_id, player, engine):
        """
        Check if player can recruit this NPC as a follower.
        Returns (can_recruit: bool, dialogue: str)
        """
        follower = next((f for f in self.follower_data['followers'] 
                        if f['id'] == npc_id), None)
        
        if not follower:
            return False, f"No follower data for {npc_id}"
        
        # Check each condition
        for condition in follower['conditions']:
            cond_type = condition.get('type')
            
            if cond_type == "quest":
                # Check if quest condition is met
                if player.quest_flags.get(condition['condition'], False):
                    return True, condition['dialogue']
            
            elif cond_type == "trade":
                # Check if player has required item
                item_id = condition['requires_item']
                if self.player_has_item(player, item_id):
                    player.trades_completed.append(item_id)
                    return True, condition['dialogue']
            
            elif cond_type == "stat":
                # Check if player has required stat
                stat = condition['stat']
                min_val = condition['min_value']
                player_stat = getattr(player, stat, 0)
                if player_stat >= min_val:
                    return True, condition['dialogue']
            
            elif cond_type == "chance":
                # Calculate chance based on stat modifier
                chance = condition['base_chance']
                if 'stat_modifier' in condition:
                    stat = condition['stat_modifier']
                    player_stat = getattr(player, stat, 0)
                    # Each point adds 1% chance (adjust as needed)
                    chance += (player_stat * 0.01)
                
                if random.random() < chance:
                    return True, condition['dialogue']
                else:
                    return False, f"The {npc_id} declines to follow you."
            
            elif cond_type == "combat":
                # Check if player has enough kills
                if player.combat_kills >= condition['requires_kills']:
                    return True, condition['dialogue']
            
            elif cond_type == "alignment":
                # Check player alignment
                if player.alignment == condition['requires_alignment']:
                    return True, condition['dialogue']
        
        # No conditions met
        return False, f"The {npc_id} won't follow you right now."
    
    def on_talk_to_npc(self, engine, npc_name, player):
        """Handle 'talk to <npc>' command"""
        can_follow, dialogue = self.can_recruit_follower(
            npc_name.lower(), 
            player, 
            engine
        )
        
        print(dialogue)
        
        if can_follow and npc_name.lower() not in [f.id for f in player.followers]:
            # Recruit the follower
            follower_data = next((f for f in self.follower_data['followers'] 
                                 if f['id'] == npc_name.lower()))
            follower = Follower(follower_data)
            player.followers.append(follower)
            print(f"{follower.name} has joined your party!")
        
        return True
```

### **3. Quest Flag Management**

```python
# In event handlers or engine:
def complete_quest(self, quest_id, player):
    """Mark a quest as completed"""
    player.quest_flags[quest_id] = True
    print(f"Quest completed: {quest_id}")

# Called when girl is rescued:
self.complete_quest("rescued_from_priest", player)

# Then when you talk to girl:
# Can now recruit because quest_flag is True
```

---

## Examples by Adventure Type

### **Example 1: Beginner's Cave - Quest-Based Follower**

```python
# When you defeat the evil priest:
def on_defeat_npc(engine, npc_name, player):
    if npc_name.lower() == "evil_priest":
        engine.event_handlers.complete_quest("rescued_from_priest", player)
        print("The girl is free!")
        return True
    return False

# When you talk to the girl:
# Condition: type=quest, condition=rescued_from_priest
# Result: Girl joins automatically
```

### **Example 2: Adventure with Trade-Based Follower**

```python
# Hermit won't follow... unless you give him something
conditions: [
    {
        "type": "trade",
        "requires_item": "flask_of_wine",
        "dialogue": "Ah! A fine wine! I'll join you!"
    }
]

# Player finds wine → gives to hermit → hermit follows
```

### **Example 3: Adventure with Charisma-Based Follower**

```python
# High charisma = more likely followers accept you
conditions: [
    {
        "type": "stat",
        "stat": "charisma",
        "min_value": 14,
        "dialogue": "Your charm is remarkable. I'll follow you."
    }
]

# Or random with charisma bonus:
conditions: [
    {
        "type": "chance",
        "base_chance": 0.3,
        "stat_modifier": "charisma",
        "dialogue": "Sure, I like your style. Let's go!"
    }
]
```

### **Example 4: Combat-Based Follower**

```python
# NPCs respect combat prowess
conditions: [
    {
        "type": "combat",
        "requires_kills": 5,
        "dialogue": "You're a warrior! I'll follow you!"
    }
]

# Track player kills:
def on_npc_death(engine, npc, player):
    player.combat_kills += 1
```

---

## Advantages of This Design

✅ **Flexible**: Any condition type can be added  
✅ **Data-Driven**: Adventure creators define conditions in JSON  
✅ **Reusable**: Same system works across all adventures  
✅ **Testable**: Each condition type can be tested independently  
✅ **Extensible**: Easy to add new condition types later  
✅ **Immersive**: NPCs join for believable reasons  
✅ **Replayable**: Different followers on different playthroughs  

---

## Questions & Considerations

1. **Follower Combat**: Should followers auto-attack? Defend player? Flee?

2. **Follower Loss**: Can followers die? Can player dismiss them?

3. **Max Followers**: Should there be a limit (e.g., max 3)?

4. **Follower Dialogue**: Should there be ongoing dialogue, or just recruitment?

5. **Charisma Scaling**: +1% per charisma point reasonable, or different formula?

6. **Alignment System**: Should player alignment change based on actions? (Kill innocents = evil, etc.)

---

## Next Steps

1. Implement Player follower tracking
2. Create followers.json template
3. Implement condition checking logic
4. Test with Beginner's Cave (girl follower)
5. Expand to other follower types as needed

---

**Status**: Ready for implementation after core bugs fixed  
**Complexity**: Medium (but very flexible)  
**Reusability**: High (works for all adventures)
