# Eamon Adventure Engine

A Python text adventure engine inspired by the classic Eamon system from the Apple II era.
Adventures are stored as plain JSON data files, completely separate from the engine code.
A built-in designer tool lets you build new adventures without touching any code.

---

## Requirements

- Python 3.7 or higher
- No external libraries required — standard library only

---

## Directory Structure

```
Eamon/
├── engine.py          # Game loop, parser, commands, combat
├── player.py          # Player state (HP, inventory, armor)
├── world.py           # Data classes: Room, Artifact, Monster, World loader
├── designer.py        # CLI adventure designer tool
├── README.md          # This file
└── adventures/
    └── sample/        # "The Ruins of Thornwall Keep" — sample adventure
        ├── adventure.json   # Title, author, intro text, starting room
        ├── rooms.json       # All rooms and their exits
        ├── artifacts.json   # All objects (weapons, armor, containers, etc.)
        └── monsters.json    # All monsters and NPCs
```

---

## Playing an Adventure

```bash
cd Eamon
python3 engine.py adventures/sample
```

To play as a named character:

```bash
python3 engine.py adventures/sample --name "Aldric"
```

### Commands

| Command | Description |
|---|---|
| `NORTH / SOUTH / EAST / WEST / UP / DOWN` | Move (abbreviations N/S/E/W/U/D work too) |
| `LOOK` or `L` | Describe the current room |
| `INVENTORY` or `I` | List carried items and show health |
| `GET <item>` / `TAKE <item>` | Pick up an item |
| `DROP <item>` | Drop an item |
| `EXAMINE <thing>` or `X <thing>` | Inspect an item or monster closely |
| `READ <item>` | Read text on a readable item |
| `OPEN <item>` / `CLOSE <item>` | Open or close a container |
| `ATTACK <monster>` | Attack a monster (also: KILL, FIGHT, HIT) |
| `FLEE` | Escape combat in a random direction |
| `HEALTH` or `HP` | Show your health and combat stats |
| `HELP` or `?` | Show the command list |
| `QUIT` | End the game |

### Combat

- Use `ATTACK <monster>` to initiate or continue a fight. Each attack is one full round — you hit, then the monster hits back.
- Your **best weapon** in inventory is used automatically.
- **Armor** in your inventory reduces incoming damage.
- **Hostile** monsters attack you when you enter their room and after most actions.
- **Neutral** monsters only fight back if you attack them first.
- **Friendly** NPCs cannot be attacked.
- You cannot move normally while in combat — use `FLEE` to escape (monsters get a free hit as you run).

---

## Building an Adventure

```bash
python3 designer.py adventures/my_adventure
```

If the directory doesn't exist yet, the designer starts a new adventure from scratch.
If it already exists, it loads and lets you continue editing.

### Designer Menu

```
1. Adventure settings   — title, author, intro text, starting room
2. Rooms                — add, edit, delete rooms; set exits between them
3. Artifacts            — add, edit, delete objects; place them in rooms
4. View map             — ASCII map of all rooms and their connections
5. Save                 — write JSON files to disk
6. Test play            — save and immediately launch the engine
0. Quit
```

### ASCII Map

Option 4 renders a live map of your adventure as you build it. The starting room
is shown with a double-line border. Vertical connections (UP/DOWN) are listed
below the map since they can't easily be shown on a 2D grid.

```
  ╔═════════╗   ┌─────────┐
  ║#1       ║   │#3       │
  ║Clearing ║───│Cave     │
  ╚════╦════╝   └─────────┘
       │
  ┌────┴────┐
  │#2       │
  │Gatehouse│
  └─────────┘
```

---

## Data File Reference

Each adventure lives in its own folder and contains four JSON files.

### adventure.json

```json
{
  "title": "My Adventure",
  "author": "Your Name",
  "intro": "Text shown before the game starts.",
  "start_room": 1
}
```

### rooms.json

```json
[
  {
    "id": 1,
    "name": "Room Name",
    "description": "What the player sees when they look around.",
    "exits": { "north": 2, "east": 3 },
    "is_dark": false
  }
]
```

Exits are a JSON object mapping direction names to destination room IDs.
Valid directions: `north`, `south`, `east`, `west`, `up`, `down`.

### artifacts.json

```json
[
  {
    "id": 1,
    "name": "rusty sword",
    "description": "A short iron sword, pitted with rust.",
    "room_id": 1,
    "artifact_type": "weapon",
    "weight": 3,
    "damage_dice": 1,
    "damage_sides": 6,
    "synonyms": ["sword", "blade"]
  }
]
```

**Artifact types:**

| Type | Extra fields | Notes |
|---|---|---|
| `generic` | — | Default; any ordinary object |
| `weapon` | `damage_dice`, `damage_sides` | Best weapon in inventory is used in combat |
| `armor` | `armor_class` | Reduces incoming damage by armor_class value |
| `container` | `is_open`, `contents` | `contents` is a list of artifact IDs inside |
| `readable` | `read_text` | Player can READ this item |
| `light` | — | Reserved for future darkness mechanic |

Set `room_id` to `null` to place an artifact in the player's starting inventory.

### monsters.json

```json
[
  {
    "id": 1,
    "name": "giant rat",
    "description": "A rat the size of a dog.",
    "room_id": 3,
    "attitude": "hostile",
    "hp": 8,
    "damage_dice": 1,
    "damage_sides": 4,
    "armor_class": 0,
    "loot_id": 0,
    "death_message": "The rat shrieks and goes limp.",
    "synonyms": ["rat", "rodent"]
  }
]
```

**Attitudes:**

| Attitude | Behavior |
|---|---|
| `hostile` | Attacks the player on sight and after every action |
| `neutral` | Passive until attacked; then fights back |
| `friendly` | Never attacks; cannot be attacked |

Set `loot_id` to an artifact ID to have that item drop when the monster dies (0 = nothing).
Leave `death_message` blank for a default message.

---

## Color Scheme

The engine uses ANSI colors. All color definitions are in the `C` class at the top
of `engine.py` and can be changed to taste.

| Color | Used for |
|---|---|
| Bold green | Room names, command prompt |
| Green | Room descriptions, intro, farewell |
| Dim green | Borders, exits, carry weight |
| Yellow | Artifact names |
| Dim yellow | "You see:", "Inside:" labels |
| Magenta | Monster names |
| Cyan | Action confirmations (pick up, drop, open) |
| Red | Errors, combat hit messages |
| Bold red | Heavy hits, death screen |
| Bold yellow | Victory / kill messages |

---

## Extending the Engine

The codebase is intentionally small and readable.

- **New commands** — add an `elif` branch in `Engine.handle()` and a `cmd_*` method.
- **New artifact types** — add a constant to `ArtifactType` in `world.py`, handle it in the engine.
- **New monster behaviors** — the `Monster` dataclass in `world.py` is the place to start; combat logic lives in `Engine.cmd_attack()` and `Engine.monster_round()`.
- **New adventures** — run `python3 designer.py adventures/your_name` and use the menus.

Planned future features: locked doors, darkness/light sources, saving mid-game, spell system.

---

## License

Do whatever you like with this. Have fun.

## Still to complete

Looking at what we have versus a complete, polished game system, here's what I see missing:

**Gameplay features the engine is missing:**
- **Save / load mid-game** — you die, everything is lost
- **Locked doors** — a key artifact that unlocks a specific exit
- **Darkness** — dark rooms where you need a light source or you're blind
- **NPC dialogue** — TALK TO <person>, the hermit just stands there silently
- **Score / win condition** — no way for an adventure to declare victory
- **Player death respawn or game-over screen** with stats summary

**Designer is missing:**
- **Monster editor** — you can create rooms and artifacts in the designer but there's no menu for monsters yet
- **Exit validation** — no warning if you point an exit at a room ID that doesn't exist
- **Adventure linter** — a "check" option that reports problems before you play

**Data / sample adventure gaps:**
- The **wraith in the undercroft** is brutally tough with no way to prepare — no armor artifact exists anywhere in the sample
- The **old hermit** is silent and interactable with nothing — wastes a friendly NPC
- No **win condition** — no way to "finish" Thornwall Keep

**Project / repo housekeeping:**
- **`.gitignore`** — `__pycache__/` is currently being committed
- **`requirements.txt`** — even if empty, it signals to others that dependencies were considered
- **Version number** somewhere (README or a `__version__` in engine.py)

**Biggest gaps in order of impact:**
1. Monster editor in designer
2. Save / load
3. Locked doors
4. NPC dialogue
5. Win condition + game over summary


