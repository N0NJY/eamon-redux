# PHASE 5: Systematic Testing Guide

**Status**: Ready for Claude Code implementation  
**Dependency**: Phases 1-4 completed  
**Estimated Time**: 2-3 hours (full test suite)

---

## Objective

Systematically test all game mechanics to ensure:
- Flag system works correctly
- Handler architecture functions properly
- Win conditions trigger at the right time
- No regressions from refactoring

---

## CRITICAL FIX: Generic Follower Checking

**Issue**: Phase 4 hardcoded checking for `has_rescued_girl`

**Solution**: Make it generic to work with ANY follower type

### **Fix 1: Update _check_win_condition() in base_handlers.py**

Replace the hardcoded "has_rescued_girl" section with:

```python
    # ─────────────────────────────────────────────────────────────
    # has_follower:ID (generic follower check)
    # ─────────────────────────────────────────────────────────────
    elif cond_type == "has_follower" and param:
        try:
            follower_id = int(param)
            return any(f.get('id') == follower_id for f in self.engine.player.followers)
        except ValueError:
            pass
    
    # ─────────────────────────────────────────────────────────────
    # has_any_follower (any follower at all)
    # ─────────────────────────────────────────────────────────────
    elif cond_type == "has_any_follower":
        return len(self.engine.player.followers) > 0
```

### **Fix 2: Update Beginner's Cave adventure.json**

**Instead of:**
```json
"win_condition": "has_rescued_girl"
```

**Use one of these (more flexible):**

**Option A** (Recommended - use quest flag):
```json
"win_condition": "quest_completed:rescued_captive"
```
Then when captive is freed, set: `player.quest_flags['rescued_captive'] = True`

**Option B** (Generic follower by ID):
```json
"win_condition": "has_follower:2"
// Checks if player has any follower with id=2 (the captive)
```

**Option C** (Any follower):
```json
"win_condition": "has_any_follower"
// Checks if player has rescued/recruited ANY follower
```

**Recommendation**: Use **Option A** (quest flag) because:
- ✅ More explicit and clear
- ✅ Decoupled from follower ID (flexible)
- ✅ Matches other quest completion patterns
- ✅ Works with ANY captive, not specific to one NPC

---

## Phase 5: Test Suite

### **Category 1: Designer Tool Tests**

#### **Test 1.1: Create Monster with Flags**
```
Steps:
1. python3 designer.py adventures/test-adventure
2. Create new adventure (if needed)
3. Create new room (id=1, "Test Room")
4. Create new monster (id=1, "Test Captive")
5. Edit monster → set flags:
   - is_follower: true
   - follower_type: quest
   - quest_condition: captive_rescued
   - follower_dialogue: "Thank you! I'll follow you!"
6. Save and check adventure.json

Expected:
- Monster has flags dict
- flags contain is_follower, follower_type, quest_condition, follower_dialogue
```

#### **Test 1.2: Create Artifact with Flags**
```
Steps:
1. In designer, create artifact (id=1, "Ancient Key")
2. Edit artifact → set flags:
   - is_tradeable: true
   - trade_npc: wizard
   - trade_dialogue: "Excellent! I'll join you!"
3. Save and check adventure.json

Expected:
- Artifact has flags dict
- flags contain is_tradeable, trade_npc, trade_dialogue
```

#### **Test 1.3: Create Room with Win Flags**
```
Steps:
1. In designer, create room (id=2, "The Exit")
2. Edit room → set flags:
   - is_exit: true
   - is_win_room: true
   - win_condition: quest_completed:rescued_captive
   - win_dialogue: "You escape! You've won!"
3. Save and check adventure.json

Expected:
- Room has flags dict
- flags contain is_exit, is_win_room, win_condition, win_dialogue
```

---

### **Category 2: Engine Tests - Basic Movement**

#### **Test 2.1: Movement Works**
```
Steps:
1. python3 tavern.py
2. Create character
3. Choose test adventure
4. From starting room, try:
   - NORTH / SOUTH / EAST / WEST
   - GO NORTH
   - U (UP) / D (DOWN)

Expected:
- Player moves to connected rooms
- LOOK shows new room description
- Exits show correctly
```

#### **Test 2.2: Dark Rooms Work**
```
Steps:
1. In designer, create dark room
2. Start adventure, go to dark room
3. Try LOOK

Expected:
- See "It is pitch dark" message
- Exits show as "unknown"
```

---

### **Category 3: Inventory & Equipment Tests**

#### **Test 3.1: Pick Up Items**
```
Steps:
1. Start adventure with items in room
2. GET <item name>
3. INVENTORY

Expected:
- Item appears in inventory
- Weight increases
- Can see item in LOOK
```

#### **Test 3.2: Drop Items**
```
Steps:
1. With item in inventory
2. DROP <item name>
3. LOOK

Expected:
- Item appears in room
- Inventory shows item gone
- Weight decreases
```

#### **Test 3.3: Equip Weapon**
```
Steps:
1. GET sword (or any weapon)
2. EQUIP sword
3. EQUIPMENT

Expected:
- Weapon shows as equipped in weapon slot
- INVENTORY shows [equipped: weapon]
```

---

### **Category 4: NPC & Follower Tests**

#### **Test 4.1: Talk to NPC (Basic)**
```
Steps:
1. Start adventure
2. Find NPC with dialogue
3. TALK TO <npc name>

Expected:
- Dialogue displays
- No crash
```

#### **Test 4.2: Recruit Follower (Quest Type)**
```
Setup:
- NPC with is_follower: true, follower_type: quest, quest_condition: test_quest
- Player can set quest_flags['test_quest'] = True somehow

Steps:
1. Set quest flag (manually or via event)
2. TALK TO <npc name>

Expected:
- NPC joins as follower
- follower_dialogue displays
- NPC appears in INVENTORY (or separate followers list)
```

#### **Test 4.3: Recruit Follower (Stat Type)**
```
Setup:
- NPC with is_follower: true, follower_type: stat, required_stat: charisma, required_stat_value: 12
- Character with charisma >= 12

Steps:
1. Create character with charisma >= 12
2. TALK TO <npc name>

Expected:
- NPC joins
- follower_dialogue displays
```

---

### **Category 5: Item Mechanics Tests**

#### **Test 5.1: Quest Item (Can't Sell)**
```
Setup:
- Artifact with is_quest_item: true
- Return to tavern

Steps:
1. GET <quest item>
2. Return to tavern (exit adventure)
3. Try to sell it to Horace

Expected:
- Item NOT offered for sale
- Can carry but never sell
```

#### **Test 5.2: Trade Item**
```
Setup:
- Artifact with is_tradeable: true, trade_npc: target_npc, trade_dialogue: message
- Target NPC in adventure

Steps:
1. GET <tradeable item>
2. TALK TO <target npc>

Expected:
- Trade dialogue displays
- (Follower mechanic could trigger)
```

---

### **Category 6: Combat Tests**

#### **Test 6.1: Combat Works**
```
Steps:
1. Find hostile monster
2. ATTACK <monster>
3. Repeat until monster dead

Expected:
- Combat messages display
- Monster takes damage
- Player takes damage
- Combat ends when monster hp <= 0
```

#### **Test 6.2: Monster Death Triggers Handler**
```
Steps:
1. Set up custom handler to track kills
2. Defeat a monster
3. Check if on_monster_defeated handler called

Expected:
- Handler executes
- Quest flag set (if configured)
```

---

### **Category 7: Win Condition Tests**

#### **Test 7.1: reach_room Win Condition**
```
Setup:
- Room with flags: is_win_room: true, win_condition: reach_room:5

Steps:
1. Move to room 5

Expected:
- Win dialogue displays
- Game ends with exit code 1
- Return to tavern
```

#### **Test 7.2: quest_completed Win Condition**
```
Setup:
- Room with flags: is_win_room: true, win_condition: quest_completed:main_quest
- Way to set player.quest_flags['main_quest'] = True

Steps:
1. Trigger quest completion (defeat NPC, get item, etc.)
2. Move to win room

Expected:
- Win dialogue displays
- Game ends
```

#### **Test 7.3: has_follower Win Condition**
```
Setup:
- Room with flags: is_win_room: true, win_condition: has_follower:2
- NPC with id=2 that can be recruited

Steps:
1. Recruit follower (id=2)
2. Move to win room

Expected:
- Win dialogue displays
- Game ends
```

#### **Test 7.4: kill_monster Win Condition**
```
Setup:
- Room with flags: is_win_room: true, win_condition: kill_monster:1
- Monster with id=1

Steps:
1. Defeat monster 1
2. Move to win room

Expected:
- Win dialogue displays
- Game ends
```

---

### **Category 8: Handler Architecture Tests**

#### **Test 8.1: Generic Handlers Work (No Custom)**
```
Steps:
1. Ensure adventure has NO handlers.py
2. Run adventure
3. Verify all mechanics work with base_handlers

Expected:
- Game runs fine
- All flag-based mechanics work
- No ImportError
```

#### **Test 8.2: Custom Handlers Override**
```
Setup:
- Create adventures/test-adventure/handlers.py
- Add custom on_enter_room handler

Steps:
1. Run adventure
2. Enter room with custom logic
3. Verify custom handler executed

Expected:
- Custom handler called
- Custom behavior executes
- Base handler doesn't interfere
```

---

## Test Execution Checklist

- [ ] Fix _check_win_condition() in base_handlers.py (remove hardcoded "girl")
- [ ] Update Beginner's Cave adventure.json win_condition (use quest flag)
- [ ] Test 1.1: Designer - Monster with flags
- [ ] Test 1.2: Designer - Artifact with flags
- [ ] Test 1.3: Designer - Room with flags
- [ ] Test 2.1: Movement works
- [ ] Test 2.2: Dark rooms work
- [ ] Test 3.1: Pick up items
- [ ] Test 3.2: Drop items
- [ ] Test 3.3: Equip weapon
- [ ] Test 4.1: Talk to NPC
- [ ] Test 4.2: Recruit follower (quest type)
- [ ] Test 4.3: Recruit follower (stat type)
- [ ] Test 5.1: Quest item mechanics
- [ ] Test 5.2: Trade mechanics
- [ ] Test 6.1: Combat works
- [ ] Test 6.2: Monster death handler
- [ ] Test 7.1: reach_room win condition
- [ ] Test 7.2: quest_completed win condition
- [ ] Test 7.3: has_follower win condition
- [ ] Test 7.4: kill_monster win condition
- [ ] Test 8.1: Generic handlers (no custom)
- [ ] Test 8.2: Custom handlers override

---

## Bug Report Format

If you find a bug, document it like this:

```
TEST: [Test Name]
EXPECTED: [What should happen]
ACTUAL: [What actually happened]
STEPS TO REPRODUCE: [How to make it happen again]
SEVERITY: [Critical / High / Medium / Low]
```

---

## Claude Code Session Start

```
I'm implementing Phase 5: Systematic Testing Guide for Eamon Redux.

PHASE 5: Systematic Testing

Current situation:
- Phases 1-4 completed ✅
- All systems in place
- Need to run systematic tests
- ONE CRITICAL FIX: base_handlers.py has hardcoded "girl" check

Deliverables:
1. Fix _check_win_condition() to support:
   - has_follower:ID (check for specific follower)
   - has_any_follower (any follower)
   - Remove hardcoded "has_rescued_girl"

2. Update Beginner's Cave adventure.json:
   - Change win_condition from "has_rescued_girl" to "quest_completed:rescued_captive"
   - (More flexible, not tied to specific NPC name)

3. Create test adventure with all mechanics

Repository: ~/git/Eamon/eamon-redux/

Steps:
1. View core/base_handlers.py _check_win_condition() method
2. Fix it to support generic follower checking
3. Update adventures/001-beginners-cave/adventure.json
4. Test: python3 tavern.py, play through Beginner's Cave

Let's start: View the _check_win_condition() method.
```

---

**After Phase 5**: Full system tested and working!  
**Status**: Nearly production-ready 🚀
