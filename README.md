# Eamon Redux

A Python text adventure engine inspired by the classic Eamon system (1980, Donald Brown).
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
├── tavern.py          # Entry point — Saunter Inn and Tavern, character hub
├── engine.py          # Game loop, parser, commands, combat, spells
├── player.py          # Runtime player state (HP, mana, equipment slots)
├── world.py           # Data classes: Room, Artifact, Monster, World loader
├── character.py       # Persistent character data (stats, class, spells, gold)
├── designer.py        # CLI adventure designer tool
├── README.md          # This file
├── MANUAL.md          # Player-facing in-game manual
├── characters/        # One JSON file per character (auto-created)
└── adventures/
    └── sample/        # "The Ruins of Thornwall Keep" — beginner adventure
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

## The Tavern

The **Saunter Inn and Tavern** is a fully navigable space between adventures.

### Rooms

```
[Guild Hall] ── west/east ── [Entrance] ── north/south ── [Bar] ── east/west ── [Back Room]
```

| Room | Who's here |
| ---- | ---------- |
| Entrance | Starting point |
| The Tavern Bar | Horace — buy/sell weapons, armor, gear |
| The Back Room | Aldric — buy spells and magical items |
| Adventurers' Guild Hall | Character management, adventure board |

### Tavern commands

| Command | Description |
| ------- | ----------- |
| `N / S / E / W` | Move between rooms |
| `GO <direction>` | Move |
| `CHARACTER` / `SHEET` | Full character stat sheet |
| `INVENTORY` / `I` | Items you are carrying with weights and sell values |
| `SPELLS` | Known spells, mana cost, and affordability |
| `LOOK` / `L` | Describe current room |
| `TALK TO HORACE` | Open Horace's shop (also: `HORACE`, `SHOP`) |
| `TALK TO ALDRIC` | Open Aldric's shop (also: `ALDRIC`, `WIZARD`) |
| `RESUME` / `SAVES` | Load a saved mid-adventure game |
| `QUIT` / `Q` | Go to the adventure board |
| `HELP` / `?` | Command list |

### Horace's Outfitters (bar)

Buy and sell weapons, armor, shields, food, and potions. Stock is fixed core items
plus 3 random extras that rotate based on your level and adventures completed.

- `B <number>` — buy an item
- `S <number>` or `SELL ALL` — sell gear (weapons, armor, shields, etc.)
- `DONE` — leave

### Aldric's Arcane Emporium (back room)

Buy spells and magical items; sell potions and readables back.
Spell prices scale with character level. Fighters pay double and can only learn Heal and Light.

- `B <number>` — buy a spell or item
- `S <number>` or `SELL ALL` — sell magical items
- `DONE` — leave

---

## Characters

### Classes

| Class | Strengths | Notes |
| ----- | --------- | ----- |
| Fighter | STR bonus to melee damage, all weapons usable | No spellcasting |
| Sorcerer | INT bonus to spell power, mana pool | Chooses one starting spell; limited melee |

### Stats (3d6, reroll freely at creation)

| Stat | Effect |
| ---- | ------ |
| Hardiness | HP = Hardiness × 2; carry capacity = Hardiness × 10 gronds |
| Agility | Hit/dodge bonus: (Agility − 10) ÷ 2 |
| Strength | Fighter melee damage bonus: (Strength − 10) ÷ 2 |
| Intelligence | Sorcerer spell bonus and mana pool: INT × 2 |
| Charisma | NPC reactions (stat tracked; merchant effects coming) |

---

## Adventure Commands

### Movement

| Command | Description |
| ------- | ----------- |
| `NORTH / SOUTH / EAST / WEST / UP / DOWN` | Move (N/S/E/W/U/D also work) |
| `GO <direction>` | Move |
| `FLEE` | Escape combat in a random direction (monsters get a free hit) |
| `UNLOCK <direction>` | Unlock a locked exit if you carry the right key |

### Actions

| Command | Description |
| ------- | ----------- |
| `LOOK` / `L` | Describe current room |
| `INVENTORY` / `I` | List carried items, health, and mana |
| `GET <item>` | Pick up an item |
| `GET ALL` | Pick up everything |
| `GET ALL <type>` | e.g. `GET ALL POTIONS` |
| `DROP <item>` | Drop an item (unequip first) |
| `EXAMINE <thing>` / `X` | Inspect an item or monster |
| `READ <item>` | Read a readable item |
| `OPEN / CLOSE <item>` | Open or close a container |
| `EAT <food>` | Eat food to restore HP |
| `DRINK <potion>` | Drink a potion to restore HP |
| `REST` | Recover 25% HP and mana (blocked by hostile monsters) |
| `TALK TO <npc>` | Speak with a friendly NPC |
| `HEALTH` / `HP` | Show health, mana, weapon, armor, and gold |

### Equipment

| Command | Description |
| ------- | ----------- |
| `EQUIP <item>` | Equip a weapon, armor, or accessory (also: `WEAR`, `WIELD`) |
| `UNEQUIP <item>` | Remove an item from its slot (also: `REMOVE`) |
| `EQUIPMENT` / `EQ` | Show all equipment slots and stats |

Slots: `weapon`, `armor`, `shield`, `ring`, `cloak`. Arrow UP/DOWN cycles command history.

### Combat

| Command | Description |
| ------- | ----------- |
| `ATTACK <monster>` | Attack a monster (also: `KILL`, `FIGHT`, `HIT`, `STAB`) |

### Magic (Sorcerer only)

| Command | Description |
| ------- | ----------- |
| `CAST <spell>` | Cast a known spell |
| `CAST FIREBALL <monster>` | Target a specific monster |
| `SPELLS` | List known spells and mana costs |

**Spells:**

| Spell | Mana | Effect |
| ----- | ---- | ------ |
| Heal | 4 | Restore 1d6 + INT bonus HP |
| Fireball | 6 | 2d6 + INT bonus fire damage to one enemy |
| Shield | 3 | +3 armor class for 3 combat rounds |
| Light | 2 | Illuminate dark rooms for the adventure |

---

## Building an Adventure

```
python3 designer.py adventures/my_adventure
```

### Designer menu

```
1. Adventure settings   — title, author, intro, starting room, win condition
2. Rooms                — add, edit, delete; set exits and locked exits
3. Artifacts            — add, edit, delete; place in rooms
4. View map             — ASCII map of room connections
5. Save
6. Test play
0. Quit
```

Monsters must currently be edited in `monsters.json` directly.

---

## Data File Reference

### adventure.json

```json
{
  "title": "My Adventure",
  "author": "Your Name",
  "intro": "Text shown before the game starts.",
  "start_room": 1,
  "is_beginner_adventure": false,
  "win_condition": {
    "type": "kill_monster",
    "monster_id": 5,
    "message": "You have won!"
  }
}
```

Win condition types: `kill_monster` (monster_id), `kill_all`, `reach_room` (room_id), `carry_artifact` (artifact_id).

### rooms.json

```json
[
  {
    "id": 1,
    "name": "Room Name",
    "description": "What the player sees.",
    "exits": { "north": 2, "east": 3 },
    "locked_exits": { "north": 9 },
    "is_dark": false
  }
]
```

`locked_exits` maps direction → artifact ID of the key that unlocks it.

### artifacts.json

```json
[
  {
    "id": 1,
    "name": "rusty sword",
    "description": "A short iron sword.",
    "room_id": 1,
    "artifact_type": "weapon",
    "weight": 3,
    "damage_dice": 1,
    "damage_sides": 6,
    "value": 15,
    "is_quest_item": false,
    "synonyms": ["sword", "blade"]
  }
]
```

Set `room_id` to `null` for starting inventory. Set `is_quest_item: true` to prevent selling.

**Artifact types:** `generic`, `weapon`, `armor`, `shield`, `ring`, `cloak`, `container`, `readable`, `food`, `potion`, `key`, `light`, `spellbook`

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
    "dialogue": "",
    "heal_amount": 0,
    "heal_cost": 0,
    "synonyms": ["rat"]
  }
]
```

Attitudes: `hostile` (attacks on sight), `neutral` (passive until attacked), `friendly` (TALK TO).

---

## Still To Complete

- **Mid-game save / load** — engine side not yet implemented; tavern UI is ready
- **Monster editor in designer** — monsters must be edited in JSON directly
- **Exit validation in designer** — no warning for broken exit links
- **Adventure linter** — pre-play check for data errors
- **Charisma effects** — merchant price modifiers and NPC reactions not yet wired
- **Ring / cloak enchantments** — equipment slots exist; effects not yet implemented
- **Ranged weapon mechanic** — bow/crossbow sold by Horace; engine treats them as melee
- **More spells** — only four in v1
- **Second adventure** — engine and designer are ready; only the sample exists

---

## License

Do whatever you like with this. Have fun.
