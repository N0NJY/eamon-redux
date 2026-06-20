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

### File Organization

All game data lives in the project directory. Nothing is written outside it.

```
eamon-redux/
├── tavern.py              # Start here — runs the Saunter Inn and Tavern
├── engine.py              # Adventure game loop (do not run directly)
├── designer.py            # Adventure designer tool
├── *.py                   # Other engine modules
├── README.md              # Quick-start and developer reference
│
├── documentation/
│   ├── MANUAL.md          # This file
│   └── README.md          # Developer documentation
│
├── adventures/            # One folder per adventure
│   ├── beginners_cave/
│   │   ├── adventure.json
│   │   ├── rooms.json
│   │   ├── artifacts.json
│   │   ├── monsters.json
│   │   └── handlers.py    # Optional custom event handlers
│   └── <your_adventure>/  # Adventures you build with the designer go here
│
├── characters/            # Your character save files (one JSON per character)
└── stored_games/          # Mid-adventure saves (one JSON per save slot)
```

**Where things get saved:**
- Characters are saved to `characters/<name>.json` automatically when you finish an adventure or quit from the tavern.
- Mid-adventure saves go to `stored_games/<name>_<adventure>_slot<n>.json` and can be resumed from the tavern.
- Adventures you create with the designer are stored under `adventures/` and appear in the adventure board immediately.

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

### Rings

Rings fit the ring slot and may carry **stat bonuses** that take effect immediately when equipped and are removed when you take the ring off.

```
EQUIP ring      — slip the ring on; bonus shown in parentheses
REMOVE ring     — remove it; bonus reversed
```

A ring's effect is printed when you equip it: "You equip the gold ring. (+2 Intelligence)."

**Cursed rings** apply a penalty to a stat and **cannot be removed** — the `REMOVE` command will tell you the ring is cursed. You will need a special item or location to lift the curse.

Stat bonuses from rings persist across save/load and carry over into new adventures as long as you are wearing the ring when the adventure ends.

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

### Followers in Combat

Any followers travelling with you automatically join each combat round. After your attack, each follower who can fight makes their own strike against the same enemy. Monsters fight back — there is a 30% chance each round that the monster swings at a follower instead of you, so keep an eye on their health.

Some followers are **non-combatants** (like a rescued prisoner). They travel with you and count toward quest objectives but do not fight.

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
FREE prisoner       — release a captive NPC (also: RELEASE)
```

`TALK TO` directs speech at a specific NPC and may trigger dialogue, healing offers, or follower recruitment. `SAY` broadcasts to the room and may trigger adventure-specific reactions (passwords, secrets).

`FREE` releases a captive NPC and causes them to join you as a follower. If the NPC has a guard, you must defeat that guard first. Freeing a captive usually awards bonus XP.

### Examining Monsters

```
EXAMINE rat
X skeleton
```

Shows the monster's description and a health status: "looks healthy," "is wounded," "is badly hurt," or "is near death."

---

## Followers and Quests

### Recruiting Followers

Some NPCs can be recruited as followers. To recruit one, use `TALK TO <npc>`. If that NPC is available to join, the game checks their recruitment conditions:

| Condition type | What it means |
|---|---|
| stat | You must have a minimum score in a specific stat (e.g., Strength ≥ 12) |
| chance | A random roll, modified by a stat such as Charisma |
| trade | You must be carrying a specific item |
| combat | You must have achieved a minimum kill count this adventure |
| alignment | Your character must have a particular alignment |

Some followers charge a **gold fee** to join. If you cannot pay, they decline. Once recruited, a follower stays with you, moves when you move, and fights beside you in combat.

**You cannot recruit the same NPC twice** in a session — if you already have them, talking to them just acknowledges that.

### Freeing Captives

Some NPCs are held prisoner and cannot be recruited by talking — they must be **freed**:

```
FREE cynthia
FREE prisoner
```

A captive usually has a **guard** that must be defeated first. Attempting to free them while the guard lives will tell you so. Once the guard is dead, `FREE` releases them and they join you as a follower.

Freeing a captive often awards bonus XP. In some adventures, bringing a rescued captive to safety unlocks an additional reward — for example, rescuing Cynthia in the Beginner's Cave and completing the adventure with her in your party earns 50 gold from her father, Duke Luxom, as a reward for her safe return.

### Follower Display

When you `LOOK` at a room, followers appear in a separate green **Companions** section, distinct from the **Creatures** list. Recruited followers no longer appear under Creatures.

### Quests (Adventure-Dependent)

Adventures may have named quests. Quest progress is tracked via flags and persists between sessions, so you can return to an adventure and resume where you left off.

---

## Saving and Loading

```
SAVE        — save your current position (3 slots per adventure)
LOAD        — load a saved game (also: RESTORE)
```

Saves store your full position: room, HP, mana, inventory, monster states, and artifact locations. You can have up to 3 save slots per adventure.

### Item Persistence

Items you carry when an adventure ends **stay with your character**. They appear in your inventory the next time you begin any adventure, and they retain all their original properties — damage dice, stat bonuses, flags. If the item is equipped (such as a ring granting +2 Intelligence), that bonus is also restored.

**If you sell an item at the tavern, it is gone permanently.** There is no buyback.

Items brought from a previous adventure are kept separate from the new adventure's own items, so there is no conflict if two adventures happen to contain items with the same name or ID.

### Quest Items and Keys

Two flags control whether an item can be sold or carried out of an adventure:

| Flag | Sell at tavern? | Carried to next adventure? |
|---|---|---|
| Normal item | Yes (if value > 0) | Yes |
| `is_quest_item` | **No** | Yes — still in inventory after exit |
| `adventure_only` | Yes, mid-adventure | **No** — auto-sold for gold on exit |
| Both flags set | **No** | **No** — silently removed on exit |

**`is_quest_item`** prevents the item from being sold at Horace's or Aldric's. It does not remove the item when the adventure ends — quest items follow the character into later adventures unless `adventure_only` is also set.

**`adventure_only`** removes the item when the player leaves the adventure. The engine auto-sells it for its stated value (minimum 1 gold) and prints a message listing what was taken. Keys are the most common use case — a cave key should not follow the player into an unrelated dungeon.

**Keys** (artifact type `key`) are never sold at the tavern regardless of flags, because the tavern's shop does not buy keys. They remain in your inventory after an adventure unless `adventure_only` is set on them.

To create a key or quest item that disappears cleanly on exit, set **both** `is_quest_item` and `adventure_only` in the designer.

---

## Managing Equipment in the Tavern

You can equip and unequip items while in the tavern without entering an adventure.

```
EQUIP <item>    — equip a carried weapon, armor, ring, shield, or cloak
                  (also: WEAR, WIELD, READY)
EQUIP           — show a numbered list of all equippable items; choose by number
UNEQUIP         — same list, but to remove a currently equipped item
                  (also: REMOVE, DOFF)
EQUIPMENT       — show all five slots and what is currently in each (also: EQ)
```

Items marked **[EQUIPPED]** in your inventory are active. Equipped status carries over into adventures — if you equip chainmail in the tavern, you begin your next adventure already wearing it.

Cursed items cannot be unequipped from the tavern any more than they can from inside an adventure.

---

## Selling Loot

Visit Horace (weapons, armor, shields, general gear) or Aldric (potions, scrolls, spellbooks) to sell items. Your full inventory is shown at the top of each shop screen so you can always see what you are carrying alongside the buy listing.

```
S <n>       — sell the numbered item (must not be equipped)
SELL ALL    — sell all eligible items at once, skipping equipped ones
DONE        — leave without selling
```

**Sell prices** are shown in parentheses next to each item in your inventory, e.g. `short sword 2g (10g)` — the first number is carry weight, the second is what Horace or Aldric will pay. Items bought from the shops resell at roughly one-third of their purchase price. Adventure loot sells at its stated value.

**Equipped items are protected.** They appear in the sell listing marked `[EQUIPPED — unequip first]` and cannot be sold — not even by SELL ALL. Use `UNEQUIP` or `EQUIPMENT` to remove an item before selling it.

Keys and quest items cannot be sold regardless of equipped status.

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
| `TALK TO <npc>` | `ASK`, `REQUEST` | Speak with an NPC; may recruit as follower |
| `SAY <words>` | `YELL`, `SHOUT` | Broadcast to the room |
| `SMILE` | `WAVE`, `GRIN`, `BOW` | Friendly emote |
| `FREE <creature>` | `RELEASE` | Free a captive; guard must be dead first |

### Special (adventure-specific)
| Command | Aliases | Notes |
|---|---|---|
| `TROLLSFIRE` | `TF` | Toggle TrollsFire's flame (see below) |

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

## Special Items

### TrollsFire

TrollsFire is a magical two-handed sword found in the Beginner's Cave. It has a command of its own:

```
TROLLSFIRE      — also: TF
```

**Behavior depends on whether you have it equipped:**

| State | Result |
|---|---|
| TrollsFire not present | "TrollsFire is not here." |
| Carried but not equipped | The sword's uncontrolled flame bursts out and **burns you for 1d4 fire damage** |
| Equipped (weapon slot) | Toggles flame on/off |

When the flame is **on**, every attack deals **+1d4 fire damage** that bypasses the monster's armor class entirely. Use `TROLLSFIRE` again to extinguish it.

Fire damage from TrollsFire stacks with critical hits and spell damage. The flame stays on until you turn it off — there is no timer.

---

## Designing Adventures

Adventures are plain folders containing four JSON files. Launch the designer with no arguments and it shows a startup menu:

```bash
python3 designer.py
```

The menu lists all existing adventures by number. Choose one to open it, `N` to create a new adventure (the designer prompts for a title and creates the directory automatically), or `0` to quit.

You can also pass a path directly to skip the chooser — useful for scripting or opening an adventure by name:

```bash
python3 designer.py adventures/my_adventure
```

### Recommended Workflow

1. **Settings** — set title, author, and introduction text (skip win condition for now)
2. **Rooms** — add all rooms; connect them with exits
3. **Artifacts** — add items and place them in rooms
4. **Monsters & NPCs** — add enemies, healers, followers, and captives
5. **Settings again** — pick the starting room and set the win condition (monsters must exist first for kill conditions)
6. **Save**, then **Test play** to verify

### Designer Menu

```
1. Adventure settings  — title, author, intro, starting room, win condition
2. Rooms               — add, edit, exits, locked exits
3. Artifacts           — items, weapons, armor, rings, ...
4. Monsters & NPCs     — enemies, followers, captives
5. View map            — ASCII grid of room connections
6. Save
7. Test play (launch engine)
0. Quit
```

### Rooms

Each room has a name, a description, and a set of exits. Exits can point to another room by ID, or to the special code `EXIT_TAVERN` to send the player back to the surface.

**Directions supported:** north, south, east, west, up, down, northeast, northwest, southeast, southwest.

**Locked exits** require the player to be carrying a specific key artifact to pass through. Set them via **Rooms → 6. Edit locked exits** — pick the exit direction and the artifact ID of the key.

The map viewer (option 5 from the main menu) renders a live ASCII grid of all room connections:

- **N/S/E/W** exits drawn with `─` and `│` line characters
- **NE/NW/SE/SW** diagonal exits drawn with `╱` and `╲` characters
- **UP/DOWN** exits listed as text below the grid (too vertical for the 2D grid)
- The starting room is shown with a double border (`╔═╗`)

Use it to spot dead ends, missing return exits, or rooms accidentally left disconnected.

### Artifacts

All 13 artifact types are supported. Choose the type when adding an artifact and the designer prompts for the relevant fields:

| Type | Player action | Key fields |
|---|---|---|
| `generic` | EXAMINE / USE | — |
| `weapon` | EQUIP / ATTACK | damage dice, damage sides, weapon type |
| `armor` | EQUIP | armor class bonus |
| `shield` | EQUIP | armor class bonus |
| `ring` | EQUIP | stat bonuses, ring label, cursed |
| `cloak` | EQUIP | stat bonuses, ring label, cursed |
| `container` | OPEN / CLOSE | starts open? |
| `readable` | READ | text displayed |
| `spellbook` | READ | text displayed; name after the spell it teaches |
| `food` | EAT | HP restored |
| `potion` | DRINK | HP restored |
| `light` | LIGHT | illuminates dark rooms |
| `key` | carried automatically | link to a locked exit via Rooms → Edit locked exits |

**Weapon types** (affects proficiency system): sword, axe, club, spear, bow.

**Sell value** is set per artifact. Use −1 to let the engine calculate a default from the type.

#### Artifact Flags

When adding or editing an artifact the designer first asks **"Quest item (cannot be sold)?"** — this sets `is_quest_item` directly. Then **"Edit special flags?"** opens the full flags menu:

| Flag | Effect |
|---|---|
| `adventure_only` | Removed on exit; auto-sold for its value (min 1 gold) and gold credited |
| `is_tradeable` | Can be given to a specific NPC for a scripted trade |
| `is_escape_vehicle` | USE on this item ends the adventure (boat, portal, etc.) |
| `triggers_event` | Using the item fires a named event handler |

**`is_quest_item` vs `adventure_only`** — these are independent. `is_quest_item` blocks tavern sales; `adventure_only` removes the item on exit. Set both on a key or plot-critical item that should not follow the player into later adventures. See the [Quest Items and Keys](#quest-items-and-keys) section for the full behaviour table.

**Rings and cloaks** also prompt for stat bonuses (per stat, positive or negative) and a label shown when the item is equipped. Setting `cursed: true` makes the item impossible to remove.

### Monsters & NPCs

Every monster has a name, description, attitude (hostile / neutral / friendly), HP, damage dice, armor class, XP value, dialogue (shown on TALK TO), and a death message.

**Loot:** set a loot artifact ID to have the monster drop that item when killed.

**Healing NPCs:** neutral and friendly NPCs can offer healing for gold — the designer prompts for HP per use and gold cost per HP.

#### Follower Flags

When adding or editing a monster, choose **Configure follower / captive flags** to make an NPC recruitable or captive. The designer prompts for every field:

**Recruitable followers** (via TALK TO):

| follower_type | Condition checked |
|---|---|
| `stat` | Player must have a minimum score in a chosen stat |
| `chance` | Random roll, optionally boosted by a stat (e.g. Charisma) |
| `trade` | Player must be carrying a specific item |
| `combat` | Player must have reached a kill-count threshold |
| `alignment` | Player must have a specific alignment |
| `quest` | A named quest flag must be True |

Additional fields: `recruit_cost` (gold to join), `follower_dialogue` (shown on success), `recruit_fail_dialogue` (shown on failure), `can_fight` (does the follower fight in combat?).

**Captives** (freed with FREE command):

Set `is_captive: true`. The designer also prompts for `guard_id` (the monster that must be killed first), `free_dialogue`, `free_fail_dialogue`, `free_xp_bonus`, and `can_fight`.

### Win Conditions

Set the win condition from **Adventure Settings → Edit win condition**. The designer walks you through all the options and picks rooms, monsters, and artifacts by name from your existing data.

| Type | When it triggers |
|---|---|
| `reach_room` | Player enters a specific room (use `EXIT_TAVERN` for the surface exit) |
| `kill_monster` | A specific monster is dead |
| `kill_all` | Every monster in the adventure is dead |
| `carry_artifact` | Player is carrying a specific artifact |
| `has_follower` | A specific NPC is in the player's party |
| `compound` | All conditions in an `all_of` list are simultaneously true |

**Tip:** set the win condition last — kill and follower conditions require monsters to already exist in the designer before you can pick them.

Every win condition also has a **victory message** shown in the win banner.

Example — kill the Pirate to win the Beginner's Cave:
```json
"win_condition": {
  "type": "kill_monster",
  "monster_id": 8,
  "message": "The Pirate falls! The cave is cleared."
}
```

Example compound win condition — reach the exit carrying the relic:
```json
"win_condition": {
  "type": "compound",
  "all_of": [
    { "type": "reach_room",     "room_id": "EXIT_TAVERN" },
    { "type": "carry_artifact", "artifact_id": 12 }
  ],
  "message": "You escaped with the relic!"
}
```

### Advanced: Custom Handlers

Custom logic via **handlers** enables NPC follower recruitment, quest systems, conditional encounters, dynamic room descriptions, and item transformations. Handlers respond to events like `on_enter_room`, `on_monster_defeated`, `on_give`, `on_say`, `on_use`, `on_light`, `on_free`, and `on_adventure_win`.

`on_adventure_win` fires just before the player's state is saved at the end of a successful adventure, making it the right place to award end-of-adventure bonuses (extra gold, XP, stat changes). The Beginner's Cave uses it to pay out Duke Luxom's reward if Cynthia is in the party.

See the README.md "For Developers" section for details on the handler architecture.

---

## A Note on the Original

Eamon was created by Donald Brown and first published in 1980 for the Apple II. It was one of the first games to separate the game engine from the adventure data, allowing anyone to design and share new adventures. Hundreds of adventures were created by the Eamon community.

Eamon Redux is a spiritual successor — rebuilt from scratch in Python, with a modern stat system, a classless character system, persistent characters, a proficiency-based magic system, critical hits and fumbles in combat, diagonal movement, and a modular adventure format. The soul of the original is the same: a world where you can go anywhere, fight anything, and tell your own story.

The name "Saunter Inn and Tavern" is a nod to the AppleVenture BBS, where adventurers once gathered in a virtual tavern of the same name.

---

*Eamon Redux — Python edition. No Apple II required.*
