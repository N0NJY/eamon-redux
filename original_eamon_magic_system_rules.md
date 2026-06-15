The Four Standard Spells:

The original Eamon system utilized four core spells, learned from wizards in the Main Hall. Unlike weapon proficiencies which started at 50%, spell proficiency began randomly between 25% and 75%. 

Blast: Fires a magical projectile that always hits its target if the cast is successful, regardless of range or the target's armor.  It inflicts 1D6 damage (1–6 points).  In some later interpretations (like Eamon Deluxe), this was adjusted to 2D5 (2–10 points), but the defining feature remains that it bypasses armor entirely.

Heal: Restores 1D10 (or fixed 10) hit points to the caster or another living creature.  It cannot raise health beyond the character's maximum "perfect health" limit.

Speed: Temporarily doubles the caster's Agility for a random duration (typically 11–20 turns).  This significantly increases the chance to hit in combat and the likelihood of striking first. Casting it again while active resets the duration but does not stack the agility bonus.

Power: A "wild card" spell with unpredictable effects determined entirely by the specific adventure's designer.  It might teleport the player, destroy an item, summon a monster, or have no effect at all. It serves as a hook for authors to implement unique, scenario-specific magic without altering the core engine. 

Magic System Mechanics:

The magic system was built on a probability-based proficiency model rather than a mana or spell-slot system. 

Casting and Proficiency:

To cast a spell, the player enters the command (e.g., BLAST GOBLIN). The system then checks the character's proficiency percentage for that specific spell:

Success Check: A random number is generated. If the roll is within the character's proficiency percentage, the spell succeeds.

Skill Growth: Upon a successful cast, the system rolls again to determine if proficiency increases.  If a 1D100 roll is less than the chance of failure (100% - current proficiency), the skill increases by 2%.  This creates a diminishing return curve; improving from 90% to 92% is much harder than improving from 30% to 32%.

Failure: If the initial cast fails, nothing happens, and the spell is not "expended," allowing players to retry immediately.

Architectural Design:

The magic system reflected Donald Brown's "splice-and-bind" philosophy:

Localized Reality: The lore justified inconsistent magic by describing Planet Eamon as a gravitational anomaly where physical laws varied by location. This allowed the four standard spells to work universally while permitting adventure authors to override them or add unique spells via BASIC code modifications. 

Hardcoded Logic: The effects of Blast, Heal, and Speed were hardcoded into the main adventure engine (Eamon.name or similar), ensuring consistency across modules. In contrast, Power was intentionally left as a hook for custom code in individual adventure files. 

No Resource Cost: Spells did not consume gold, mana, or items upon casting. The only "cost" was the initial training fee paid to the wizard and the risk of failure due to low proficiency. 

Specific instructions for using this:

A) let's stick to this as closely as possible.
B) Modify the system files to match it as closely as possible.
C) Code error checks



The "Power" Spell Specifics
The Power spell was unique because it contained no hardcoded effect in the main engine.  Instead, it functioned as a dedicated subroutine hook (Power or SpellCast4) that adventure authors were expected to overwrite with custom BASIC code. 

Default Behavior: In the unmodified Main Program, casting Power often resulted in a generic message (e.g., "Nothing happens" or a "sonic boom") or simply branched to a return statement, effectively doing nothing unless the specific adventure file (adventure.name) contained custom logic. 
Design Intent: It was explicitly designed as a "wild card" to allow authors to implement scenario-specific magic—such as teleporting the player, destroying a specific artifact, or triggering a plot event—without needing to rewrite the entire spellcasting engine. 
Implementation: Authors would locate the Power routine in the source code and insert their own GOTO statements or conditional logic (e.g., IF room = 45 THEN...) to define the outcome.
Hardcoded Mechanics and Percentages
The underlying magic system relied on strict mathematical formulas hardcoded into the Applesoft BASIC engine (MAINPGM). 

1. Proficiency and Growth Formula
Starting Value: When learned, a spell's proficiency is randomly set between 25% and 75%. 
Success Check: The system generates a random number (1–100). If the roll is $\le$ current proficiency, the spell succeeds. 
Skill Increase: Upon a successful cast, the system attempts to increase proficiency:
It rolls 1D100 again.
If this second roll is less than the chance of failure ($100 - \text{current proficiency}$), the skill increases by exactly 2%.
Example: At 30% proficiency, there is a 70% chance to increase to 32%. At 90%, there is only a 10% chance to increase to 92%. 

2. The "Fatigue" Mechanic (Halving Rule)
A critical, often overlooked hardcoded rule is the cumulative fatigue penalty:

The Rule: Every time a spell is cast (regardless of success or failure), the caster's effective chance for the next cast is halved for the remainder of the adventure. 
Progression:
Cast 1: 100% of listed proficiency.
Cast 2: 50% of listed proficiency.
Cast 3: 25% of listed proficiency.
Cast 4: 12.5% (rounded down).

Recovery: Proficiency recovers slightly each turn the player performs a non-casting action (moving, taking items) or by using the REST command. 

Hard Limits:
Minimum Success: The chance to cast can never drop below 5%, ensuring even an exhausted wizard has a slim chance.
Critical Failure: There is a hardcoded 1% chance on any cast that the spell "overloads" the caster's mind, rendering that specific spell unusable for the rest of the adventure.
Critical Success/Failure: Some versions include a flat 5% chance of automatic success or failure regardless of proficiency. 
Recovery Mechanism: During any turn where the player performs a non-magical action (moving between rooms, picking up items, examining objects, or using the REST command), the system restores a portion of the caster's effective proficiency. 
Source Code Logic: In the Applesoft BASIC source code, this is typically implemented as a small, incremental addition to the current "effective chance" variable (often restoring 5% to 10% of the base proficiency or a flat small integer per turn), counteracting the halving penalty.
Strategic Implication: Because the recovery is "slight" compared to the severe 50% reduction per cast, players cannot sustain continuous casting.  The system forces a rhythm of Cast → Act/Move → Cast, ensuring that magic remains a tactical support tool rather than a primary spam-able damage source.

Character Classes and Magic Learning
In the original Eamon system, there were no character classes.  Any adventurer could learn magic regardless of their attributes or background. 

Universal Access: The system did not restrict spellcasting to specific "wizard" or "mage" classes. Any character could visit a wizard in the Main Hall and pay gold to learn any of the four standard spells (Blast, Heal, Speed, Power).
No Attribute Requirements: Unlike weapon proficiencies which relied heavily on Agility, or armor which relied on Hardiness, learning magic had no minimum attribute thresholds.  A character with low stats could theoretically become a powerful spellcaster if they survived long enough to increase their spell proficiency.

Cost-Based Limitation: The only barrier to entry was economic. Players started with 200 gold pieces, and each spell cost a varying amount (often 50–100+ gold) to learn. This forced new players to choose between buying better weapons/armor or investing in magic. 

Magic Users and Weapons
Magic users could absolutely use weapons, and the system actively encouraged hybrid combat styles. 

No Mutual Exclusivity: Learning or casting spells did not prevent a character from wielding weapons. There were no "spell failure" chances for wearing armor, nor were there restrictions on using weapons while knowing spells. 
Tactical Synergy: Because the magic system used a fatigue mechanic (halving effective proficiency with consecutive casts), players often alternated between casting spells and attacking with weapons. This allowed the caster's "effective chance" to recover between turns while still dealing damage.

Independent Progression: Weapon skills and spell proficiencies were tracked separately. A character could simultaneously have 90% proficiency with a Club and 80% proficiency with Blast, switching between them as the situation demanded. 
Equipment Flexibility: A "mage" could wear any armor type (Leather, Chain, Plate) and use any shield without penalty to their spellcasting ability. The only downside to heavy armor was the standard reduction to hit chance in melee, which applied to everyone regardless of whether they knew magic. 
