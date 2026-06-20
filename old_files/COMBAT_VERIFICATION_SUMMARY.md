# Full Combat Suite — Verification Plan Summary

**Date:** June 17, 2026  
**Status:** Ready for testing  
**Scope:** All weapon types, crits, fumbles, proficiency tracking under pressure

---

## WHAT WE'VE PREPARED

### 1. **COMBAT_TEST_CHECKLIST.md** ✅
Comprehensive step-by-step testing guide covering:
- All 6 weapon types (sword, dagger, axe, bow, club, unarmed)
- Critical hits (5% frequency, 5 tiers: ignore armor, 1.5×, 2×, 3×, instant kill)
- Fumbles (4% frequency, 5 outcomes: recover, drop, break, hit self, kill self)
- Weapon proficiency growth (skill increases on hits)
- Speed spell mechanics (11-20 round duration, monster attack decrements)
- Monster counter-attacks (hit/miss, damage calculation)
- Extended stress test (50+ hits without crashes)
- Edge cases (crit kills, fumble during unarmed, etc.)

**Use this for:** Manual testing in the actual game

---

### 2. **ENGINE_COMBAT_CODE_REVIEW.md** ✅
Critical analysis of combat logic in engine.py identifying:

**Issues Found:**
- 🔴 **HIGH:** Instant kill skips XP/loot rewards (line 1046)
- 🔴 **HIGH:** Unarmed proficiency never grows (line 917 + 1083)
- 🟡 **MEDIUM:** Hit chance unclamped (can exceed 100% or go negative)

**Recommended Fixes:**
All three issues are documented with exact code changes

**Use this for:** Identifying bugs before testing, understanding combat flow

---

### 3. **combat_test_harness.py** ✅
Standalone Python script that simulates 100 attacks without the full game:
- Configurable player/monster stats
- Tracks all dice rolls, crits, fumbles
- Validates frequencies match expected percentages
- Shows detailed statistics and validation results

**Use this for:** Quick smoke test of combat math (before git push, takes 1 second)

**How to run:**
```bash
cd /mnt/user-data/outputs
python3 combat_test_harness.py
```

**Expected output:**
```
Hit rate: 55.0% ✓ (reasonable)
Fumble rate: 4.2% ✓ (~4%)
Crit rate: 5.1% ✓ (~5%)
Proficiency growth: +12% ✓ (reasonable)
```

---

### 4. **PROFICIENCY_TRACKER_VERIFICATION.md** ✅
Detailed guide for validating weapon proficiency system:
- Initialization (all 6 weapons created at start)
- Runtime growth (increases on successful hits)
- Persistence (saved/loaded correctly)
- Separate tracking (each weapon type independent)
- Data structure validation
- Python validation script to check JSON files

**Use this for:** Verifying proficiency system works correctly

---

## RECOMMENDED TESTING SEQUENCE

### Phase 1: Code Review & Quick Test (Today)
1. ✅ Read ENGINE_COMBAT_CODE_REVIEW.md
2. ✅ Run combat_test_harness.py (takes 1 sec)
3. ✅ Review identified issues (instant kill, unarmed proficiency, hit clamping)

### Phase 2: Fix High-Priority Issues (Before git push)
1. Fix instant kill to award XP/loot (3 lines of code)
2. Fix unarmed proficiency tracking (1 line of code)
3. Optional: Clamp hit chance (1 line of code)

### Phase 3: Manual Testing (At computer)
1. ✅ Create new Fighter character
2. ✅ Follow COMBAT_TEST_CHECKLIST.md sections 1-6
3. ✅ Use PROFICIENCY_TRACKER_VERIFICATION.md to validate proficiency data
4. ✅ Test 50+ hit stress scenario
5. ✅ Document any issues found

### Phase 4: Validate & Commit
1. ✅ Verify no crashes, stat corruption
2. ✅ Confirm all frequencies match (~4% fumble, ~5% crit, ~5% hit for balanced stats)
3. ✅ Check proficiency growth is reasonable
4. ✅ Commit to GitHub with: "Test: Full combat suite working (all weapon types, crits, fumbles, proficiency)"

---

## KEY FINDINGS FROM CODE REVIEW

### BUG 1: Instant Kill Doesn't Award Rewards
**Location:** engine.py lines 1046–1049

**Problem:** When critical hit tier 5 triggers, monster dies but XP and loot are not awarded

**Current code:**
```python
else:
    print(self.tc(f"INSTANT KILL!", "win"))
    monster.hp = 0
    monster.is_alive = False
    return  # ← Skips XP/loot logic below
```

**Fix:** Before returning, execute XP/loot code (copy from lines 1067–1079)

**Impact:** Players won't be rewarded for rare instant kills

---

### BUG 2: Unarmed Proficiency Never Grows
**Location:** engine.py lines 917 + 1083

**Problem:** Unarmed attacks don't have a weapon_type, so proficiency check fails

**Current code (line 917):**
```python
weapon_type = None
if weapon:
    weapon_type = weapon.weapon_type
```

**Fix:** Change to:
```python
weapon_type = "unarmed" if not weapon else weapon.weapon_type
```

**Impact:** Unarmed characters never improve at barehanded combat

---

### MINOR: Hit Chance Unclamped
**Location:** engine.py line 951

**Problem:** Hit chance can exceed 100% or go negative in extreme cases

**Current:** No bounds checking
**Proposed:** Clamp to 5-95% range

**Impact:** Low priority — only affects extreme cases

---

## TESTING EXPECTATIONS

### Hit Rate
- **New Fighter with sword vs weak monster:** ~55-65%
  - Base 50% + AGI bonus (~+1) + Proficiency 50% - Monster AC 0 = 101%
  - (Gets clamped to 95% if bounded, or just hits every time)
- **After proficiency growth:** Hit rate should increase slightly

### Fumble Rate
- **Expected:** ~4% (1 in 25 attacks)
- **Range:** 2-6% is acceptable (randomness)

### Critical Hit Rate
- **Expected:** ~5% of hits (0.25% of total attacks)
- **Range:** 3-7% is acceptable

### Proficiency Growth
- **At 50% proficiency:** ~50% chance to grow per successful hit
- **After 20 hits:** Proficiency should increase by +4 to +10
- **Per session:** Sword might go 50% → 58-65% after extended combat

### Monster Attacks
- **Should appear after every player attack** (if monster alive)
- **Hit rate:** Lower than player (50% base, affected by player AC)
- **Damage:** Should be 1-6 (1d6), minus player AC

---

## BEFORE YOU TEST

### Setup Checklist
- [ ] Download corrected engine.py and tavern.py
- [ ] Push to GitHub (when ready)
- [ ] Have Beginner's Cave adventure available
- [ ] Create test characters (Fighter + Sorcerer)
- [ ] Print or reference COMBAT_TEST_CHECKLIST.md

### Pre-Test: Run Harness
```bash
python3 combat_test_harness.py
```

Should see:
- Hit rate 40-80%
- Fumble rate 2-6%
- Crit rate 3-7%
- Proficiency growth +2-15%
- No issues found (or known issues listed)

---

## IF YOU FIND ISSUES

**Document them with:**
1. **What:** Brief description
2. **Expected:** What should happen
3. **Actual:** What happened instead
4. **Steps to reproduce:** How to trigger it
5. **Severity:** Critical / High / Medium / Low

**Example:**
```
ISSUE: Instant kill doesn't award XP
Expected: Monster dies, player gains XP
Actual: Monster dies, no XP message, proficiency not awarded
Steps: Get critical hit tier 5 (rare, takes ~2000 attacks or luck)
Severity: High (affects rare case, but player loses rewards)
```

---

## SUCCESS CRITERIA

### Combat system is fully tested when:
- ✅ All 6 weapon types attack correctly
- ✅ Crits occur at expected frequency (~5%)
- ✅ Fumbles occur at expected frequency (~4%)
- ✅ All crit tiers trigger (5 total)
- ✅ All fumble outcomes trigger (5 total)
- ✅ Weapon proficiency increases on hits
- ✅ Multiple weapons tracked independently
- ✅ Speed spell works (duration, decay)
- ✅ Monster attacks trigger after player attacks
- ✅ No crashes in 50+ hit stress test
- ✅ HP never goes below 0 or above max
- ✅ Edge cases handled (unarmed fumble, crit kill, etc.)

### Known issues before commit:
- 🟡 Instant kill should award XP (awaiting fix)
- 🟡 Unarmed proficiency doesn't grow (awaiting fix)

---

## NEXT STEPS

1. **Today (Code Review):**
   - Read ENGINE_COMBAT_CODE_REVIEW.md
   - Run combat_test_harness.py
   - Plan fixes for bugs 1 & 2

2. **At Computer (Implementation):**
   - Apply 2-3 line fixes for bugs 1 & 2
   - Verify syntax still works
   - Commit to GitHub

3. **Testing Session (Manual):**
   - Follow COMBAT_TEST_CHECKLIST.md
   - Validate with PROFICIENCY_TRACKER_VERIFICATION.md
   - Document findings
   - Create next issue list

---

**All materials ready. Let's get a fully working combat system!** 🎯⚔️

