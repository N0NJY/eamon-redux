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
├── characters/        # One JSON file per character (auto-created)
└── adventures/
    └── sample/        # "The Ruins of Thornwall Keep" — beginner adventure
        ├── adventure.json   # Title, author, intro, starting room, win condition
        ├── rooms.json       # All rooms and their exits
        ├── artifacts.json   # All objects (weapons, armor, food, potions, etc.)
        └── monsters.json    # All monsters and NPCs
```

---

## Starting the Game

```bash
cd Eamon
python3 tavern.py
```

This opens the **Saunter Inn and Tavern** — the main hub where you create and manage
characters, choose adventures, and sell loot between runs. Do not run `engine.py`
directly for normal play.

---

## Characters

### Classes

| Class | Strengths | Notes |
|---|---|---|
| Fighter | STR bonus to melee damage, all weapons usable | No spellcasting |
| Sorcerer | INT bonus to spell power, mana pool | Chooses one starting spell; limited melee |

### Stats (all rolled 3d6 at creation, reroll freely until satisfied)

| Stat | Effect |
|---|---|
| Hardiness | HP = Hardiness × 2; carry capacity = Hardiness × 10 gronds |
| Agility | Hit/dodge bonus: (Agility − 10) ÷ 2 |
| Strength | Fighter melee damage bonus: (Strength − 10) ÷ 2 |
| Intelligence | Sorcerer spell bonus and mana pool: INT × 2 |
| Charisma | NPC reactions (implemented, full effects coming) |

### Character files

Characters are saved in `characters/<name>.json`. The file tracks current HP, mana,
gold, completed adventures, and whether the character is still a beginner.
Delete the file to remove a character, or use option D in the Guild menu.

---

## Commands

### Movement

| Command | Description |
|---|---|
| `NORTH / SOUTH / EAST / WEST / UP / DOWN` | Move (N/S/E/W/U/D also work) |
| `GO <direction>` | Move |
| `FLEE` | Escape combat in a random direction (monsters get a free hit) |
| `UNLOCK <direction>` | Unlock a locked exit if you carry the right key |

### Actions

| Command | Description |
|---|---|
| `LOOK` or `L` | Describe current room |
| `INVENTORY` or `I` | List carried items, health, and mana |
| `GET <item>` | Pick up an item |
| `GET ALL` | Pick up everything in the room |
| `GET ALL <type>` | e.g. `GET ALL POTIONS`, `GET ALL WEAPONS` |
| `DROP <item>` | Drop an item (must unequip first) |
| `EXAMINE <thing>` or `X` | Inspect an item or monster |
| `READ <item>` | Read a readable item |
| `OPEN / CLOSE <item>` | Open or close a container |
| `EAT <food>` | Eat food to restore HP |
| `DRINK <potion>` | Drink a potion to restore HP |
| `REST` | Recover 25% HP and mana (blocked by hostile monsters) |
| `TALK TO <npc>` | Speak with a friendly NPC (some offer healing for gold) |
| `HEALTH` or `HP` | Show health, mana, weapon, armor, and gold |

### Equipment

| Command | Description |
|---|---|
| `EQUIP <item>` | Equip a weapon, armor, or accessory (also: WEAR, WIELD) |
| `UNEQUIP <item>` | Remove an item from its slot (also: REMOVE) |
| `EQUIPMENT` or `EQ` | Show all equipment slots and stats |

Equipment slots: `weapon`, `armor`, `shield`, `ring`, `cloak`.
Only the equipped weapon is used in combat. Unequipped weapons do nothing.
Arrow UP/DOWN cycles through command history (like bash).

### Combat

| Command | Description |
|---|---|
| `ATTACK <monster>` | Attack a monster (also: KILL, FIGHT, HIT, STAB) |

Each attack is one full round — you hit, then the monster hits back.
Hostile monsters attack automatically when you enter their room and after most actions.
Neutral monsters only fight back if you attack them first.
Friendly NPCs cannot be attacked.

### Magic (Sorcerer only)

| Command | Description |
|---|---|
| `CAST <spell>` | Cast a known spell |
| `CAST FIREBALL <monster>` | Target a fireball at a specific monster |
| `SPELLS` | List known spells and mana costs |

**Starting spells (choose one at character creation):**

| Spell | Mana cost | Effect |
|---|---|---|
| Heal | 4 | Restore 1d6 + INT bonus HP |
| Fireball | 6 | Deal 2d6 + INT bonus fire damage to one enemy |
| Shield | 3 | +3 armor class for 3 combat rounds |
| Light | 2 | Illuminate dark rooms for the adventure |

Mana refills 25% on REST and fully on return to the tavern.

---

## The Tavern

Between adventures, the **Saunter Inn and Tavern** offers:

- **Character management** — create, view, or delete characters
- **Adventure selection** — veterans see all available adventures with stat requirements
- **Horace's Trading Post** — sell carried loot for gold after each adventure
- **Healing** — full HP and mana restored on return (alive or dead)
- **Death penalty** — revival costs 2 gold per missing HP

Guardian Horace directs new characters to the beginner's adventure. Once completed,
the full adventure list opens up.

### Selling items

After returning from an adventure, if you have sellable items Horace will offer
to buy them. Prices are set per item in the JSON (`value` field), or fall back
to type defaults. Keys and quest items cannot be sold.

**Type price floors:** weapon 10g, armor 15g, shield 10g, ring 20g, cloak 15g,
potion 5g, food 2g, readable 3g, generic 1g.

---

## Building an Adventure

```bash
python3 designer.py adventures/my_adventure
```

The designer starts a new adventure if the folder doesn't exist, or loads an
existing one. Option 6 saves and immediately launches the engine for test play.

### Designer menu

```
1. Adventure settings   — title, author, intro, starting room
2. Rooms                — add, edit, delete; set exits and locked exits
3. Artifacts            — add, edit, delete; place in rooms
4. View map             — ASCII map of room connections
5. Save
6. Test play
0. Quit
```

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
  "min_hardiness": 0,
  "min_agility": 0,
  "win_condition": {
    "type": "kill_monster",
    "monster_id": 5,
    "message": "You have won!"
  }
}
```

**Win condition types:** `kill_monster` (monster_id), `kill_all`, `reach_room` (room_id),
`carry_artifact` (artifact_id).

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

`locked_exits` maps a direction to the artifact ID of the key that unlocks it.

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

**Artifact types:**

| Type | Extra fields | Notes |
|---|---|---|
| `generic` | — | Any ordinary object |
| `weapon` | `damage_dice`, `damage_sides` | Must be EQUIPped to use in combat |
| `armor` | `armor_class` | Must be EQUIPped; reduces incoming damage |
| `shield` | `armor_class` | Equips in shield slot |
| `ring` | — | Equips in ring slot (effects coming) |
| `cloak` | — | Equips in cloak slot (effects coming) |
| `container` | `is_open`, `contents` | `contents` is a list of artifact IDs |
| `readable` | `read_text` | Player can READ this item |
| `food` | `heal_amount` | EAT to restore HP |
| `potion` | `heal_amount` | DRINK to restore HP |
| `key` | — | Unlocks a locked exit; cannot be sold |
| `light` | — | Reserved for darkness mechanic |
| `spellbook` | — | Reserved for learning spells |

Set `room_id` to `null` to place an artifact in the player's starting inventory.
Set `is_quest_item: true` to prevent selling.

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
    "synonyms": ["rat", "rodent"]
  }
]
```

**Attitudes:** `hostile` (attacks on sight), `neutral` (passive until attacked),
`friendly` (never attacks, can TALK TO).

Set `dialogue` for NPC speech. Set `heal_amount` and `heal_cost` (gold per HP)
for a healing NPC.

---

## Color Scheme

All colors are defined in the `C` class at the top of `engine.py`.

| Color | Used for |
|---|---|
| Bold green | Room names, command prompt |
| Green | Room descriptions, intro text |
| Dim green | Borders, exits, carry weight |
| Yellow | Artifact names |
| Bold yellow | Equipped item tags, victory messages |
| Magenta | Monster names, NPC speech |
| Cyan | Action confirmations, health bar |
| Dim cyan | Mana bar, spell info |
| Bold cyan | Spell effects |
| Red | Errors, combat hit messages |
| Bold red | Player death screen |

---

## Extending the Engine

The codebase is intentionally small and readable.

- **New commands** — add an entry to the `dispatch` dict in `Engine.handle()` and a `cmd_*` method.
- **New artifact types** — add a constant to `ArtifactType` in `world.py`; add a slot in `EQUIP_SLOTS` in `player.py` if equippable.
- **New spells** — add an entry to `SPELL_DEFS` in `engine.py` and a `_cast_*` method.
- **New monster behaviors** — extend the `Monster` dataclass in `world.py`; combat logic is in `Engine.cmd_attack()` and `Engine.monster_round()`.
- **New adventures** — run `python3 designer.py adventures/your_name`.

---

## Still To Complete

- **Save / load mid-game** — progress is lost if you quit mid-adventure
- **Monster editor in designer** — monsters must be edited in JSON directly
- **Exit validation in designer** — no warning for broken exit links
- **Adventure linter** — a check option to catch data errors before play
- **Charisma effects** — stat exists but merchant prices and NPC reactions not yet wired
- **Ring / cloak effects** — equipment slots exist, enchantment effects not yet implemented
- **NPC shop** — Horace buys items; selling back to player not yet implemented
- **More spells** — only four spells in v1

---

## License

Do whatever you like with this. Have fun.
