# Eamon Redux — Adventurer's Manual

*"Slaying monsters and looting keeps for fun and profit."*

---

## Welcome to Eamon Redux

Eamon Redux is a text adventure engine inspired by the classic Eamon system originally created by Donald Brown for the Apple II in 1980. Like the original, it combines interactive fiction with a fantasy role-playing game. You create a character, journey through adventures, fight monsters, collect loot, and solve puzzles using plain English commands.

Unlike the original, Eamon Redux runs in Python on any modern system, stores all adventure data as readable JSON files, and supports two character classes — Fighter and Sorcerer — each with their own combat style and abilities. All adventures begin and end at the **Saunter Inn and Tavern**, where your character is stored between sessions, loot can be sold, and new adventures are chosen.

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

### Choosing a Class

Before rolling stats, you choose your class. **This is a permanent choice.**

**Fighter** — A warrior who relies on weapons, armor, and brute strength. Fighters get a Strength bonus to all melee damage and can use any weapon or armor in the game. They cannot cast spells. Fighters are straightforward and powerful in direct combat.

**Sorcerer** — A spellcaster who relies on Intelligence and magic. Sorcerers get an Intelligence bonus to all spell effects and have a mana pool for casting spells. Their Strength bonus is capped — they are not built for prolonged melee combat. Sorcerers choose one spell at creation and may learn more over time.

### Rolling Stats

All five stats are rolled randomly using three six-sided dice (3d6). After seeing the results, you may keep them or reroll as many times as you like — there is no limit. When you are satisfied, confirm to save your character.

**What 3d6 means:** Three six-sided dice are rolled and added together. The result is between 3 (all ones) and 18 (all sixes). Most results fall in the 9-12 range — consider any stat above 14 excellent and any below 8 challenging.

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

Some adventures may also use Agility to determine success at non-combat tasks like picking locks or avoiding traps.

### Strength

Strength represents raw physical power and muscle.

- **Fighters** gain a damage bonus of (Strength − 10) ÷ 2 added to all melee strikes. A Fighter with Strength 16 deals an extra 3 damage per hit.
- **Sorcerers** receive no bonus from Strength — their power lies in magic.

### Intelligence

Intelligence governs magical aptitude and mental sharpness.

- **Sorcerers** gain a spell bonus of (Intelligence − 10) ÷ 2, added to spell damage and healing rolls. Their mana pool = Intelligence × 2.
- **Fighters** receive no bonus from Intelligence — but Intelligence affects your knowledge and reaction to written clues.

A Sorcerer with Intelligence 14 has a +2 spell bonus and a mana pool of 28 points.

### Charisma

Charisma is a measure of personality, appearance, and social grace. It affects how NPCs react to your character.

A Charisma of 10 is average. Above 10 gives a positive reaction bonus; below 10 gives a penalty. Specific NPC reactions and merchant price effects are adventure-dependent.

---

## Equipment

### Equipping Items

Simply carrying a weapon or a piece of armor is not enough — you must **equip** it for it to take effect. An unequipped sword does nothing in combat.

```
EQUIP sword         — equip a weapon (also: WIELD)
EQUIP chainmail     — equip armor (also: WEAR)
UNEQUIP sword       — remove from slot (also: REMOVE)
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

Your proficiency **grows by 1% each time you successfully land a hit** with that weapon. A well-used sword becomes increasingly reliable.

### Armor and Shields

Armor reduces incoming damage by its **armor class** value. If a monster hits you for 5 damage and you are wearing armor with armor class 3, you take only 2 damage. If the armor class equals or exceeds the damage, the hit is fully absorbed.

Shields work the same way but occupy the shield slot, letting you stack armor and a shield together for greater protection.

---

## Combat

### How Combat Works

Combat proceeds in **rounds**. When you type `ATTACK <monster>`, one full round takes place: you strike the monster, then (if it survives) the monster strikes back. Each round also includes any special circumstances — critical hits, fumbles, or environmental effects.

Hostile monsters also attack at the end of most other actions — picking things up, opening containers — so staying in a room with an angry enemy is always dangerous. Neutral monsters will fight back if you attack them, but won't initiate combat.

### The Attack Roll

When you attack, the game calculates your **hit chance**:

```
Hit Chance = 50 + Agility Bonus + Weapon Proficiency - Monster AC
```

Clamped to a minimum of 5% and maximum of 95%.

Then it rolls 1d100. If the roll is less than or equal to your hit chance, you hit. Otherwise, you miss.

**Example:** You have Agility +2, sword proficiency +15%, and the monster has AC 2.
```
Hit Chance = 50 + 2 + 15 - 2 = 65%
```
You hit on a roll of 65 or lower.

### Fumbles (4% Chance on Any Attack)

Even the best warriors sometimes stumble. Every attack has a 4% chance of a **fumble**. The severity varies:

| Fumble Type | Chance | Effect |
|---|---|---|
| Recover | 35% | You stumble but regain your footing. No damage dealt. |
| Drop Weapon | 40% | Your weapon clatters to the ground. You're unarmed for the next round. |
| Break Weapon | 20% | Your weapon shatters. 50% chance you're injured for 1d4 damage. |
| Hit Yourself | 4% | You accidentally swing at yourself for 2d6 damage. |
| Fatal Wound | 1% | You fatally wound yourself. Adventure ends. |

Even while fumbling, the monster still gets a free attack.

### Normal Hit and Damage

If your attack hits and wasn't a fumble, you roll damage based on your weapon:

```
Damage = Weapon Dice + Agility Bonus + Strength Bonus (Fighters) - Monster AC
```

A result of zero means no damage was done, but minimum 1 damage always gets through.

### Critical Hits (5% Chance on Successful Hit)

If your attack hits, there's a 5% chance of a **critical hit**. The severity varies:

| Critical Type | Chance | Effect |
|---|---|---|
| Ignore Armor | 50% | Your attack bypasses the monster's armor class entirely. Full damage. |
| 1.5× Damage | 35% | Your hit deals 50% extra damage. |
| 2× Damage | 10% | Your hit deals double damage. |
| 3× Damage | 4% | Your hit deals triple damage. |
| Instant Kill | 1% | The monster falls instantly. |

Critical hits are rare but can turn the tide of battle.

### Monster Attitudes

| Attitude | Behavior |
|---|---|
| Hostile | Attacks on sight; attacks after every action you take |
| Neutral | Passive; fights back only if you attack first |
| Friendly | Never attacks; can be talked to |

### Fleeing

If things go badly, type `FLEE`. Your character bolts in a random available direction. Each hostile monster in the room gets one free attack as you turn to run. There is no guarantee the exit you flee through is a safe one.

You cannot use normal movement commands while hostile monsters are present — you must either fight or flee.

---

## Magic

### For Sorcerers Only

Only Sorcerer class characters can cast spells. Fighters have no access to magic.

A Sorcerer begins with one spell chosen at character creation. More spells may become available through adventure rewards, spellbooks, or purchasing from Aldric in the tavern.

### Mana

Casting spells costs **mana**. Your mana pool is Intelligence × 2. If you do not have enough mana for a spell, the cast fails and no mana is spent.

Mana recovers in two ways:

- **REST** command — recovers a random amount (5-10% of your pool) and eases spell fatigue
- **Return to the tavern** — mana is fully restored and spell fatigue resets

### Proficiencies and Fatigue

Each spell has a **proficiency percentage** (25-75% when you first learn it). This affects:

1. **Success Chance** — The probability the spell lands as intended (vs. fizzling)
2. **Spell Fatigue** — After each successful cast, your effective proficiency **halves** (100% → 50% → 25% → 12.5%, etc.)
3. **Overload Risk** — Each cast has a 1% chance of **critical failure** (overload), which locks the spell for the rest of the adventure

Your proficiency **grows by 1% on each successful cast** until you learn to use the spell more reliably.

**Example:** You learn Blast at 50% proficiency.
- First cast: 50% chance to hit. Success! You deal 1d6 damage. Proficiency becomes 51%, but fatigue halves it to 25.5%.
- Second cast: 25.5% effective proficiency. You rest to recover fatigue.

### The Four Starting Spells

#### BLAST

Hurls a sphere of conjured flame at a single target. Deals 1d6 fire damage. Fire damage **bypasses armor class** — it burns regardless.

```
CAST BLAST
CAST BLAST skeleton
```

**Cost:** 3 mana  
**Damage:** 1d6 + Intelligence bonus (bypasses armor)

#### HEAL

Calls upon restorative magic to knit wounds. Restores 1d10 HP to yourself. Cannot heal above your maximum HP.

```
CAST HEAL
```

**Cost:** 2 mana  
**Effect:** Restore 1d10 + Intelligence bonus HP

#### SPEED

Wraps your entire body in a shimmering aura of haste. For 11-20 combat rounds (random), your Agility is **doubled**, which affects:
- Hit chance
- Dodge chance
- Damage output

The spell effect ticks down one round with each action taken and fades with a message when it expires.

```
CAST SPEED
```

**Cost:** 5 mana  
**Duration:** 11-20 combat rounds

#### POWER

A versatile spell whose effect depends on the adventure you're in. Read any available documentation or ask NPCs what it does.

```
CAST POWER
```

**Cost:** 1 mana  
**Effect:** Adventure-specific

### Viewing Your Spells

```
SPELLS
```

Lists all known spells, their mana cost, and whether you currently have enough mana to cast them.

---

## Healing

There are several ways to restore lost hit points during an adventure:

### Food

Some artifacts are edible. Use the `EAT` command to consume food and restore HP. Food is consumed when eaten and cannot be used again.

```
EAT meat
EAT bread
```

### Potions

Healing potions restore HP when drunk. Like food, they are consumed on use.

```
DRINK potion
DRINK healing potion
```

### REST

Resting allows your body to recover. Each rest restores 25% of your maximum HP and also recovers some spell fatigue (random 5-10%).

You cannot rest while hostile monsters are in the room.

```
REST
```

### Friendly NPCs

Some friendly characters in adventures can heal you for a price. Use `TALK TO` to speak with them. If they offer healing, you will be shown the cost and asked to confirm before gold is spent.

```
TALK TO hermit
TALK TO healer
```

Healing services are adventure-specific; not all NPCs offer healing.

### The Tavern

Returning to the tavern — whether you completed the adventure, quit early, or died — restores your HP and mana to full. Death carries a gold penalty (2 gold per missing HP at revival), but you are never left permanently weakened.

---

## Exploration

### Movement

Move between rooms using compass directions:

```
NORTH   SOUTH   EAST   WEST   UP   DOWN
N       S       E      W      U    D
GO NORTH
```

You cannot move while hostile monsters are in the room — you must either fight or flee.

### Looking Around

```
LOOK    — describe the current room (also: L)
```

The room description shows exits, any monsters present, and any visible items. Monsters appear in color; items appear in color. The first time you enter a room, you see the full description. Subsequent visits show a shorter version unless you use LOOK again.

### Locked Doors

Some exits are locked and require a specific key. The exit will be shown as `[locked]`. Carry the correct key and you will unlock the door automatically when you try to move through it. You can also manually unlock with:

```
UNLOCK NORTH
```

If you don't have the key, the exit remains locked.

### Darkness

Some rooms are dark. Without the LIGHT spell (or a light source artifact), you will see nothing and cannot navigate safely. You'll see `[DARK]` in the room description and must cast LIGHT or find a light source to proceed.

Sorcerers should consider taking LIGHT as their starting spell for dungeon exploration.

### Items

```
GET <item>          — pick up an item
GET ALL             — pick up everything in the room
GET ALL POTIONS     — pick up all items of a type
DROP <item>         — drop a carried item (unequip first)
EXAMINE <item>      — inspect closely for details, stats, and type (also: X)
READ <item>         — read a readable item
OPEN <item>         — open a container
CLOSE <item>        — close a container
```

Items in containers are only accessible when the container is open.

### Inventory

```
INVENTORY   — list everything you are carrying (also: I, INV)
HEALTH      — show HP, mana, equipped weapon, armor, and gold (also: HP)
EQUIPMENT   — show all equipment slots (also: EQ)
```

Your carrying capacity is Hardiness × 10 gronds. The inventory display shows your current weight versus your limit. If you're over the limit, you can't move until you drop items.

---

## NPCs and Monsters

### Talking to NPCs

Friendly and neutral NPCs can be spoken to:

```
TALK TO hermit
TALK TO merchant
```

What they say and what they offer (healing, trading, joining your party) is adventure-specific. The engine supports NPC dialogue and interactions via the handler system; each adventure can implement its own NPC behavior.

### Examining Monsters

```
EXAMINE rat
X skeleton
```

Shows the monster's description and a health status: "looks healthy," "is wounded," "is badly hurt," or "is near death." Use this to decide whether to press on or flee.

---

## Followers and Quests

### Followers (Handler-Dependent)

Some adventures allow you to recruit NPCs as followers. This is adventure-specific and implemented via custom handlers. You may be able to:

- Recruit NPCs based on your stats, alignment, or quest progress
- Have followers fight alongside you in combat
- Carry followers to specific locations to win the adventure
- Build relationships with characters

Check the adventure's description or talk to NPCs to learn how to recruit followers.

### Quests (Handler-Dependent)

Adventures may have named quests you can complete. Quest progress is tracked via flags in your character data. Specific quest mechanics vary by adventure:

- Talk to NPCs to learn about quests
- Complete objectives to advance quest flags
- Some adventures require quest completion to win
- Rewards for completing quests may include gold, items, or followers

Your quest progress persists between tavern visits, so you can return to an adventure and resume where you left off.

---

## Selling Loot

After returning from an adventure, Horace will ask if you want to visit the trading post if you are carrying anything worth selling. Keys and quest items cannot be sold — only regular equipment and items.

```
S 2         — sell item number 2 from the list
SELL ALL    — sell everything at once (with confirmation)
DONE        — leave the shop without selling
```

Gold carries over between adventures and can be spent on healing from friendly NPCs or learning new spells from Aldric.

---

## Buying Equipment and Spells

### Horace's Outfitters

Buy weapons, armor, shields, food, and potions. Stock rotates based on your level and adventures completed. Some items are always available; others are random finds.

### Aldric's Arcane Emporium

Buy spells and magical items. Spell prices scale with your level:

- **Blast:** Relatively cheap
- **Heal:** Cheap
- **Speed:** Expensive
- **Power:** Varies by adventure

Fighters can only learn **Heal** and **Light** — other spells are unavailable to them.

---

## Command Reference

### Movement
| Command | Notes |
|---|---|
| `N S E W U D` | Move in a direction |
| `GO <direction>` | Move |
| `FLEE` | Escape combat randomly |
| `UNLOCK <direction>` | Unlock a locked exit |

### Exploration
| Command | Notes |
|---|---|
| `LOOK` / `L` | Describe room |
| `EXAMINE <x>` / `X <x>` | Inspect item or monster |
| `READ <item>` | Read a readable |
| `OPEN / CLOSE <item>` | Container interaction |

### Inventory
| Command | Notes |
|---|---|
| `INVENTORY` / `I` | List carried items |
| `GET <item>` | Pick up |
| `GET ALL` | Pick up everything |
| `GET ALL <type>` | Pick up by type |
| `DROP <item>` | Drop (unequip first) |

### Equipment
| Command | Notes |
|---|---|
| `EQUIP <item>` / `WEAR` / `WIELD` | Equip to appropriate slot |
| `UNEQUIP <item>` / `REMOVE` | Remove from slot |
| `EQUIPMENT` / `EQ` | Show all slots |

### Combat and Health
| Command | Notes |
|---|---|
| `ATTACK <monster>` | Attack (also KILL, FIGHT, HIT) |
| `FLEE` | Run from combat |
| `HEALTH` / `HP` | Show stats |
| `REST` | Recover 25% HP/mana |
| `EAT <food>` | Consume food |
| `DRINK <potion>` | Consume potion |
| `TALK TO <npc>` | Speak with NPC |

### Magic (Sorcerer)
| Command | Notes |
|---|---|
| `CAST <spell>` | Cast a known spell |
| `CAST <spell> <target>` | Targeted spell |
| `SPELLS` | List known spells |

### Other
| Command | Notes |
|---|---|
| `HELP` / `?` | Show in-game command list |
| `SAVE` | Save mid-adventure |
| `LOAD` | Load a saved game |
| `QUIT` | End the adventure and return to tavern |

**Tip:** Arrow UP and DOWN cycle through your command history, just like a terminal shell.

---

## Designing Adventures

Adventures are plain folders containing four JSON files. Anyone can build one using the designer tool:

```bash
python3 designer.py adventures/my_adventure
```

### Getting Started

1. Run the designer tool with a new adventure name
2. Set adventure title, author, introduction text, and starting room
3. Add rooms and link them with exits
4. Add artifacts (items) and place them in rooms
5. Add monsters and NPCs (currently by editing monsters.json)
6. Set a win condition (what makes the adventure complete?)
7. Test play your adventure from start to finish
8. Refine and save

### Adventure Design Basics

**Rooms** are the spaces your adventure contains. Each room has:
- A unique ID number
- A name and description
- Exits leading to other rooms (north, south, east, west, up, down)
- Optional locked exits (require a key)
- Optional flags for tracking state

**Artifacts** are items: weapons, armor, food, keys, readable texts, magical items, etc. Each artifact has:
- A unique ID number
- A name and description
- Damage dice if it's a weapon
- Armor class if it's armor
- A sell value
- Optional flags (quest item, tradeable, etc.)

**Monsters** are creatures and NPCs. Each monster has:
- A unique ID number
- A name and description
- Hit points and armor class
- Attitude (hostile, neutral, friendly)
- Dialogue text if it can be talked to
- Optional healing services (cost in gold)

**Win Condition** defines what the player must do to complete your adventure:
- Kill a specific monster
- Kill all monsters
- Reach a specific room
- Carry a specific artifact to the exit
- Recruit a specific NPC (handler-dependent)
- Complete a named quest (handler-dependent)

### Designer Menu Options

```
1. Adventure settings   — title, author, intro, starting room, win condition
2. Rooms                — add, edit, delete; set exits and locked exits
3. Artifacts            — add, edit, delete; place in rooms
4. View map             — ASCII map of room connections
5. Save
6. Test play
0. Quit
```

### Testing Your Adventure

Use the "Test play" option to play your own adventure from start to finish. This helps catch:
- Broken exit links (doors leading nowhere)
- NPCs with no dialogue
- Items placed in inaccessible rooms
- Win conditions that can't be met

Test your adventure thoroughly before sharing it!

### Advanced: Custom Handlers

Once you've created the basic adventure in the designer, you can add custom logic via **handlers**. Handlers respond to game events and enable:

- NPC follower recruitment
- Quest systems
- Conditional encounters
- Dynamic room descriptions
- Item transformations

This requires Python coding. See the README.md "For Developers" section for details on the handler architecture.

---

## A Note on the Original

Eamon was created by Donald Brown and first published in 1980 for the Apple II. It was one of the first games to separate the game engine from the adventure data, allowing anyone to design and share new adventures. Hundreds of adventures were eventually created by the Eamon community.

Eamon Redux is a spiritual successor — rebuilt from scratch in Python, with a modern stat system, two character classes, persistent characters, a proficiency-based magic system, critical hits and fumbles in combat, and a modular adventure format — but the soul of the original is the same: a world where you can go anywhere, fight anything, and tell your own story.

The name "Saunter Inn and Tavern" is a nod to the AppleVenture BBS, where adventurers once gathered to share stories in a virtual tavern of the same name.

---

*Eamon Redux — Python edition. No Apple II required.*
