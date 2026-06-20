# Adventure Exit Rooms - Design Guide

## Overview

Adventures can now have natural exit points that lead back to the tavern. Instead of having to use a command or backtrack, players encounter an exit room that provides a natural, immersive way to return to town.

---

## How It Works

When a player moves to an exit with the special code `EXIT_TAVERN`, the engine detects it and smoothly returns them to the tavern:

```
  ──────────────────────────────────────────────────────────
  🏛️  You return to the town and the warmth of the Inn...
  ──────────────────────────────────────────────────────────
```

---

## Designing an Exit Room

### Example: Town Gate Room

**In your adventure.json, add a room like this:**

```json
{
  "id": 999,
  "title": "Town Gate",
  "description": "You stand at the weathered gate of the town. The ancient stone arch above is inscribed with symbols of protection. The path you came from winds back into the wilderness to the north. Ahead to the south, the familiar warmth of the Inn and Tavern beckons.",
  "first_visit": true,
  "exits": {
    "north": 100,
    "south": "EXIT_TAVERN"
  },
  "monsters": [],
  "artifacts": [],
  "locked_exits": {}
}
```

### Example: Forest Trail Exit

```json
{
  "id": 50,
  "title": "Forest Trail to Town",
  "description": "The forest path widens as it approaches civilization. Sunlight breaks through the trees ahead. To the north, the dark interior of the forest awaits. To the south, you can see the roofs of buildings and smell cooking smoke from the town.",
  "first_visit": true,
  "exits": {
    "north": 40,
    "south": "EXIT_TAVERN"
  },
  "monsters": [],
  "artifacts": [],
  "locked_exits": {}
}
```

### Example: Castle Exit Hall

```json
{
  "id": 75,
  "title": "Castle Entrance Hall",
  "description": "You stand in the grand entrance hall of the castle. Sunlight streams through the tall windows. The main hall stretches deeper into the castle to the north. The castle doors to the south stand open, revealing the road back to town.",
  "first_visit": true,
  "exits": {
    "north": 70,
    "south": "EXIT_TAVERN",
    "west": 76,
    "east": 77
  },
  "monsters": [],
  "artifacts": [],
  "locked_exits": {}
}
```

---

## Special Exit Codes

The engine recognizes these special exit codes:
- `EXIT_TAVERN`
- `RETURN_TO_TAVERN`
- `BACK_TO_TAVERN`

You can use any of these in the exits dictionary.

---

## Adventure Design Patterns

### Pattern 1: Linear Path with Exit

```
[Start] → [Challenge] → [Final Room] → [Town Gate] → TAVERN
           (combat)      (treasure)    (EXIT_TAVERN)
```

**JSON Structure:**
```json
{
  "id": 1,
  "title": "Starting Area",
  "exits": { "south": 2 }
},
{
  "id": 2,
  "title": "Final Challenge",
  "exits": { "south": 3, "north": 1 }
},
{
  "id": 3,
  "title": "Town Gate",
  "exits": { "north": 2, "south": "EXIT_TAVERN" }
}
```

### Pattern 2: Hub with Multiple Exits

```
                [Chamber 1]
                    |
[Start] → [Main Hall] ↔ [Chamber 2]
            |
       [Town Gate] → TAVERN
```

**JSON Structure:**
```json
{
  "id": 10,
  "title": "Main Hall",
  "exits": {
    "north": 11,
    "east": 12,
    "south": 20
  }
},
{
  "id": 20,
  "title": "Town Gate",
  "exits": {
    "north": 10,
    "south": "EXIT_TAVERN"
  }
}
```

### Pattern 3: Multiple Endings

```
[Start] → [Crossroads] → [Path A] → [Victory Room] → [Town Gate] → TAVERN
                      ↘
                       [Path B] → [Defeat Room] → [Town Gate] → TAVERN
```

**JSON Structure:**
```json
{
  "id": 30,
  "title": "Crossroads",
  "exits": {
    "east": 31,
    "west": 32,
    "south": 50
  }
},
{
  "id": 31,
  "title": "Victory Path",
  "exits": { "west": 30, "south": 50 }
},
{
  "id": 32,
  "title": "Different Path",
  "exits": { "east": 30, "south": 50 }
},
{
  "id": 50,
  "title": "Town Gate",
  "exits": {
    "north": 30,
    "south": "EXIT_TAVERN"
  }
}
```

---

## Best Practices

✅ **DO:**
- Place exit rooms at logical endpoints (end of story, at town entrance, etc.)
- Use descriptive text that hints at the journey's end ("...the familiar warmth of the Inn...")
- Provide a way back into the adventure (e.g., exit north to re-enter)
- Use consistent naming for exit rooms (e.g., "Town Gate", "Inn Entrance", etc.)

❌ **DON'T:**
- Put EXIT_TAVERN in a room players might visit mid-adventure
- Make it hard for players to find the exit (it should be obvious)
- Create multiple confusing paths to the exit

---

## Testing Your Exit

1. **Design your adventure** with an exit room
2. **Load the adventure** in the game
3. **Navigate to the exit room**
4. **Move to the exit** (e.g., `SOUTH`)
5. **Verify the message:**
   ```
   ──────────────────────────────────────────────────────────
   🏛️  You return to the town and the warmth of the Inn...
   ──────────────────────────────────────────────────────────
   ```
6. **Confirm you're back at tavern** (should see tavern room description)

---

## Example: Thornwall Keep Exit Room

For "The Ruins of Thornwall Keep", you could add:

```json
{
  "id": 999,
  "title": "Thornwall Gate",
  "description": "You stand before the crumbling gate of Thornwall Keep. The ancient ruins stretch behind you, their mysteries partly solved. Before you lies the road back to civilization, and you can see the welcoming lights of the town in the distance.",
  "first_visit": true,
  "exits": {
    "north": 1,
    "south": "EXIT_TAVERN"
  },
  "monsters": [],
  "artifacts": [],
  "locked_exits": {}
}
```

Then make room 1 point south to room 999:
```json
{
  "id": 1,
  "title": "Great Hall",
  "exits": {
    "south": 999,
    ...other exits...
  }
}
```

---

## Summary

Adding exit rooms gives players:
- ✅ Natural progression through the adventure
- ✅ Clear sense of adventure completion
- ✅ Immersive storytelling
- ✅ Easy return to tavern

Just add a room with `"EXIT_TAVERN"` as an exit, and the engine handles the rest!
