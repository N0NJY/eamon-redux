# Eamon Redux — Adventurer's Manual

*"Slaying monsters and looting keeps for fun and profit."*

---

## Welcome to Eamon Redux

Eamon Redux is a text adventure engine inspired by the classic Eamon system originally created by Donald Brown for the Apple II in 1980. Like the original, it combines interactive fiction with a fantasy role-playing game. You create a character, journey through adventures, fight monsters, collect loot, and solve puzzles using plain English commands.

Unlike the original, Eamon Redux runs in Python on any modern system, stores all adventure data as readable JSON files, and features a **classless character system** — any character can learn any spell, use any weapon, and develop any skill over time. All adventures begin and end at the **Main Hall of the Free Adventurers**, where your character is stored between sessions, loot can be sold, new adventures are chosen, and a handful of memorable NPCs will help — or hinder — your progress.

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
├── tavern.py              # Start here — runs the Main Hall of the Free Adventurers
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

### The Main Hall of the Free Adventurers

When you start the game with `python3 tavern.py`, you arrive at the Main Hall of the Free Adventurers — the Guild's headquarters and your home base. Unlike a simple menu screen, the Main Hall is a **navigable space** with multiple rooms, each with its own NPC and purpose. Navigate it with the same directional commands you use inside adventures.

---

## Creating a Character

### Rolling Stats

All six stats are rolled randomly using three six-sided dice (3d6). After seeing the results, you may keep them or reroll as many times as you like — there is no limit. When you are satisfied, confirm to save your character.

**What 3d6 means:** Three six-sided dice are rolled and added together. The result is between 3 (all ones) and 18 (all sixes). Most results fall in the 9–12 range — consider any stat above 14 excellent and any below 8 challenging.

There are no classes in Eamon Redux. Every character can use any weapon, wear any armor, and learn any spell. Your stats determine how effective you are — a high STR makes you hit harder, a high INT powers your offensive spells, a high WIS improves healing and resistance to magic.

**During character creation, type `?` at the "Keep these stats?" prompt to display a full stat reference.**

---

## Character Stats

Every character has six core statistics, following the classic D&D model. These are set at creation and persist across adventures. Marie Laveau in the Main Hall can raise them for a steep fee.

The **stat bonus formula** used throughout the game is: `(stat − 10) ÷ 2`, rounded down. A stat of 10 gives no bonus (+0). A stat of 14 gives +2. A stat of 18 gives +4. A stat of 8 gives −1.

### STR — Strength

Strength is raw physical muscle. It affects how hard you hit in melee combat and how much you can carry.

- **Melee Damage Bonus** = (STR − 10) ÷ 2. Added to every melee weapon damage roll.  
  STR 14 → +2 damage per hit. STR 18 → +4 damage per hit.
- **Carry Capacity** = STR × 10 gronds. STR 12 → 120 gronds. STR 16 → 160 gronds.

Weight in Eamon Redux is measured in **gronds**. A rusty sword might weigh 3 gronds; a coat of chainmail might weigh 6. Exceeding your carry limit prevents picking up anything more.

> STR does **not** affect ranged weapons (bows, crossbows). Ranged attacks use weapon dice only.

### DEX — Dexterity

Dexterity governs speed, reflexes, and accuracy. It is the primary combat stat for both attack and defence.

- **Hit Chance Bonus** = (DEX − 10) ÷ 2. Added to your hit roll for both melee and ranged attacks.
- **AC Defence** = (DEX − 10) ÷ 2. Subtracted from the monster's chance to hit you (alongside your armour).
- **Initiative Bonus** = (DEX − 10) ÷ 2. Added to your initiative roll at the start of each combat round.
- **Speed Spell** — doubles your current DEX for 11–20 rounds, dramatically improving hit chance and initiative.

DEX 16 → +3 to hit, +3 AC, +3 initiative. With Speed active: effectively DEX 32, +11 to all three.

### CON — Constitution

Constitution is your physical endurance and toughness.

- **Hit Points (HP)** = CON × 2. CON 10 → 20 HP. CON 16 → 32 HP.

That is its only mechanical effect — but it is a critical one. A character with high CON survives more punishment and needs to heal less often.

### INT — Intelligence

Intelligence governs magical aptitude and the strength of offensive spells.

- **Mana Pool** = INT × 2. INT 12 → 24 mana. INT 16 → 32 mana.
- **Blast Spell Bonus** = (INT − 10) ÷ 2. Added to Blast damage.

INT does **not** affect healing magic (that is WIS). Focus INT if you want to cast more often and deal more damage with Blast.

### WIS — Wisdom

Wisdom governs intuition, spiritual attunement, and resilience to supernatural threats.

- **Heal Spell Bonus** = (WIS − 10) ÷ 2. Added to HP restored by the Heal spell.
- **Saving Throw Bonus** = (WIS − 10) ÷ 2 × 5%. Added to your base 50% chance to resist monster special attacks (fear, paralysis, charm, magic).

WIS 14 → +2 Heal bonus, +10% saving throws. A wise character heals more effectively and shrugs off debilitating effects more readily.

### CHA — Charisma

Charisma is personality, appearance, and social grace. It affects NPC reactions and merchant pricing.

- **Weapon and spell shops** — CHA ≥ 15 earns a random 5–15% discount; CHA ≤ 8 adds a 5–10% surcharge.
- **Marie Laveau** — CHA ≥ 16 shifts her attitude one step in your favour; CHA ≤ 7 shifts it one step against you.
- **Adventure NPCs** — reactions are adventure-dependent and may gate dialogue, recruitment, or quests.

CHA has no effect in combat.

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

Combat proceeds in **rounds**. When you type `ATTACK <monster>`, one full round takes place:

1. **Initiative** is rolled to determine who acts first.
2. **You attack** (unless the monster won initiative and you didn't survive).
3. **The monster counterattacks** (unless you won initiative and it didn't survive, or it already attacked in step 1).

Hostile monsters also attack at the end of most other actions — picking things up, opening containers — so staying in a room with an angry enemy is always dangerous. Neutral monsters will fight back if you attack them, but won't initiate combat.

### Initiative

At the start of each combat round, both sides roll for initiative:

```
Player Initiative  = 1d6 + DEX Bonus
Monster Initiative = 1d6 (flat)
```

Higher roll acts first. Ties go to the player. If the monster wins, it strikes before your attack — you could be killed before you swing. High DEX is your best protection against this.

**Example:** DEX 16 (+3 bonus). You roll 4 + 3 = 7. Monster rolls 5. You go first.  
**Example:** DEX 8 (−1 bonus). You roll 3 − 1 = 2. Monster rolls 4. Monster strikes first.

### The Attack Roll

When you attack, the game calculates your **hit chance**:

```
Hit Chance = 50 + DEX Bonus + Weapon Proficiency − Monster AC
```

Clamped to a minimum of 5% and maximum of 95%. DEX governs hit chance for **both melee and ranged** attacks.

**Example:** DEX +2, sword proficiency +15%, monster AC 2.
```
Hit Chance = 50 + 2 + 15 − 2 = 65%
```
You hit on a roll of 65 or lower.

### Ranged vs. Melee

Bows and other ranged weapons (crossbow, sling, dart, thrown) use DEX for hit chance but add **no stat bonus to damage** — you deal weapon dice only. Melee weapons add your STR bonus to damage.

| Type | Hit Stat | Damage |
|---|---|---|
| Melee (sword, axe, etc.) | DEX bonus | Weapon dice + STR bonus |
| Ranged (bow, crossbow, etc.) | DEX bonus | Weapon dice only |

A high-DEX, low-STR character is a natural archer: hitting reliably but not hitting hard in melee.

### Fumbles (4% Chance on Any Attack)

Every attack has a 4% chance of a **fumble**:

| Fumble Type | Chance | Effect |
|---|---|---|
| Recover | 35% | You stumble but regain your footing. No damage dealt. |
| Drop Weapon | 40% | Your weapon clatters to the ground. You're unarmed next round. |
| Break Weapon | 20% | Your weapon shatters. 50% chance of 1d4 self-damage. |
| Hit Yourself | 4% | You accidentally swing at yourself for 2d6 damage. |
| Fatal Wound | 1% | You fatally wound yourself. Adventure ends. |

If the monster already attacked this round (it won initiative), a fumble ends your turn without a monster counterattack.

### Normal Hit and Damage

**Melee:**
```
Damage = Weapon Dice + STR Bonus − Monster AC  (minimum 1)
```

**Ranged:**
```
Damage = Weapon Dice − Monster AC  (minimum 1)
```

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

There are no spell restrictions in Eamon Redux. Any character can learn and cast any spell. INT determines your mana pool and offensive spell power; WIS determines your healing power and resistance to hostile magic.

To learn spells, visit **Aldric the Mage** in the Magic, Potions and Sundries shop (Common Room → East). You can also find spellbooks in adventures.

### Mana

Casting spells costs **mana**. Your mana pool is Intelligence × 2. If you do not have enough mana for a spell, the cast fails and no mana is spent.

Your mana pool is `INT × 2`. If you do not have enough mana for a spell, the cast fails and no mana is spent.

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

**Cost:** 3 mana | **Damage:** 1d6 + INT bonus (bypasses armor)

#### HEAL

Calls upon restorative magic to knit wounds. Cannot heal above your maximum HP.

```
HEAL
CAST HEAL
```

**Cost:** 2 mana | **Effect:** Restore 1d10 + WIS bonus HP

#### SPEED

Doubles your DEX for 11–20 combat rounds. Since DEX governs hit chance, initiative, and AC defence, this is a powerful all-round combat buff. Fades with a message when it expires.

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

### The Main Hall

Returning to the Main Hall restores your HP and mana to full. Death carries a gold penalty (2 gold per missing HP at revival), but you are never left permanently weakened.

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
LOOK      — describe the current room in full (also: L)
VERBOSE   — always show the full description when entering a room (also: VER)
BRIEF     — show a short description on re-entry after the first visit (also: BR)
```

The room description shows exits, any monsters present, and any visible items. The first time you enter a room you always see the full description. After that, behaviour depends on the current mode:

- **Verbose mode** (default) — full description every time you enter.
- **Brief mode** — a shorter description is shown on re-entry. If the adventure designer did not write a brief description for a room, the full description is used as a fallback.

`LOOK` always shows the full description regardless of mode. The mode resets to Verbose at the start of each adventure.

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

Your carrying capacity is STR × 10 gronds.

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

### Saving in the Main Hall

`SAVE` works at any Main Hall prompt. It writes your character's stats, gold, bank balance, inventory, and equipped items to disk without consuming an adventure save slot. Your character is also saved automatically whenever you leave a shop, use the bank, or quit. Type `SAVE` at any time to force an immediate write.

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

**`is_quest_item`** prevents the item from being sold at Marcus's or Aldric's. It does not remove the item when the adventure ends — quest items follow the character into later adventures unless `adventure_only` is also set.

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

Visit Marcus Marcos (weapons, armor, shields, general gear) or Aldric the Mage (potions, scrolls, spellbooks) to sell items. Your full inventory is shown at the top of each shop screen so you can always see what you are carrying alongside the buy listing.

You can open a shop several ways:

```
BUY / SELL          — open the shop in your current room
MARCUS / CAVIELLI   — open Marcus's shop (must be in his room; otherwise you get directions)
ALDRIC / WIZARD     — open Aldric's shop (must be in his room; otherwise you get directions)
TALK TO marcus      — also opens Marcus's shop
TALK TO aldric      — also opens Aldric's shop
```

Inside the shop, use these commands:

```
S <n>       — sell the numbered item (must not be equipped)
SELL ALL    — sell all eligible items at once, skipping equipped ones
DONE        — leave without selling
```

**Sell prices** are shown in parentheses next to each item in your inventory, e.g. `short sword 2g (10g)` — the first number is carry weight, the second is what Marcus or Aldric will pay. Items bought from the shops resell at roughly one-third of their purchase price. Adventure loot sells at its stated value.

**Equipped items are protected.** They appear in the sell listing marked `[EQUIPPED — unequip first]` and cannot be sold — not even by SELL ALL. Use `UNEQUIP` or `EQUIPMENT` to remove an item before selling it.

Keys and quest items cannot be sold regardless of equipped status.

---

## Buying Equipment and Spells

### Cavielli's Weapons and Armour Shoppe

Marcus Marcos runs the weapon shop east of the Main Hall. His **core stock** — daggers, short swords, leather armor, chainmail, wooden shields, rations, and torches — is always available. A rotating selection of additional weapons and armor appears each session based on your level and completed adventures.

High Charisma earns you a small random discount (up to 15%) on everything Marcus sells.

### Magic, Potions and Sundries

Aldric the Mage operates the magic shop east of the Common Room. He sells all four spells (any character can learn any spell), a rotating selection of potions, and the occasional scroll.

**Spell prices (flat, before Charisma adjustment):**

| Spell | Cost | Effect |
|---|---|---|
| Power  | 100g  | Adventure-specific effect (1 mana) |
| Heal   | 500g  | 1d10 + WIS bonus HP restored (2 mana) |
| Blast  | 1000g | 1d6 + INT bonus damage, bypasses armor (3 mana) |
| Speed  | 4000g | Double DEX for 11–20 rounds (5 mana) |

Spells are not cheap — plan accordingly. Charisma ≥ 15 earns a random 5–15% discount; Charisma ≤ 8 adds a 5–10% surcharge.

You may carry a maximum of **2 potions** at a time.

---

## The Main Hall

### Layout and Navigation

The Main Hall is a navigable space with seven distinct rooms. Move between them using the same directional commands you use inside adventures.

```
              [Marie Laveau's Chamber]
                        │ N
               [Common Room]
               │ S        │ E
           [Main Hall] ─────── [Magic, Potions & Sundries]
           │ W    │ NE
        [Bank]  [Guild Hall]
           │ E
           │ (back to Main Hall)

         S from Main Hall → EXIT (save and leave)
         E from Main Hall → [Cavielli's Weapons & Armour Shoppe]
```

| Room | Direction from Main Hall | NPC |
|---|---|---|
| Main Hall (foyer) | — | — |
| Common Room | North | — |
| Cavielli's Weapons & Armour Shoppe | East | Marcus Marcos |
| Magic, Potions and Sundries | Common Room → East | Aldric the Mage |
| Marie Laveau's Chamber | Common Room → North | Marie Laveau |
| The Main Hall Bank | West | Reginald T. Pemberton |
| Adventurers' Guild Hall | Northeast | (quest board) |

When you first enter a room each session, the NPC there greets you. On subsequent visits you get a shorter acknowledgment.

### Main Hall Commands

Most Main Hall commands are the same as in adventures. A few are unique to this space:

```
ADVENTURE / A       — go to the guild hall and choose an adventure
RESUME / R          — resume a saved adventure from the load menu
LEAVE / QUIT        — Temporarily Leave the Universe (save and exit)
```

Directional shortcuts also work: typing `S` from the Main Hall foyer goes south, triggering the exit. You do not need to type LEAVE explicitly — just walk out.

### Marie Laveau — The Witch

Marie Laveau's chamber is north of the Common Room. For a steep fee (2500–5000 gold, chosen randomly), she will attempt to raise one of your six stats by 1 point. She will never raise a stat by more than 1 per visit.

The key word is *attempt*. Marie keeps track of how she feels about you — her **attitude** ranges from -3 (hostile) to +3 (devoted). Her attitude is shaped by:

- **Persistent attitude** (`marie_attitude` on your character file) — adjusts permanently based on gifts you give her.
- **Session gift bonus** — resets each time you enter the Main Hall; rises and falls with gifts given during that session.
- **Charisma modifier** — Charisma ≥ 16 adds +1; Charisma ≤ 7 subtracts 1.

**Attitude outcomes:**

| Total Attitude | What happens |
|---|---|
| +2 or higher | You get exactly the stat you asked for |
| +1 | 85% chance of your chosen stat, 15% random |
| 0 (neutral) | She raises your *lowest* stat — her call, not yours |
| -1 | Unpredictable: weakest stat, wrong stat, or wrong stat with commentary |
| -2 or lower | 40% chance she takes your gold and does nothing; 60% raises a random stat |

**Changing her attitude** — give her gifts:

```
GIVE <item> TO MARIE    — give her an item as an offering
GIVE <item> TO LAVEAU   — same thing
```

She values items by their sell price:

| Item value | Session bonus | Permanent shift |
|---|---|---|
| 200g or more | +2 this session | +1 permanent |
| 50–199g | +1 this session | none |
| 10–49g | no bonus | none (she notes the effort) |
| under 10g | -1 this session | -1 permanent (she is insulted) |

### The Main Hall Bank

The bank is west of the Main Hall. Reginald T. Pemberton will hold your gold between sessions. Your balance is saved on your character and persists across all adventures.

```
DEPOSIT <amount>    — move gold from your purse to the vault
DEPOSIT ALL         — deposit everything you're carrying
WITHDRAW <amount>   — take gold from the vault
WITHDRAW ALL        — withdraw your entire balance
BALANCE             — show carried gold and vault balance
```

These commands only function inside the bank room. You can also type `BANK` from any room to get directions.

### Temporarily Leaving the Universe

The classic Eamon exit. Walk south from the Main Hall foyer, or type `LEAVE` from the foyer, to save your character and exit the game.

```
S       — from the Main Hall foyer: save and exit
LEAVE   — same effect from the foyer
QUIT    — same effect from anywhere in the Main Hall
```

Your character is saved to disk, your bank balance is preserved, and the game exits cleanly. Everything waits for you when you return.

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
| `LOOK` | `L` | Describe room in full (ignores BRIEF mode) |
| `VERBOSE` | `VER` | Full description on every room entry (default) |
| `BRIEF` | `BR` | Short description on re-entry after first visit |
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
| `SAVE` | `SA` | Save mid-adventure (3 slots); also saves character in Main Hall |
| `LOAD` | `RESTORE` | Load a saved game |
| `HELP` | `H`, `?` | In-game command list |
| `QUIT` | `Q`, `EXIT`, `BYE` | Return to the Main Hall |

### Main Hall Only
| Command | Aliases | Notes |
|---|---|---|
| `ADVENTURE` | `A`, `ADV` | Go to the guild hall and pick an adventure |
| `RESUME` | `R`, `LOAD` | Resume a saved adventure |
| `MARCUS` | `CAVIELLI` | Open Marcus's weapon shop (must be in his room) |
| `ALDRIC` | `WIZARD`, `MAGIC` | Open Aldric's magic shop (must be in his room) |
| `MARIE` | `WITCH`, `LAVEAU` | Enter Marie Laveau's stat-raising service |
| `BANK` | `BA` | Go to the bank (or type from the bank room to interact) |
| `DEPOSIT <amount>` | `DEP` | Deposit gold in the bank |
| `WITHDRAW <amount>` | `WITH`, `WD` | Withdraw gold from the bank |
| `BALANCE` | `BAL` | Show carried gold and bank balance |
| `GIVE <item> TO <npc>` | `GI` | Give an item to an NPC (gifts for Marie) |
| `LEAVE` | `LE`, `EXIT`, `OUTSIDE` | Temporarily Leave the Universe (save and exit) |

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

The menu lists all existing adventures by number. Choose one to open it, `N` to create a new adventure (the designer prompts for a title and creates the directory automatically), `I` to import an adventure from an Eamon Deluxe JSON file, or `0` to quit.

You can also pass a path directly to skip the chooser — useful for scripting or opening an adventure by name:

```bash
python3 designer.py adventures/my_adventure
```

### Importing Adventures from Eamon Deluxe

The original Eamon community produced hundreds of adventures for the Eamon Deluxe (EDX) web system, stored as Django fixture JSON files. The importer converts these into Eamon Redux format automatically.

**From the designer startup menu**, choose `I. Import from Eamon Deluxe (EDX) JSON`. You will be prompted for:

1. **Path to the source JSON file** — e.g., `original_adventures_json/002-lair-of-the-minotaur.json`
2. **Slug / directory name** — the folder name for the imported adventure. Leave blank to auto-generate from the adventure title.

The importer creates `adventures/<slug>/` with `adventure.json`, `rooms.json`, `artifacts.json`, and `monsters.json`, then opens the result in the designer.

You can also run the importer directly from the command line (useful for scripting multiple imports):

```bash
python3 import_eamon.py <source.json> [adventure_slug]
```

**What gets imported automatically:**

| EDX data | Eamon Redux result |
|---|---|
| Adventure title, intro text, author | `adventure.json` metadata |
| Rooms (name, description, `is_dark`) | `rooms.json` — exits resolved from the separate roomexit records |
| Room exits | Direction expanded: n/s/e/w/u/d → north/south/east/west/up/down |
| Artifacts (type codes 0–13) | `artifacts.json` with mapped `artifact_type` |
| Artifact weapon type (1–5) | sword / axe / club / spear / bow |
| Monsters (stats, room, friendliness) | `monsters.json` — hostile/friend/random → hostile/friendly/neutral |

**Items flagged for manual follow-up** are printed at the end of the import. The designer opens the adventure with these requiring attention:

| Situation | Flag message | What to do |
|---|---|---|
| Artifact belongs to a monster (`monster_id` set) | "set as monster loot manually" | Use **Monsters → Edit monster** and set the loot artifact ID |
| Artifact is inside a container (`container_id` set) | "place manually" | Use **Artifacts → Move artifact to room** |
| Artifact is a bound captive (EDX type 10) | "convert to NPC/monster manually" | The captive was a special EDX construct — add an equivalent monster with `is_captive` flags |
| Monster has no room (`room_id` is null or 0) | "place manually" | The monster starts in a container or is spawned by a script — use **Monsters → Move monster to room** |

**After importing, plan to:**

1. Fill in **brief descriptions** — imported rooms have none. Use **Rooms → 7. Fill missing brief descriptions**.
2. Assign **monster loot** — any weapons carried by monsters in EDX need their artifact IDs entered in the monster's loot field.
3. Set the **win condition** — the importer does not infer one from the EDX data.
4. Set a **starting room** — the importer defaults to room 1; verify this is correct in Adventure Settings.
5. Review **room names** — EDX room names are partial phrases ("below the trap door. (S)"); the importer prepends "You are" to each. Review and reword if needed.

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
2. Rooms               — add, edit, exits, locked exits, fill brief descriptions
3. Artifacts           — items, weapons, armor, rings, ...
4. Monsters & NPCs     — enemies, followers, captives
5. View map            — ASCII grid of room connections
6. Save
7. Test play (launch engine)
0. Quit
```

### Rooms

Each room has a name, a **verbose description**, an optional **brief description**, and a set of exits. Exits can point to another room by ID, or to the special code `EXIT_TAVERN` to send the player back to the surface.

The **verbose description** is shown on the first visit and whenever the player types `LOOK` or is in Verbose mode. The **brief description** is shown on re-entry when the player has enabled Brief mode — write it as a one- or two-sentence reminder of where the player is. Leaving it blank causes Brief mode to fall back to the verbose description.

**Adding brief descriptions to existing adventures** — the Rooms menu shows option 7, *Fill missing brief descriptions*, whenever any rooms are still missing one. It displays a running count and streams through each unfilled room in order, showing the room name and the first 80 characters of the verbose description as context. Press Enter to skip a room for now, or type `S` to save progress and stop. The count updates each time you re-enter the Rooms menu so you can work through them in batches.

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

### Where It All Began

Eamon was created by Donald Brown and first published in 1980 for the Apple II. It was one of the first games to separate the adventure engine from the adventure data — meaning anyone could design and share a new dungeon without touching the core program. The Eamon community ran with that idea and produced hundreds of adventures over the following decade, all playable with the same persistent character you built up over time.

### The BBS Years

Before the internet, players connected to each other through Bulletin Board Systems — BBSes — over phone lines at 300 or 1200 baud. Two of those systems left a deep mark on this game:

**AppleVenture ][** and **Starport** were Apple II-based BBSes where adventurers gathered in an online common room called the Saunter Inn. From there you could download and play Eamon adventures, trade tips on Wizardry and Ultima, work through the puzzles of Zork, and swap saves with other players. The games that defined that era — Wizardry I–V, Ultima I–VIII, Zork and its sequels, and Eamon itself — all shared a shelf on those systems, and the players who grew up on them carried that sensibility forward.

The Main Hall of the Free Adventurers in this game — and the Saunter Inn common room within it — is a direct nod to those boards. The spirit is the same: a gathering place between adventures, where your character persists, your gold accumulates, and the next dungeon is always one command away.

### The Eamon / D&D Mashup

The Adventurer's Gate is a spiritual successor to Eamon, rebuilt from scratch in Python — but it takes the original concept one step further by blending it with the mechanics of Advanced Dungeons & Dragons.

The original Eamon used a simple three-stat system (Hardiness, Agility, Charisma). The Adventurer's Gate replaces that with the full D&D six-stat model:

| Stat | Governs |
|---|---|
| STR | Carry weight, melee damage bonus |
| DEX | Hit chance, initiative, ranged combat |
| CON | Hit points at creation |
| INT | Spell learning, BLAST damage bonus |
| WIS | HEAL bonus, spell fatigue recovery |
| CHA | NPC reactions, follower recruitment |

Combat uses D&D-style initiative rolls (1d6 + DEX bonus), attack rolls with weapon proficiency bonuses, armour class, critical hits at 5%, and fumbles at 4%. Magic uses a mana pool rather than spell slots, with fatigue that scales on proficiency — the more you've practiced a spell, the less it costs you.

The adventure format is unchanged from Eamon's original vision: rooms, artifacts, monsters, and a win condition, all in plain data files anyone can edit. The designer program lets you build new adventures without writing a line of code.

### What's the Same, What's Different

| | Original Eamon | The Adventurer's Gate |
|---|---|---|
| Stats | Hardiness / Agility / Charisma | STR / DEX / CON / INT / WIS / CHA |
| Magic | Spell percentages, no resource | Mana pool + fatigue |
| Combat | Simple hit roll | Initiative, AC, proficiency, crits |
| Adventures | BASIC programs + data files | JSON data + Python engine |
| Designer | Separate BASIC program | Built-in Python designer |
| Platform | Apple II | Any system with Python 3 |

The soul of the original is unchanged: a world where you can go anywhere, fight anything, recruit followers, free captives, and tell your own story — with the same character across every adventure you ever play.

---

*The Adventurer's Gate — a D&D / Eamon mashup. No Apple II required, but one is welcome.*
