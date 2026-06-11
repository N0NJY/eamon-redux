# Eamon Redux — Adventurer's Manual

*"Slaying monsters and looting keeps for fun and profit."*

---

## Welcome to Eamon Redux

Eamon Redux is a text adventure engine inspired by the classic Eamon system originally
created by Donald Brown for the Apple II in 1980. Like the original, it combines
interactive fiction with a fantasy role-playing game. You create a character, journey
through adventures, fight monsters, collect loot, and solve puzzles using plain English
commands.

Unlike the original, Eamon Redux runs in Python on any modern system, stores all
adventure data as readable JSON files, and supports two character classes — Fighter
and Sorcerer — each with their own combat style and abilities.

All adventures begin and end at the **Saunter Inn and Tavern**, where your character
is stored between sessions, loot can be sold, and new adventures are chosen.

---

## The Saunter Inn and Tavern

When you start the game with `python3 tavern.py`, you arrive at the Saunter Inn and
Tavern. This is your home base. Guardian Horace stands behind the bar, ready to
help — or to send you on your way.

### The Adventurers' Guild

From the Guild menu you can create a new character, view an existing one, or delete
one you no longer need. Each character is stored as a separate file in the
`characters/` folder.

### New Characters

New characters are directed to the **beginner's adventure** — The Ruins of Thornwall
Keep — before the full adventure list is unlocked. Horace will let you know when
you've graduated.

### Between Adventures

After returning from an adventure, the tavern offers:

- **Full healing** — HP and mana are fully restored (win, lose, or die)
- **Death penalty** — if you died, revival costs 2 gold per missing HP
- **Horace's Trading Post** — sell any loot you carried back

---

## Creating a Character

### Choosing a Class

Before rolling stats, you choose your class. This is a permanent choice.

**Fighter** — A warrior who relies on weapons, armor, and brute strength. Fighters
get a Strength bonus to all melee damage. They can use any weapon or armor. They
cannot cast spells.

**Sorcerer** — A spellcaster who relies on Intelligence and magic. Sorcerers get an
Intelligence bonus to all spell effects and have a mana pool for casting. Their
Strength bonus is capped — they are not built for prolonged melee combat. They
choose one spell at creation and may learn more over time.

### Rolling Stats

All five stats are rolled randomly using three six-sided dice (3d6). After seeing
the results, you may keep them or reroll as many times as you like — there is no
limit. When you are satisfied, type **y** to save the character.

---

## Character Stats

Every character has five core statistics. These are set at creation and do not
change naturally, though future adventures may offer ways to increase them.

### Hardiness

Hardiness is your physical toughness and endurance. It has two effects:

- **Hit Points** = Hardiness × 2. A character with Hardiness 12 has 24 HP.
- **Carry Capacity** = Hardiness × 10 gronds. The same character can carry 120 gronds.

Weight in Eamon Redux is measured in **gronds**. A rusty sword might weigh 3 gronds;
a full coat of chainmail might weigh 6. If you try to pick up something that would
exceed your limit, you'll be told it's too heavy.

### Agility

Agility governs your quickness in combat. A high Agility gives you a better chance
to land blows and a better chance to dodge incoming ones.

- **Combat bonus** = (Agility − 10) ÷ 2, rounded down. Added to your damage rolls.
- **Dodge chance** = combat bonus × 5%. An Agility of 16 gives a 15% dodge chance.

Some adventures may also use Agility to determine success at non-combat tasks like
picking locks or avoiding traps.

### Strength

Strength represents raw physical power.

- **Fighters** gain a damage bonus of (Strength − 10) ÷ 2 added to all melee strikes.
- **Sorcerers** receive no bonus from Strength — their power lies elsewhere.

### Intelligence

Intelligence governs magical aptitude and mental sharpness.

- **Sorcerers** gain a spell bonus of (Intelligence − 10) ÷ 2, added to spell damage
  and healing rolls. Their mana pool = Intelligence × 2.
- **Fighters** receive no bonus from Intelligence.

### Charisma

Charisma is a measure of personality, appearance, and social grace. It affects how
NPCs react to your character and, in future updates, will influence merchant prices
and whether neutral monsters choose to fight or flee.

A Charisma of 10 is average. Above 10 gives a positive reaction bonus; below 10
gives a penalty.

---

## Equipment

### Equipping Items

Simply carrying a weapon or a piece of armor is not enough — you must **equip** it
for it to take effect. An unequipped sword does nothing in combat.

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

Only one item may occupy each slot at a time. Equipping a new item automatically
removes the old one.

### Weapon Types

All weapons use the same basic combat system: roll damage dice, add your Agility
and Strength (Fighter) bonuses, subtract the monster's armor class. The result is
the damage dealt. A result of zero means no damage was done.

Weapons are defined by their **damage dice** and **damage sides**. A weapon rated
1d8 rolls one 8-sided die per strike. A weapon rated 2d6 rolls two 6-sided dice
and adds them together.

### Armor and Shields

Armor reduces incoming damage by its **armor class** value. If a monster hits you
for 5 damage and you are wearing armor with armor class 3, you take only 2 damage.
If the armor class equals or exceeds the damage, the hit is fully absorbed.

Shields work the same way but occupy the shield slot, letting you stack armor and
a shield together for greater protection.

---

## Combat

### How Combat Works

Combat proceeds in **rounds**. When you type `ATTACK <monster>`, one full round
takes place: you strike the monster, then (if it survives) the monster strikes back.

Hostile monsters also attack at the end of most other actions — picking things up,
opening containers — so staying in a room with an angry enemy is always dangerous.

### Hitting and Dodging

Your chance to dodge an incoming attack is based on your Agility bonus. Each point
of bonus above zero gives a 5% chance to avoid the blow entirely.

Your damage output is your equipped weapon's dice roll, plus your Agility bonus,
plus your Strength bonus (Fighters only).

### Monster Attitudes

| Attitude | Behavior |
|---|---|
| Hostile | Attacks on sight; attacks after every action you take |
| Neutral | Passive; fights back only if you attack first |
| Friendly | Never attacks; can be talked to |

### Fleeing

If things go badly, type `FLEE`. Your character bolts in a random available
direction. Each hostile monster in the room gets one free attack as you turn to run.
There is no guarantee the exit you flee through is a safe one.

You cannot use normal movement commands while hostile monsters are present — you
must either fight or flee.

---

## Magic

### Sorcerers Only

Only Sorcerer class characters can cast spells. Fighters have no access to magic.

A Sorcerer begins with one spell chosen at character creation. More spells may
become available through adventure rewards, spellbooks, or future game updates.

### Mana

Casting spells costs **mana**. Your mana pool is Intelligence × 2. If you do not
have enough mana for a spell, the cast fails and no mana is spent.

Mana recovers in two ways:

- **REST** command — recovers 25% of your mana pool (blocked by hostile monsters)
- **Return to the tavern** — mana is fully restored

### The Four Starting Spells

#### HEAL

Calls upon restorative magic to knit wounds. Restores 1d6 + Intelligence bonus HP
to yourself. Cannot heal above your maximum HP.

```
CAST HEAL
```

Cost: 4 mana

#### FIREBALL

Hurls a sphere of conjured flame at a single target. Deals 2d6 + Intelligence bonus
fire damage. Fire damage bypasses the target's armor class — it burns regardless.

```
CAST FIREBALL
CAST FIREBALL skeleton
```

Cost: 6 mana. If there is only one monster in the room, no target name is needed.

#### SHIELD

Wraps the caster in a shimmering barrier of magical force. Grants +3 armor class
for 3 combat rounds. The shield ticks down one round with each action taken and
fades with a message when it expires.

```
CAST SHIELD
```

Cost: 3 mana

#### LIGHT

Conjures a soft magical radiance from the caster's hands. Illuminates dark rooms
for the remainder of the adventure. Without this spell (or a light source artifact),
dark rooms cannot be explored.

```
CAST LIGHT
```

Cost: 2 mana

### Viewing Your Spells

```
SPELLS
```

Lists all known spells, their mana cost, and whether you currently have enough
mana to cast them (✦ = affordable, ✗ = too costly).

---

## Healing

There are several ways to restore lost hit points during an adventure:

### Food

Some artifacts are edible. Use the `EAT` command to consume food and restore HP.
Food is consumed when eaten and cannot be used again.

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

Resting allows your body to recover. Each rest restores 25% of your maximum HP
and 25% of your maximum mana. You cannot rest while hostile monsters are in
the room.

```
REST
```

### Friendly NPCs

Some friendly characters in adventures can heal you for a price. Use `TALK TO`
to speak with them. If they offer healing, you will be shown the cost and asked
to confirm before gold is spent.

```
TALK TO hermit
TALK TO healer
```

### The Tavern

Returning to the tavern — whether you completed the adventure, quit early, or died
— restores your HP and mana to full. Death carries a gold penalty (2 gold per
missing HP at revival), but you are never left permanently weakened.

---

## Exploration

### Movement

Move between rooms using compass directions:

```
NORTH   SOUTH   EAST   WEST   UP   DOWN
N       S       E      W      U    D
GO NORTH
```

### Looking Around

```
LOOK    — describe the current room (also: L)
```

The room description shows exits, any monsters present, and any visible items.
Monsters appear in magenta; items appear in yellow.

### Locked Doors

Some exits are locked and require a specific key. The exit will be shown in red
with a `[locked]` tag. Carry the correct key and you will unlock the door
automatically when you try to move through it, or manually with:

```
UNLOCK NORTH
```

### Darkness

Some rooms are dark. Without the LIGHT spell or a light source artifact, you will
see nothing and cannot navigate safely. Sorcerers should consider taking LIGHT as
their starting spell for dungeon exploration.

### Items

```
GET <item>          — pick up an item
GET ALL             — pick up everything in the room
GET ALL POTIONS     — pick up all items of a type
DROP <item>         — drop a carried item (unequip first)
EXAMINE <item>      — inspect closely for details, stats, and type
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

Your carrying capacity is Hardiness × 10 gronds. The inventory display shows
your current weight versus your limit.

---

## NPCs and Monsters

### Talking

Friendly and neutral NPCs can be spoken to:

```
TALK TO hermit
TALK TO merchant
```

### Examining Monsters

```
EXAMINE rat
X skeleton
```

Shows the monster's description and a health status: "looks healthy," "is wounded,"
"is badly hurt," or "is near death." Use this to decide whether to press on or flee.

---

## Selling Loot

After returning from an adventure, Horace will ask if you want to visit the trading
post if you are carrying anything worth selling. Keys and quest items cannot be sold.
All other items have a gold value based on their type or a designer-assigned price.

```
S 2         — sell item number 2 from the list
SELL ALL    — sell everything at once (with confirmation)
DONE        — leave the shop without selling
```

Gold carries over between adventures and can be spent on healing from friendly NPCs.

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
| `CAST FIREBALL <monster>` | Targeted fireball |
| `SPELLS` | List known spells |

### Other
| Command | Notes |
|---|---|
| `HELP` / `?` | Show in-game command list |
| `QUIT` | End the adventure and return to tavern |

**Tip:** Arrow UP and DOWN cycle through your command history, just like a terminal shell.

---

## Designing Adventures

Adventures are plain folders containing four JSON files. Anyone can build one
using the designer tool:

```bash
python3 designer.py adventures/my_adventure
```

The designer provides menus for creating rooms, linking them with exits (including
locked exits), and placing artifacts. Monsters are currently added by editing
`monsters.json` directly — a monster editor is planned for a future update.

Each adventure can define a **win condition**: kill a specific monster, kill all
monsters, reach a specific room, or carry a specific artifact to the exit.
Adventures can also set minimum stat requirements so they appear only to characters
who are ready for them.

See `README.md` for the full data file reference.

---

## A Note on the Original

Eamon was created by Donald Brown and first published in 1980 for the Apple II.
It was one of the first games to separate the game engine from the adventure data,
allowing anyone to design and share new adventures. Hundreds of adventures were
eventually created by the Eamon community.

Eamon Redux is a spiritual successor — rebuilt from scratch in Python, with a
modern stat system, two character classes, persistent characters, and a modular
adventure format — but the soul of the original is the same: a world where you can
go anywhere, fight anything, and tell your own story.

The name "Saunter Inn and Tavern" is a nod to the AppleVenture BBS, where adventurers
once gathered to share stories in a virtual tavern of the same name.

---

*Eamon Redux — Python edition. No Apple II required.*
