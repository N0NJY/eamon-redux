# Eamon Redux — Adventurer's Manual

*"Slaying monsters and looting keeps for fun and profit."*

---

## Welcome to Eamon Redux

Eamon Redux is a text adventure engine inspired by the classic Eamon system originally created by Donald Brown for the Apple II in 1980. Like the original, it combines interactive fiction with a fantasy role-playing game. You create a character, journey through adventures, fight monsters, collect loot, and solve puzzles using plain English commands.

Unlike the original, Eamon Redux runs in Python on any modern system, stores all adventure data as readable JSON files, and features a **classless character system** — any character can learn any spell, use any weapon, and develop any skill over time. All adventures begin and end at the **Saunter Inn and Tavern**, where your character is stored between sessions, loot can be sold, and new adventures are chosen.

---

## Starting the Game

### Installation

1. Download or clone the Eamon Redux repository
2. Open a terminal/command prompt
3. Navigate to the Eamon directory
4. Type: `python3 tavern.py`
5. Create a new character or load an existing one

**System Requirements:**
- Python 3.7 or higher
- No external libraries needed
- Works on Linux, macOS, and Windows

### The Saunter Inn and Tavern

When you start the game with `python3 tavern.py`, you arrive at the Saunter Inn and Tavern. This is your home base. From here you can create characters, manage your inventory, buy equipment and spells, and choose your next adventure.

---

## Creating a Character

### Rolling Stats

All five stats are rolled randomly using three six-sided dice (3d6). After seeing the results, you may keep them or reroll as many times as you like — there is no limit. When you are satisfied, confirm to save your character.

**What 3d6 means:** Three six-sided dice are rolled and added together. The result is between 3 (all ones) and 18 (all sixes). Most results fall in the 9–12 range — consider any stat above 14 excellent and any below 8 challenging.

There are no classes in Eamon Redux. Every character can use any weapon, wear any armor, and learn any spell. Your stats determine how effective you are — a high Strength makes you hit harder, a high Intelligence makes your spells more powerful.

---

## Character Stats

Every character has five core statistics. These are set at creation and do not change during normal play, though future adventures may offer ways to increase them.

### Hardiness

Hardiness is your physical toughness and endurance. It has two effects:

- **Hit Points (HP)** = Hardiness × 2. A character with Hardiness 12 has 24 maximum HP.
- **Carry Capacity** = Hardiness × 10 gronds. The same character can carry 120 gronds of weight.

Weight in Eamon Redux is measured in **gronds**. A rusty sword might weigh 3 gronds; a full coat of chainmail might weigh 6. If you try to pick up something that would exceed your carry limit, you'll be told it's too heavy.

### Agility

Agility governs your quickness in combat. A high Agility gives you a better chance to land blows and a better chance to dodge incoming ones.

- **Combat Bonus** = (Agility − 10) ÷ 2, rounded down. Added to your damage rolls and hit chance.
- **Dodge Chance** = Combat Bonus × 5%. An Agility of 16 gives a +3 combat bonus and a 15% chance to dodge incoming attacks.

### Strength

Strength represents raw physical power and muscle.

- **Damage Bonus** = (Strength − 10) ÷ 2, rounded down. Added to all melee weapon damage. A character with Strength 16 deals an extra 3 damage per hit.

### Intelligence

Intelligence governs magical aptitude and mental sharpness.

- **Mana Pool** = Intelligence × 2. This is how much spell energy you have.
- **Spell Bonus** = (Intelligence − 10) ÷ 2. Added to spell damage and healing rolls.

A character with Intelligence 14 has a +2 spell bonus and a mana pool of 28 points.

### Charisma

Charisma is a measure of personality, appearance, and social grace. It affects how NPCs react to your character and the prices merchants offer for your loot.

A Charisma of 10 is average. Above 10 gives a positive reaction bonus; below 10 gives a penalty. Specific NPC reactions are adventure-dependent.

---

## Equipment

### Equipping Items

Simply carrying a weapon or piece of armor is not enough — you must **equip** it for it to take effect. An unequipped sword does nothing in combat.

```
EQUIP sword         — equip an item (also: WEAR, WIELD, READY)
REMOVE sword        — remove from slot (also: UNEQUIP, DOFF)
EQUIPMENT           — show all slots (also: EQ)
```

### Equipment Slots

Each character has five equipment slots:

| Slot | What goes in it |
|---|---|
| weapon | Any weapon artifact |
| armor | Any armor artifact |
| shield | A shield artifact |
| ring | A ring artifact |
| cloak | A cloak artifact |

Only one item may occupy each slot at a time. Equipping a new item automatically removes the old one.

### Weapons and Proficiencies

All weapons use the same basic combat system: roll damage dice, add your bonuses, subtract the monster's armor class. The result is the damage dealt.

Weapons are defined by their **damage dice** and **damage sides**. A weapon rated 1d8 rolls one 8-sided die per strike. A weapon rated 2d6 rolls two 6-sided dice and adds them together.

Each weapon type has a **proficiency percentage** that affects your hit chance and starts at a weapon-specific value:
- Sword: 0% (balanced)
- Club: +20% (common training)
- Spear: +10% (straightforward)
- Axe: +5% (somewhat difficult)
- Bow: -10% (very difficult to learn)
- Unarmed: 0% (your fists)

Your proficiency **grows by 1% each time you successfully land a hit** with that weapon.

### Armor and Shields

Armor reduces incoming damage by its **armor class** value. If a monster hits you for 5 damage and you are wearing armor with armor class 3, you take only 2 damage. Shields stack with armor for greater protection.

---

## Combat

### How Combat Works

Combat proceeds in **rounds**. When you type `ATTACK <monster>`, one full round takes place: you strike the monster, then (if it survives) the monster strikes back.

Hostile monsters also attack at the end of most other actions — picking things up, opening containers — so staying in a room with an angry enemy is always dangerous. Neutral monsters will fight back if you attack them, but won't initiate combat.

### The Attack Roll

When you attack, the game calculates your **hit chance**:

```
Hit Chance = 50 + Agility Bonus + Weapon Proficiency - Monster AC
```

Clamped to a minimum of 5% and maximum of 95%.

**Example:** You have Agility +2, sword proficiency +15%, and the monster has AC 2.
```
Hit Chance = 50 + 2 + 15 - 2 = 65%
```
You hit on a roll of 65 or lower.

### Fumbles (4% Chance on Any Attack)

Every attack has a 4% chance of a **fumble**:

| Fumble Type | Chance | Effect |
|---|---|---|
| Recover | 35% | You stumble but regain your footing. No damage dealt. |
| Drop Weapon | 40% | Your weapon clatters to the ground. You're unarmed next round. |
| Break Weapon | 20% | Your weapon shatters. 50% chance of 1d4 self-damage. |
| Hit Yourself | 4% | You accidentally swing at yourself for 2d6 damage. |
| Fatal Wound | 1% | You fatally wound yourself. Adventure ends. |

Even while fumbling, the monster still gets a free attack.

### Normal Hit and Damage

```
Damage = Weapon Dice + Agility Bonus + Strength Bonus - Monster AC
```

Minimum 1 damage always gets through.

### Critical Hits (5% Chance on Successful Hit)

| Critical Type | Chance | Effect |
|---|---|---|
| Ignore Armor | 50% | Bypasses monster's armor class entirely. |
| 1.5× Damage | 35% | Hit deals 50% extra damage. |
| 2× Damage | 10% | Hit deals double damage. |
| 3× Damage | 4% | Hit deals triple damage. |
| Instant Kill | 1% | The monster falls instantly. |

### Monster Attitudes

| Attitude | Behavior |
|---|---|
| Hostile | Attacks on sight; attacks after every action you take |
| Neutral | Passive; fights back only if you attack first |
| Friendly | Never attacks; can be talked to |

### Fleeing

Type `FLEE` (also: `RUN`, `ESCAPE`) to bolt in a random available direction. Each hostile monster gets one free attack as you turn to run. You cannot use normal movement while hostile monsters are present — fight or flee.

---

## Magic

### All Characters Can Cast Spells

There are no spell restrictions in Eamon Redux. Any character can learn and cast any spell. Your Intelligence determines your mana pool and your spell effectiveness.

To learn spells, visit **Aldric's Arcane Emporium** in the tavern. You can also find spellbooks in adventures.

### Mana

Casting spells costs **mana**. Your mana pool is Intelligence × 2. If you do not have enough mana for a spell, the cast fails and no mana is spent.

Mana recovers by:
- **REST** command — recovers a portion of your pool and eases spell fatigue
- **Return to the tavern** — mana is fully restored and spell fatigue resets

### Proficiencies and Fatigue

Each spell has a **proficiency percentage** (25–75% when you first learn it):

1. **Success Chance** — Probability the spell works as intended
2. **Spell Fatigue** — After each cast, your effective proficiency **halves** (100% → 50% → 25% → ...)
3. **Overload Risk** — Each cast has a 1% chance of **critical failure**, locking the spell for the rest of the adventure

Proficiency **grows by 1% on each successful cast**.

### Casting Spells

Spells can be cast two ways — both are equivalent:

```
CAST BLAST              — cast using the CAST keyword
BLAST                   — shortcut, no CAST needed
CAST BLAST skeleton     — targeted spell with CAST
BLAST skeleton          — targeted spell shortcut
```

The four spells: `BLAST`, `HEAL`, `SPEED`, `POWER`. See below for details.

### The Four Spells

#### BLAST

Hurls conjured energy at a single target. Fire damage **bypasses armor class**.

```
BLAST           — cast at current combat target
CAST BLAST rat  — target a specific monster
```

**Cost:** 3 mana | **Damage:** 1d6 + Intelligence bonus (bypasses armor)

#### HEAL

Calls upon restorative magic to knit wounds. Cannot heal above your maximum HP.

```
HEAL
CAST HEAL
```

**Cost:** 2 mana | **Effect:** Restore 1d10 + Intelligence bonus HP

#### SPEED

Doubles your Agility for 11–20 combat rounds, which affects hit chance, dodge chance, and damage output. Fades with a message when it expires.

```
SPEED
CAST SPEED
```

**Cost:** 5 mana | **Duration:** 11–20 combat rounds

#### POWER

A versatile spell whose effect depends on the adventure. Read any available documentation or ask NPCs what it does.

```
POWER
CAST POWER
```

**Cost:** 1 mana | **Effect:** Adventure-specific

### Viewing Your Spells

```
SPELLS
```

Lists all known spells, their mana cost, current fatigue, and whether you have enough mana to cast them.

---

## Healing

### Food

```
EAT meat
EAT bread
```

Food is consumed when eaten and cannot be used again.

### Potions

```
DRINK potion
DRINK healing potion
```

Potions are consumed on use.

### REST

Resting restores 25% of your maximum HP and mana, and recovers some spell fatigue. You cannot rest while hostile monsters are in the room.

```
REST
```

### Friendly NPCs

Some characters can heal you for a price. Use `TALK TO` to speak with them.

```
TALK TO hermit
TALK TO healer
```

### The Tavern

Returning to the tavern restores your HP and mana to full. Death carries a gold penalty (2 gold per missing HP at revival), but you are never left permanently weakened.

---

## Exploration

### Movement

Move between rooms using compass directions — including diagonals:

```
NORTH   SOUTH   EAST   WEST   UP   DOWN
N       S       E      W      U    D

NORTHEAST   NORTHWEST   SOUTHEAST   SOUTHWEST
NE          NW          SE          SW

GO NORTH
GO NE
```

You cannot move while hostile monsters are in the room — fight or flee first.

### Locked Doors

Some exits require a specific key. Carry the correct key and you unlock the door automatically when you move through it. You can also unlock manually:

```
UNLOCK NORTH
```

### Darkness

Some rooms are dark. Without a light source, you cannot navigate safely. Find a torch or lamp and use `LIGHT` to illuminate it.

### Looking Around

```
LOOK    — describe the current room (also: L)
```

The room description shows exits, any monsters present, and any visible items. The first time you enter a room you see the full description; use LOOK again to re-read it.

---

## Items and Inventory

### Picking Up and Dropping

```
GET sword           — pick up an item (also: TAKE, PICK)
GET ALL             — pick up everything in the room
GET ALL potions     — pick up all items of a type (plural OK)
DROP sword          — drop a carried item
```

### Examining and Reading

```
EXAMINE sword       — inspect closely: description, stats, type (also: X)
EXAMINE rat         — examine a monster: health status
READ inscription    — read a readable item
```

`EXAMINE` works on anything — items, monsters, room features. `READ` is specifically for readable items (inscriptions, books, scrolls). You cannot read a monster.

### Containers

```
OPEN chest          — open a container
CLOSE chest         — close a container
```

Items inside containers are only accessible when the container is open.

### Using Items

```
USE potion          — smart-use: delegates to DRINK, EAT, EQUIP, READ, or LIGHT
LIGHT torch         — light a torch or lamp (also: IGNITE)
EAT bread           — consume food
DRINK potion        — consume a potion
```

`USE` figures out what to do based on the item type. For unusual items, the adventure may define a custom effect.

### Giving and Placing

```
GIVE sword TO hermit    — hand an item to an NPC
PUT coin IN chest       — place an item in a container (also: PUT coin INTO chest)
```

### Inventory Display

```
INVENTORY   — list everything you are carrying (also: I, INV)
HEALTH      — show HP, mana, equipped weapon, armor, and gold (also: HP)
EQUIPMENT   — show all equipment slots (also: EQ)
CHAR        — full character sheet (also: STATUS, SHEET, V)
```

Your carrying capacity is Hardiness × 10 gronds.

---

## NPC Interaction

### Talking

```
TALK TO hermit      — speak with an NPC (also: ASK, REQUEST)
SAY "open sesame"   — broadcast words to the room (also: YELL, SHOUT)
SMILE               — friendly gesture (also: WAVE, GRIN, BOW)
FREE prisoner       — release a captive creature (also: RELEASE)
```

`TALK TO` directs speech at a specific NPC and may trigger dialogue, healing offers, or quest events. `SAY` broadcasts to the room and may trigger adventure-specific reactions (passwords, secrets).

### Examining Monsters

```
EXAMINE rat
X skeleton
```

Shows the monster's description and a health status: "looks healthy," "is wounded," "is badly hurt," or "is near death."

---

## Followers and Quests

### Followers (Adventure-Dependent)

Some adventures allow you to recruit NPCs as followers — they fight alongside you in combat. Recruit them by talking to them and meeting their conditions (stats, alignment, items, quest progress). Check the adventure's intro or talk to NPCs to learn more.

### Quests (Adventure-Dependent)

Adventures may have named quests. Quest progress is tracked via flags and persists between sessions, so you can return to an adventure and resume where you left off.

---

## Saving and Loading

```
SAVE        — save your current position (3 slots per adventure)
LOAD        — load a saved game (also: RESTORE)
```

Saves store your full position: room, HP, mana, inventory, monster states, and artifact locations. You can have up to 3 save slots per adventure.

---

## Selling Loot

After returning from an adventure, Horace will offer to buy any items you're carrying. Keys and quest items cannot be sold.

```
S 2         — sell item number 2
SELL ALL    — sell everything at once (with confirmation)
DONE        — leave without selling
```

---

## Buying Equipment and Spells

### Horace's Outfitters

Weapons, armor, shields, food, and potions. Stock varies by your level and adventures completed.

### Aldric's Arcane Emporium

All four spells are available to any character. Prices:

| Spell | Approximate Cost |
|---|---|
| Power | Cheap |
| Heal | Moderate |
| Blast | Moderate |
| Speed | Expensive |

---

## Command Reference

### Movement
| Command | Aliases | Notes |
|---|---|---|
| `N S E W U D` | — | Cardinal directions |
| `NE NW SE SW` | — | Diagonal directions |
| `GO <direction>` | `G` | Move by name |
| `FLEE` | `RUN`, `ESCAPE` | Escape combat randomly |
| `UNLOCK <direction>` | `UL` | Unlock a locked exit |

### Exploration
| Command | Aliases | Notes |
|---|---|---|
| `LOOK` | `L` | Describe room |
| `EXAMINE <x>` | `X`, `EX` | Inspect item, monster, or feature |
| `READ <item>` | `REA` | Read a readable item |
| `OPEN <item>` | `OP` | Open a container |
| `CLOSE <item>` | `CL` | Close a container |

### Inventory
| Command | Aliases | Notes |
|---|---|---|
| `INVENTORY` | `I`, `INV` | List carried items |
| `GET <item>` | `TAKE`, `PICK` | Pick up an item |
| `GET ALL` | — | Pick up everything |
| `GET ALL <type>` | — | Pick up by type (plurals OK) |
| `DROP <item>` | `DR`, `PLACE` | Drop a carried item |
| `USE <item>` | `US` | Smart-use (delegates by type) |
| `LIGHT <item>` | `IGNITE` | Light a torch or lamp |
| `GIVE <item> TO <npc>` | `GI` | Give to an NPC |
| `PUT <item> IN <container>` | `PU` | Place in container |
| `EAT <food>` | `EA` | Consume food |
| `DRINK <potion>` | `DRI` | Consume a potion |

### Equipment
| Command | Aliases | Notes |
|---|---|---|
| `EQUIP <item>` | `WEAR`, `WIELD`, `READY` | Equip to appropriate slot |
| `UNEQUIP <item>` | `REMOVE`, `DOFF` | Remove from slot |
| `EQUIPMENT` | `EQ` | Show all slots |

### Combat
| Command | Aliases | Notes |
|---|---|---|
| `ATTACK <monster>` | `KILL`, `FIGHT`, `HIT`, `A` | Attack a monster |
| `FLEE` | `RUN`, `ESCAPE` | Run from combat |

### Magic
| Command | Aliases | Notes |
|---|---|---|
| `CAST <spell>` | `CA` | Cast a known spell |
| `CAST <spell> <target>` | — | Targeted spell |
| `BLAST [target]` | `BLA` | Cast Blast directly |
| `HEAL` | `HEA` | Cast Heal directly |
| `SPEED` | `SPEE` | Cast Speed directly |
| `POWER` | `POW` | Cast Power directly |
| `SPELLS` | `SP` | List known spells |

### Interaction
| Command | Aliases | Notes |
|---|---|---|
| `TALK TO <npc>` | `ASK`, `REQUEST` | Speak with an NPC |
| `SAY <words>` | `YELL`, `SHOUT` | Broadcast to the room |
| `SMILE` | `WAVE`, `GRIN`, `BOW` | Friendly emote |
| `FREE <creature>` | `RELEASE` | Release a captive |

### Status
| Command | Aliases | Notes |
|---|---|---|
| `HEALTH` | `HP` | Show HP, mana, gear, gold |
| `REST` | `RES` | Recover 25% HP/mana |
| `CHAR` | `STATUS`, `SHEET`, `V` | Full character sheet |
| `SPELLS` | `SP` | Known spells and proficiencies |

### Game Control
| Command | Aliases | Notes |
|---|---|---|
| `SAVE` | `SA` | Save mid-adventure (3 slots) |
| `LOAD` | `RESTORE` | Load a saved game |
| `HELP` | `H`, `?` | In-game command list |
| `QUIT` | `Q`, `EXIT`, `BYE` | Return to tavern |

---

## Designing Adventures

Adventures are plain folders containing four JSON files. Anyone can build one using the designer tool:

```bash
python3 designer.py adventures/my_adventure
```

### Getting Started

1. Run the designer tool with a new adventure name
2. Set adventure title, author, introduction text, and starting room
3. Add rooms and link them with exits (including diagonals: northeast, northwest, etc.)
4. Add artifacts (items) and place them in rooms
5. Add monsters and NPCs
6. Set a win condition
7. Test play your adventure from start to finish

### Adventure Design Basics

**Rooms** each have:
- A unique ID number
- A name and description
- Exits leading to other rooms (north, south, east, west, up, down, northeast, northwest, southeast, southwest)
- Optional locked exits (require a key artifact)
- Optional flags for tracking state

**Artifacts** are items: weapons, armor, food, keys, readable texts, containers, light sources, magical items, etc.

**Monsters** are creatures and NPCs with hit points, armor class, attitude (hostile/neutral/friendly), and optional dialogue and healing services.

**Win Condition** defines what the player must do:
- Kill a specific monster
- Kill all monsters
- Reach a specific room (including `EXIT_TAVERN` to return home)
- Carry a specific artifact to the exit
- Complete a named quest (handler-dependent)

### Designer Menu

```
1. Adventure settings   — title, author, intro, starting room, win condition
2. Rooms                — add, edit, delete; set exits and locked exits
3. Artifacts            — add, edit, delete; place in rooms
4. View map             — ASCII map of room connections
5. Save
6. Test play
0. Quit
```

### Advanced: Custom Handlers

Custom logic via **handlers** enables NPC follower recruitment, quest systems, conditional encounters, dynamic room descriptions, and item transformations. Handlers respond to events like `on_enter_room`, `on_monster_defeated`, `on_give`, `on_say`, `on_use`, `on_light`, and `on_free`.

See the README.md "For Developers" section for details on the handler architecture.

---

## A Note on the Original

Eamon was created by Donald Brown and first published in 1980 for the Apple II. It was one of the first games to separate the game engine from the adventure data, allowing anyone to design and share new adventures. Hundreds of adventures were created by the Eamon community.

Eamon Redux is a spiritual successor — rebuilt from scratch in Python, with a modern stat system, a classless character system, persistent characters, a proficiency-based magic system, critical hits and fumbles in combat, diagonal movement, and a modular adventure format. The soul of the original is the same: a world where you can go anywhere, fight anything, and tell your own story.

The name "Saunter Inn and Tavern" is a nod to the AppleVenture BBS, where adventurers once gathered in a virtual tavern of the same name.

---

*Eamon Redux — Python edition. No Apple II required.*
