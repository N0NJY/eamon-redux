# Eamon Redux — Full Combat Suite Test Checklist

**Objective:** Verify all combat mechanics work correctly under pressure (crits, fumbles, proficiency growth, speed spell, monster attacks)

**Test Environment:** Beginner's Cave adventure with Fighter or Sorcerer character

---

## SECTION 1: WEAPON TYPE TESTING
Test each weapon type to ensure basic attacks work and damage is calculated correctly.

### 1.1 Sword Combat (1d6 base damage)
- [ ] **Test Case:** Find a basic sword, equip it, attack a weak monster (e.g., rat in room 3)
- [ ] **Expected:** Hit message shows "You hit <monster> for X damage"
- [ ] **Verify:** Damage is 1-6 (base) + any agility bonus, minus monster AC
- [ ] **Check:** Weapon proficiency shows in SPELLS menu as "sword" at baseline

### 1.2 Dagger Combat (1d4 base damage)
- [ ] **Equip:** Dagger (lower damage than sword)
- [ ] **Attack:** Same rat
- [ ] **Expected:** Damage 1-4 range (lower than sword)
- [ ] **Verify:** Different damage dice work correctly

### 1.3 Axe Combat (1d8 base damage — if available)
- [ ] **Equip:** Axe (Horace's shop or loot)
- [ ] **Attack:** Stronger monster (e.g., goblin)
- [ ] **Expected:** Damage 1-8 range
- [ ] **Verify:** Highest base damage weapon does more damage

### 1.4 Bow Combat (1d6 base damage — ranged, if implemented)
- [ ] **Equip:** Hunting bow
- [ ] **Attack:** Monster
- [ ] **Expected:** Works like melee (range not yet implemented)
- [ ] **Verify:** Bow proficiency tracked separately

### 1.5 Club Combat (1d6 base damage — if in loot)
- [ ] **Equip:** Club
- [ ] **Attack:** Monster
- [ ] **Expected:** 1d6 damage, club proficiency tracked

### 1.6 Unarmed Combat (1d2 base damage)
- [ ] **Unequip:** All weapons
- [ ] **Attack:** Weak monster with bare hands
- [ ] **Expected:** Damage 1-2 per hit (very low)
- [ ] **Verify:** Unarmed proficiency exists and grows

---

## SECTION 2: CRITICAL HIT TESTING (5% chance)
Critical hits should occur roughly 1 in 20 attacks. Test all tiers.

### 2.1 Critical Hit Frequency
- [ ] **Scenario:** Attack same monster 20+ times with good hit chance (high proficiency, good agility)
- [ ] **Count:** Track critical hits
- [ ] **Expected:** ~1 critical per 20 hits (may vary, but roughly 5%)
- [ ] **Check:** Message clearly states "CRITICAL HIT!"

### 2.2 Tier 1: Ignore Armor (50% of crits, ~2.5% overall)
- [ ] **Setup:** Equip light armor (AC +1) on character
- [ ] **Fight:** Attack monster 40+ times, watch for crits
- [ ] **Check:** When "CRITICAL HIT! You bypass the armor!" appears, damage should be full (no AC reduction)
- [ ] **Verify:** Monster takes full damage, not reduced by its AC

### 2.3 Tier 2: 1.5× Damage (35% of crits, ~1.75% overall)
- [ ] **During crit spree:** Watch for "CRITICAL HIT! X damage!" with 1.5× multiplier
- [ ] **Example:** Base 1d6 sword = 4 damage → crit tier 2 = 6 damage (4 × 1.5)
- [ ] **Verify:** Damage is clearly higher than base but not extreme

### 2.4 Tier 3: 2× Damage (10% of crits, ~0.5% overall)
- [ ] **Harder to trigger:** Watch for "CRITICAL HIT! X damage!" with 2× multiplier
- [ ] **Example:** 4 damage → crit tier 3 = 8 damage
- [ ] **Check:** Significantly more damage than normal attacks

### 2.5 Tier 4: 3× Damage (4% of crits, ~0.2% overall)
- [ ] **Rare:** May not see in single session, but should exist
- [ ] **Example:** 4 damage → 12 damage
- [ ] **Verify:** Possible via code inspection

### 2.6 Tier 5: Instant Kill (1% of crits, ~0.05% overall)
- [ ] **Extremely rare:** May require 100+ attacks to see
- [ ] **Message:** "INSTANT KILL!" in gold/yellow
- [ ] **Verify:** Monster HP immediately set to 0 and dies
- [ ] **Code check:** If not seen in testing, verify in engine.py line 1045-1049

---

## SECTION 3: FUMBLE TESTING (4% chance)
Fumbles occur roughly 1 in 25 attacks. Test all outcomes.

### 3.1 Fumble Frequency
- [ ] **Scenario:** Attack monster 25+ times
- [ ] **Count:** Track fumbles
- [ ] **Expected:** ~1 fumble per 25 attacks (roughly 4%)
- [ ] **Check:** Message shows fumble occurred

### 3.2 Tier 1: Recover (35% of fumbles, ~1.4% overall)
- [ ] **Message:** "You fumble the attack but recover!"
- [ ] **Effect:** No damage dealt, monster still attacks
- [ ] **Verify:** No weapon dropped, no injury

### 3.3 Tier 2: Drop Weapon (40% of fumbles, ~1.6% overall)
- [ ] **Message:** "You drop your <weapon>!"
- [ ] **Effect:** Weapon unequipped and placed on ground
- [ ] **Verify:** 
  - [ ] Weapon appears in room inventory (LOOK shows it)
  - [ ] Combat continues unarmed on next round
  - [ ] Can pick up weapon after combat ends

### 3.4 Tier 3: Weapon Breaks (20% of fumbles, ~0.8% overall, with 50% self-injury)
- [ ] **Message:** "Your weapon breaks!"
- [ ] **Effect:** Weapon destroyed, possibly self-damage
- [ ] **Verify:**
  - [ ] Weapon removed from inventory
  - [ ] Check for "The broken weapon cuts you" message (50% chance)
  - [ ] If injured, HP reduced by 1-4 damage

### 3.5 Tier 4: Hit Self (4% of fumbles, ~0.16% overall)
- [ ] **Message:** "You accidentally hit yourself for X damage!"
- [ ] **Damage:** 2-6 HP loss
- [ ] **Verify:** HP visibly decreases, combat continues

### 3.6 Tier 5: Kill Self (1% of fumbles, ~0.04% overall)
- [ ] **Extremely rare:** May not occur in single session
- [ ] **Message:** "You fatally wound yourself!"
- [ ] **Effect:** Character dies immediately
- [ ] **Verify:** Game over screen appears

---

## SECTION 4: WEAPON PROFICIENCY GROWTH
Proficiency increases when attacks land. Track skill growth through combat.

### 4.1 Proficiency Baseline
- [ ] **Check:** New character with fresh weapon (0% or low proficiency)
- [ ] **View:** SPELLS menu → shows weapon proficiencies
- [ ] **Record:** Starting sword proficiency (should be 50% for Fighter, lower for Sorcerer)

### 4.2 Proficiency Growth on Hit
- [ ] **Attack:** Land 10 successful hits with sword on same monster
- [ ] **Watch:** After each hit, message appears: "Your sword proficiency increased: X% → Y%"
- [ ] **Expected:** Growth every few hits (not every hit, skill check involved)
- [ ] **Verify:** After ~10 hits, proficiency is noticeably higher (e.g., 50% → 54%)

### 4.3 Different Weapons Track Separately
- [ ] **Switch:** From sword to axe mid-fight
- [ ] **Attack:** Hit with axe 5 times
- [ ] **Check:** Axe proficiency increases, sword proficiency doesn't change further
- [ ] **Verify:** SPELLS menu shows different values for sword vs axe

### 4.4 Proficiency Persistence
- [ ] **Return to tavern:** After combat ends
- [ ] **Check:** SPELLS menu still shows increased proficiencies
- [ ] **Load character:** Close and reopen character sheet
- [ ] **Verify:** Proficiencies saved (not reset to baseline)

---

## SECTION 5: SPEED SPELL MECHANICS
Speed spell grants 2× agility for 11-20 rounds. Verify duration and decay.

### 5.1 Speed Spell Activation
- [ ] **Sorcerer only:** Create/use Sorcerer character
- [ ] **Learn:** Speed spell from Aldric's shop (if not known)
- [ ] **Cast:** CAST SPEED in combat
- [ ] **Check:** Message shows "Your agility is doubled for X rounds!"
- [ ] **Verify:** Agility bonus visible in next attack's calculation

### 5.2 Speed Duration (11-20 rounds)
- [ ] **In combat:** Cast speed spell
- [ ] **Count:** Each round of combat (player or monster attack) = 1 tick
- [ ] **Round 1-10:** Speed active, hit chance should be higher
- [ ] **Round 11-20:** Randomly selected on cast, speed still active
- [ ] **Round 21:** After duration expires, message: "Your speed enhancement fades."
- [ ] **Verify:** Hit chance returns to normal

### 5.3 Speed Spell Decrement on Monster Attacks
- [ ] **Scenario:** Cast speed, monster attacks
- [ ] **After each monster attack:** Speed duration ticks down
- [ ] **Check:** If duration was, say, 15 rounds, after first monster attack it's 14 rounds
- [ ] **Verify:** Monster round attacks properly decrement speed counter (line 1117 in engine.py)

### 5.4 Speed Spell Fatigue (if applicable)
- [ ] **Cast:** Speed spell multiple times in sequence
- [ ] **Check:** Does fatigue penalty apply? (should be minimal since speed is utility)
- [ ] **Verify:** Second cast costs same as first (no doubling penalty for speed)

---

## SECTION 6: MONSTER ROUND ATTACKS
After player attacks, monsters should attack back. Verify hit/miss and damage.

### 6.1 Monster Attacks After Player Hit
- [ ] **Attack:** Monster with weapon
- [ ] **Check:** Message appears: "<Monster> hits you for X damage!" or "<Monster> misses you."
- [ ] **Verify:** Monster round executes after every player attack
- [ ] **HP Check:** Your HP visibly decreases if hit lands

### 6.2 Monster Hit/Miss Calculation
- [ ] **Setup:** Wear heavy armor (high AC, low hit chance for monster)
- [ ] **Fight:** Attack monster 10 times
- [ ] **Count:** How many misses? Should be frequent with high AC
- [ ] **Formula check:** Hit chance = 50 - player_agility_bonus - player_armor_class
- [ ] **Example:** Monster base 50%, player AC +3, agility bonus -2 → 50 - (-2) - 3 = 49% hit chance

### 6.3 Monster Damage Calculation
- [ ] **Weak monster:** (1d4 damage) — should do 1-4 HP damage
- [ ] **Strong monster:** (1d8 damage) — should do 1-8 HP damage
- [ ] **Armor reduction:** Monster damage minus player AC (floor 1, never 0)
- [ ] **Example:** Monster 1d6 rolls 5, player AC +2 → 5 - 2 = 3 damage taken

### 6.4 Multiple Rounds
- [ ] **Combat:** Fight monster for 5+ rounds (you attack, monster attacks, repeat)
- [ ] **Track:** Each round, both attacks should execute
- [ ] **Verify:** Combat continues until monster dies or you flee

### 6.5 Monster Death
- [ ] **Kill monster:** Reduce HP to 0
- [ ] **Check:** Message: "<Monster> <death_message>"
- [ ] **Gain XP:** "You gain X XP!" appears
- [ ] **Loot:** If monster has loot, it should appear on ground

---

## SECTION 7: STRESS TEST — EXTENDED COMBAT
Fight same monster 50+ times to verify no crashes or stat corruption.

### 7.1 No Crashes
- [ ] **Scenario:** Pick a weak monster (rat, goblin)
- [ ] **Action:** Attack it 50 times without stopping
- [ ] **Check:** No crashes, no error messages
- [ ] **Verify:** Game continues smoothly

### 7.2 Proficiency Growth Stability
- [ ] **Before:** Record weapon proficiency
- [ ] **After 50 hits:** Check proficiency again
- [ ] **Verify:** Proficiency is higher, not corrupted
- [ ] **Example:** Started 50%, now ~65-70% (reasonable growth)

### 7.3 HP Tracking
- [ ] **Throughout:** Track your HP and monster HP
- [ ] **Verify:** Both update correctly each round
- [ ] **No overflow:** HP should never exceed max or go below 0

### 7.4 XP Accumulation
- [ ] **Track:** Total XP before and after 50 hits
- [ ] **Verify:** XP increases each time monster dies and respawns (if it does)
- [ ] **No corruption:** XP value is reasonable

---

## SECTION 8: EDGE CASES & CORNER CASES

### 8.1 Killing Monster with Critical Hit
- [ ] **Scenario:** Monster at low HP, land critical hit that kills it
- [ ] **Check:** Does death message appear correctly?
- [ ] **Verify:** XP and loot still awarded

### 8.2 Fumble Kills Self While Monster Alive
- [ ] **Rare:** Trigger tier 5 fumble (self-kill)
- [ ] **Check:** Do you die immediately even though monster is alive?
- [ ] **Verify:** Game over screen appears

### 8.3 Unarmed Fumble
- [ ] **No weapon:** Attack unarmed
- [ ] **Fumble:** Trigger fumble while unarmed
- [ ] **Verify:** "Drop weapon" fumble doesn't crash (no weapon to drop)

### 8.4 Speed Spell Expires Mid-Combat
- [ ] **Scenario:** Speed spell with 2 rounds left, continue fighting
- [ ] **Round 1:** Monster attacks, speed ticks to 1
- [ ] **Round 2:** Monster attacks, speed ticks to 0, fades message appears
- [ ] **Verify:** No crash, agility bonus removed correctly

---

## TESTING SUMMARY

### Quick Pass/Fail
- [ ] All 6 weapon types attack correctly
- [ ] Crits occur at ~5% frequency
- [ ] Fumbles occur at ~4% frequency
- [ ] Weapon proficiency increases on hits
- [ ] Speed spell lasts 11-20 rounds
- [ ] Monsters attack back each round
- [ ] No crashes in 50+ hit stress test
- [ ] Edge cases handled gracefully

### Issues Found
**List any bugs discovered:**

1. 
2. 
3. 
4. 

### Notes for Next Session
- Prioritize: _______________
- Investigate: _______________
- Test further: _______________

---

**End of Checklist**

