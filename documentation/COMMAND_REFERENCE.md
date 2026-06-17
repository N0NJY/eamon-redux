# Command Abbreviations Quick Reference

## Common Shortcuts (Most Used)

### Movement
```
n           north         s           south
e           east          w           west
u           up            d           down
```

### Essential Actions
```
l           look          i           inventory
ex          examine       ca          cast
a           attack        dr          drop
```

### Information
```
hp          health        sp          spells
?  or  h    help          ch          character (tavern only)
```

### Game Control
```
q           quit          sa          save
lo          load          res         rest
```

---

## Extended Abbreviations (All Options)

### Examination & Reading
```
l       look            x, ex, exa   examine
re      read            ta           talk
```

### Inventory & Objects
```
i, inv, in          inventory       ge          get
ga                  get all         dr          drop
op                  open            cl          close
ea                  eat             di          drink
ul                  unlock
```

### Equipment
```
eq                  equip           un          unequip
wear, wield         equip aliases   remove      unequip alias
equ                 equipment (3 chars min)
```

### Combat
```
a, att, kill        attack          ca          cast
fl                  flee            k           kill (alias for attack)
```

### Magic & Abilities
```
sp, spell           spells          res         rest
```

### Game Control
```
h, ?                help            q           quit
exit, bye           quit aliases    sa          save
lo                  load
```

---

## Tavern-Only Commands

### Navigation & Character
```
n, s, e, w          directions      ch, cha     character
sheet               character alias i, inv, in  inventory
sp, spell           spells
```

### Shopping
```
b                   buy             se          sell
ho, shop            horace          wiz, magic  wizard
aldric              wizard alias
```

### Adventures
```
a, ad, adv          adventure       r, res      resume
load                resume alias    ne          new
```

---

## Tips for Fast Playing

### Minimum Typing Strategy
Use the shortest option for maximum speed:
- **Movement**: `n/s/e/w/u/d` (1 char) ⚡
- **Combat**: `a <enemy>` or `ca <spell>` (2 chars) ⚡  
- **Inventory**: `i` to check, `ex <item>` to examine (1-2 chars) ⚡
- **Status**: `hp` for health, `sp` for spells (2 chars) ⚡
- **Control**: `q` to quit, `h` for help (1 char) ⚡

### Common Command Chains
```
n ex sword          (move north, examine sword)
ex corpse get all   (examine corpse, get everything)
ca fireball orc     (cast fireball, target orc)
dr all rest         (drop everything, rest)
i ea potion         (check inventory, eat a potion)
```

---

## Special Cases

### "h" Priority
- **In adventure**: `h` → help (use `hp` for health)
- **In tavern**: `h` → help (same as adventure)

### Directional Shortcuts
All cardinal directions work with single letter:
```
n/s/e/w/u/d      Any context (engine or tavern)
```

### Context Matters
These work differently in tavern vs. adventure:
```
a   → adventure (tavern)      a   → attack (adventure)
ch  → character (tavern)      (not available in adventure)
sp  → spells (both contexts)  sp  → spells (both contexts)
```

---

## If You Get Stuck

### "Ambiguous" Error
If the parser doesn't recognize your command:
```
Wrong:  "b"  (too short for buy/both/bow)
Right:  "b"  → buy (tavern context - works!)
Right:  "ga" → get all (in adventure)
```

### "Unknown Command" Error
The parser didn't find any match. Try:
1. Type more characters (at least 2-3)
2. Use the full command name
3. Type `h` or `?` to see all available commands
4. Check you're using the right context (tavern vs. adventure)

---

## Cheat Sheet by Goal

### "I want to..."

**...explore the dungeon**
```
n/s/e/w/u/d    move around
l              look at room
ex             examine something
```

**...fight a monster**
```
a goblin       attack the goblin
ca fireball    cast a spell
fl             flee if losing
```

**...manage inventory**
```
i              check what I have
get sword      pick up a sword
dr all         drop everything
eq sword       equip the sword
```

**...check my status**
```
hp             how healthy am I?
sp             what spells do I know?
ch             show my full character sheet
```

**...play the game**
```
h              what can I do?
q              quit and save progress
lo             resume a saved game
```

---

**Tip**: The more you abbreviate, the faster you play! But you can always type full commands too.
