# Eamon Redux

A Python text adventure engine inspired by the classic Eamon system (1980, Donald Brown).
Adventures are stored as plain JSON data files, completely separate from the engine code.
A built-in designer tool lets you build new adventures without touching any code.

This implementation features a proficiency-based magic system, weapon skill growth, critical hits/fumbles in combat, a persistent character hub (the Saunter Inn and Tavern), and an extensible handler architecture for custom adventure logic.

---

## Installation & Setup

### Requirements

- Python 3.7 or higher
- No external libraries required — standard library only
- Linux, macOS, or Windows (any OS that runs Python)

### Getting Started

1. **Clone or download the repository:**
   ```bash
   git clone https://github.com/N0NJY/eamon-redux.git
   cd eamon-redux
   ```

2. **Verify Python is installed:**
   ```bash
   python3 --version
   ```
   (Must be 3.7+)

3. **Start the game:**
   ```bash
   python3 tavern.py
   ```

4. **Create or load a character:**
   - First launch: Create a new character (directed to beginner adventure)
   - Subsequent launches: Load existing character from the menu

### Project Structure

All data is stored locally in the project directory. No internet connection required after initial setup.

```
Eamon/
├── tavern.py              # Entry point — Saunter Inn and Tavern, character hub
├── engine.py              # Game loop, parser, commands, combat, spells
├── player.py              # Runtime player state (HP, mana, equipment slots)
├── world.py               # Data classes: Room, Artifact, Monster, World loader
├── character.py           # Persistent character data (stats, class, spells, gold)
├── designer.py            # CLI adventure designer tool
├── command_parser.py      # Fuzzy command matching and parsing
├── save_system.py         # Mid-adventure save/load system
├── README.md              # This file
├── MANUAL.md              # Player-facing in-game manual
├── core/
│   └── base_handlers.py   # Generic event handler system for adventures
├── characters/            # One JSON file per character (auto-created)
└── adventures/
    └── beginner_cave/     # "The Beginner's Cave" — starting adventure
        ├── adventure.json
        ├── rooms.json
        ├── artifacts.json
        └── monsters.json
```

---

## Starting the Game

```
cd Eamon
python3 tavern.py
```

Do not run `engine.py` directly for normal play.

---

## The Tavern (Character Hub)

The **Saunter Inn and Tavern** is a fully navigable space between adventures where you manage characters, buy/sell equipment, learn spells, and choose your next adventure.

### Tavern Layout

```
[Guild Hall] ── west/east ── [Entrance] ── north/south ── [Bar] ── east/west ── [Back Room]
```

| Room | Description |
| ---- | ----------- |
| Entrance | Starting point, adventure board access |
| The Tavern Bar | Horace — buy/sell weapons, armor, shields, food, potions |
| The Back Room | Aldric — buy spells and magical items |
| Adventurers' Guild Hall | Character management, create/delete characters |

### Tavern Commands

| Command | Aliases | Description |
| ------- | ------- | ----------- |
| `N / S / E / W` | Navigation | Move between rooms |
| `GO <direction>` | | Move |
| `CHARACTER` | `SHEET`, `CH`, `CHA` | Full character stat sheet |
| `INVENTORY` | `I`, `INV`, `IN` | Items you're carrying with weights and sell values |
| `SPELLS` | `SPELL`, `SP` | Known spells, mana cost, and affordability |
| `EQUIPMENT` | `EQ`, `EQU` | Show all equipment slots and current items |
| `LOOK` | `L` | Describe current room |
| `TALK TO HORACE` | `HORACE`, `SHOP`, `HO` | Open Horace's outfitters |
| `TALK TO ALDRIC` | `ALDRIC`, `WIZARD`, `WIZ` | Open Aldric's arcane emporium |
| `ADVENTURE` | `A`, `ADV`, `AD` | View adventure list and select new adventure |
| `RESUME` | `R`, `LOAD`, `RES` | Load a saved mid-adventure game |
| `NEW` | `NE` | Create a new character |
| `HELP` | `H`, `?` | Command list |
| `QUIT` | `Q` | Exit the game |

### Horace's Outfitters (bar)

Buy and sell weapons, armor, shields, food, and potions. Stock is fixed core items plus 3 random extras that rotate based on your level and adventures completed.

- `B <number>` — buy an item
- `S <number>` or `SELL ALL` — sell gear (weapons, armor, shields, etc.)
- `DONE` — leave the shop

### Aldric's Arcane Emporium (back room)

Buy spells and magical items; sell potions and readables back.
Spell prices scale with character level.

- `B <number>` — buy a spell or item
- `S <number>` or `SELL ALL` — sell magical items
- `DONE` — leave the shop

---

## Characters

### Classes

| Class | Strengths | Notes |
| ----- | --------- | ----- |
| **Fighter** | STR bonus to melee damage, all weapons usable | No spellcasting; weapon-focused |
| **Sorcerer** | INT bonus to spell power, mana pool | Limited melee; spell-focused |

### Stats (3d6, reroll freely at creation)

| Stat | Effect |
| ---- | ------ |
| **Hardiness** | HP = Hardiness × 2; carry capacity = Hardiness × 10 gronds |
| **Agility** | Hit/dodge bonus: (Agility − 10) ÷ 2; affects combat rolls and dodge chance |
| **Strength** | Fighter melee damage bonus: (Strength − 10) ÷ 2 |
| **Intelligence** | Sorcerer spell bonus and mana pool: INT × 2 |
| **Charisma** | NPC reactions and merchant interactions (stat tracked; full effects adventure-dependent) |

---

## Adventure Commands

### Movement

| Command | Aliases | Description |
| ------- | ------- | ----------- |
| `NORTH / SOUTH / EAST / WEST / UP / DOWN` | `N/S/E/W/U/D` | Move in direction |
| `GO <direction>` | `G` | Move |
| `FLEE` | `FL` | Escape combat in a random direction (monsters get a free hit) |
| `UNLOCK <direction>` | `UL` | Unlock a locked exit if you carry the right key |

### Exploration & Interaction

| Command | Aliases | Description |
| ------- | ------- | ----------- |
| `LOOK` | `L` | Describe current room |
| `EXAMINE <thing>` | `X`, `EX`, `EXA` | Inspect an item or monster |
| `READ <item>` | `RE` | Read a readable item |
| `OPEN / CLOSE <item>` | `OP`, `CL` | Open or close a container |
| `TALK TO <npc>` | `TA` | Speak with a friendly NPC (dialogue and interactions are adventure-specific) |

### Inventory & Items

| Command | Aliases | Description |
| ------- | ------- | ----------- |
| `INVENTORY` | `I`, `INV`, `IN` | List carried items, health, and mana |
| `GET <item>` | `GE` | Pick up an item |
| `GET ALL` | `GA` | Pick up everything |
| `GET ALL <type>` | | e.g., `GET ALL POTIONS` |
| `DROP <item>` | `DR` | Drop an item (unequip first) |
| `EAT <food>` | `EA` | Eat food to restore HP |
| `DRINK <potion>` | `DI` | Drink a potion to restore HP |

### Equipment

| Command | Aliases | Description |
| ------- | ------- | ----------- |
| `EQUIP <item>` | `WEAR`, `WIELD`, `EQ` | Equip a weapon, armor, or accessory |
| `UNEQUIP <item>` | `REMOVE`, `UN` | Remove an item from its slot |
| `EQUIPMENT` | `EQU` | Show all equipment slots and stats |

**Slots:** `weapon`, `armor`, `shield`, `ring`, `cloak`. Only one item per slot.

### Combat

| Command | Aliases | Description |
| ------- | ------- | ----------- |
| `ATTACK <monster>` | `KILL`, `ATT`, `A` | Attack a monster in the room |
| `HEALTH` | `HP` | Show health, mana, equipped weapon, armor, and gold |
| `REST` | `RES` | Recover 25% HP and mana (blocked by hostile monsters) |

### Magic (Sorcerer only)

| Command | Aliases | Description |
| ------- | ------- | ----------- |
| `CAST <spell>` | `CA` | Cast a known spell |
| `CAST <spell> <target>` | | e.g., `CAST BLAST skeleton` |
| `SPELLS` | `SPELL`, `SP` | List known spells and mana costs |

### Game Control

| Command | Aliases | Description |
| ------- | ------- | ----------- |
| `SAVE` | `SA` | Save mid-adventure (slot-based) |
| `LOAD` | `LO` | Load a saved game |
| `HELP` | `H`, `?` | Command list |
| `QUIT` | `Q`, `EXIT`, `BYE` | End adventure and return to tavern |

**Tip:** Arrow UP and DOWN cycle through your command history, just like a terminal shell.

---

## Building an Adventure

```
python3 designer.py adventures/my_adventure
```

### Designer Menu

```
1. Adventure settings   — title, author, intro, starting room, win condition
2. Rooms                — add, edit, delete; set exits and locked exits
3. Artifacts            — add, edit, delete; place in rooms; set flags
4. View map             — ASCII map of room connections
5. Save
6. Test play
0. Quit
```

Monsters must be edited in `monsters.json` directly. Custom adventure logic (NPCs, followers, events) is implemented via the handler system (see "For Developers" section below).

---

## Data File Reference

### adventure.json

```json
{
  "title": "The Beginner's Cave",
  "author": "Your Name",
  "intro": "Text shown before the game starts.",
  "start_room": 1,
  "is_beginner_adventure": false,
  "win_condition": {
    "type": "kill_all",
    "message": "You have cleared the cave!"
  }
}
```

### Win Condition Types

Eamon Redux supports 7 generic win condition types:

| Type | Parameters | Description |
| ---- | ---------- | ----------- |
| `kill_monster` | `monster_id` (int) | Slay a specific monster |
| `kill_all` | (none) | Slay all monsters in adventure |
| `reach_room` | `room_id` (int) | Reach a specific room |
| `carry_artifact` | `artifact_id` (int) | Carry a specific artifact to the exit |
| `has_follower` | `monster_id` (int) | Recruit a specific NPC as follower (handler-dependent) |
| `has_any_follower` | (none) | Recruit any follower (handler-dependent) |
| `quest_completed` | `quest_id` (string) | Complete a named quest (handler-dependent) |

**Example:**
```json
{
  "type": "kill_monster",
  "monster_id": 5,
  "message": "You have defeated the guardian!"
}
```

### rooms.json

```json
[
  {
    "id": 1,
    "name": "Entrance Hall",
    "description": "A large stone chamber with exits to the north and east.",
    "exits": { "north": 2, "east": 3 },
    "locked_exits": { "north": 9 },
    "is_dark": false,
    "flags": {}
  }
]
```

- `locked_exits` maps direction → artifact ID of the key that unlocks it
- `flags` is a dict for custom adventure logic (e.g., `{"visited": true, "torches_lit": 2}`)

### artifacts.json

```json
[
  {
    "id": 1,
    "name": "rusty sword",
    "description": "A short iron sword, dull but serviceable.",
    "room_id": 1,
    "artifact_type": "weapon",
    "weight": 3,
    "damage_dice": 1,
    "damage_sides": 6,
    "value": 15,
    "weapon_type": "sword",
    "is_quest_item": false,
    "flags": {},
    "synonyms": ["sword", "blade"]
  }
]
```

**Artifact types:** `generic`, `weapon`, `armor`, `shield`, `ring`, `cloak`, `container`, `readable`, `food`, `potion`, `key`, `light`, `spellbook`

**Weapon types:** `axe`, `bow`, `club`, `spear`, `sword`

- Set `room_id` to `null` for starting inventory
- Set `is_quest_item: true` to prevent selling
- `flags` dict for custom adventure logic

### monsters.json

```json
[
  {
    "id": 1,
    "name": "giant rat",
    "description": "A rat the size of a dog, with yellowed teeth.",
    "room_id": 3,
    "attitude": "hostile",
    "hp": 8,
    "damage_dice": 1,
    "damage_sides": 4,
    "armor_class": 0,
    "loot_id": 0,
    "xp_value": 100,
    "death_message": "shrieks and goes limp.",
    "dialogue": "",
    "heal_amount": 0,
    "heal_cost": 0,
    "flags": {},
    "synonyms": ["rat"]
  }
]
```

**Attitudes:** `hostile` (attacks on sight), `neutral` (passive until attacked), `friendly` (can be talked to)

- `xp_value` is XP granted on kill (0 = auto-calculated as hp_max × 10)
- `dialogue` is spoken when player uses `TALK TO`
- `heal_amount` and `heal_cost` enable NPC healing services
- `flags` dict for custom adventure logic

---

## For Developers

### Architecture Overview

Eamon Redux uses a **data-driven, handler-based architecture** that cleanly separates game mechanics from adventure-specific logic.

**Core Components:**
- **engine.py** — Game loop, command parser, standard combat/magic/exploration
- **world.py** — Data model (Room, Artifact, Monster, World)
- **player.py** — Runtime player state (HP, mana, equipment, proficiencies)
- **character.py** — Persistent character data (saved to `characters/` JSON)
- **core/base_handlers.py** — Hook system for custom adventure logic

### Handler Architecture

Adventures can implement custom logic by creating handlers that respond to game events. The engine calls these hooks at key moments:

```python
def on_game_start(self):
    """Called when the adventure begins."""
    pass

def on_enter_room(self, room_id: int):
    """Called when the player enters a room."""
    pass

def on_talk_to_npc(self, monster_id: int):
    """Called when the player talks to a friendly NPC."""
    pass

def on_use_item(self, artifact_id: int):
    """Called when the player uses an item (READ, EAT, DRINK, etc.)."""
    pass

def on_monster_defeated(self, monster_id: int):
    """Called when the player defeats a monster."""
    pass
```

**Example:** To implement an NPC follower system, override `on_talk_to_npc()`:

```python
def on_talk_to_npc(self, monster_id: int):
    npc = self.world.monsters[monster_id]
    
    if npc.id == 5:  # The Healer
        # Check player stats or quest flags
        if self.player.alignment == "good":
            self.player.followers.append(npc.id)
            print("The healer joins your party!")
```

### Flag System

**Artifacts, Monsters, and Rooms** each have a `flags` dict for tracking adventure-specific state:

```python
artifact.flags["tradeable"] = False
artifact.flags["quest_item"] = True
room.flags["visited"] = True
room.flags["torch_count"] = 3
monster.flags["defeated"] = True
```

These persist in JSON files and can be checked in handlers or custom logic.

### Win Condition System

Win conditions are evaluated generically by the engine. Adventures define which type applies:

```python
# In adventure.json
"win_condition": {
  "type": "has_follower",
  "monster_id": 5
}
```

The engine checks the player's `followers` list. Custom logic can extend this via handlers.

### Proficiency System

**Weapons:** Each character tracks proficiency for unarmed, axe, bow, club, spear, and sword. Proficiency:
- Starts at weapon-specific values (e.g., club: +20%, bow: -10%)
- Grows by 1% on each successful hit
- Affects hit chance: `hit_chance = 50 + agility_bonus + weapon_prof - monster_ac`

**Spells:** Each spell has a proficiency percentage (25-75% when learned). Casting:
- Applies **spell fatigue** — effective proficiency is halved after each cast (50%, 25%, 12.5%, etc.)
- Recovers via REST or return to tavern
- Can fail with 1% critical failure (overload), locking the spell for the adventure
- Proficiency grows on successful casts

### Testing

Run the automated test suite:

```bash
python3 test_suite.py
```

47 tests cover flag persistence, movement, inventory, combat, magic, win conditions, and handler integration. All tests must pass before pushing changes.

### Extending the Engine

**To add a new spell:**
1. Add to `SPELL_DEFS` in `character.py`
2. Add spell key to `Player.spell_proficiencies` and `Player.spell_fatigue_multiplier`
3. Implement cast logic in `Engine.cast_spell()`
4. Test with `test_suite.py`

**To add a new combat mechanic:**
1. Modify `Engine.cmd_attack()` or `Engine.monster_round()`
2. Update `Player` runtime state if needed
3. Add tests to `test_suite.py`
4. Verify all 47 tests still pass

**To add custom adventure logic:**
1. Create `adventures/my_adventure/handlers.py` with custom handler class
2. Override relevant hooks (on_enter_room, on_talk_to_npc, etc.)
3. Use flags and quest_flags to track state
4. Test in the designer's "Test play" mode

---

## License

Do whatever you like with this. Have fun.
