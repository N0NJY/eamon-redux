#!/usr/bin/env python3
"""
Combat Test Harness for Eamon Redux

Simulates combat without needing the full game, allowing quick testing
of damage calculations, critical hits, fumbles, and proficiency growth.

Usage:
    python3 combat_test_harness.py
"""

import random
from dataclasses import dataclass

# ── CONFIG ────────────────────────────────────────────────────────────────────

# Player setup
PLAYER_AGILITY = 12           # Gives +1 bonus
PLAYER_HARDINESS = 10         # 20 HP
PLAYER_ARMOR_CLASS = 1        # From leather armor
WEAPON_PROFICIENCY = 50       # Starting sword proficiency

# Monster setup
MONSTER_ARMOR_CLASS = 0
MONSTER_DAMAGE_DICE = 1
MONSTER_DAMAGE_SIDES = 6
MONSTER_HP_MAX = 15

# Test parameters
NUM_ATTACKS = 100             # How many attacks to simulate
SHOW_EACH_ATTACK = False      # Print every single attack (verbose)

# ── HELPERS ───────────────────────────────────────────────────────────────────

def roll(dice: int, sides: int) -> int:
    """Roll dice. Example: roll(1, 6) -> 1-6"""
    return sum(random.randint(1, sides) for _ in range(dice))

def agility_bonus(agi: int) -> int:
    """Convert agility stat to combat bonus"""
    return (agi - 10) // 2

# ── SIMULATION ────────────────────────────────────────────────────────────────

@dataclass
class CombatStats:
    total_attacks: int = 0
    total_hits: int = 0
    total_misses: int = 0
    total_crits: int = 0
    total_fumbles: int = 0
    total_damage: int = 0
    monster_hp: int = MONSTER_HP_MAX
    player_hp: int = PLAYER_HARDINESS * 2
    proficiency: int = WEAPON_PROFICIENCY
    
    # Crit tiers
    crit_ignore_armor: int = 0
    crit_15x: int = 0
    crit_2x: int = 0
    crit_3x: int = 0
    crit_instant_kill: int = 0
    
    # Fumble tiers
    fumble_recover: int = 0
    fumble_drop: int = 0
    fumble_break: int = 0
    fumble_hit_self: int = 0
    fumble_kill_self: int = 0

def simulate_player_attack(stats: CombatStats) -> None:
    """Simulate one player attack"""
    stats.total_attacks += 1
    
    # Check for FUMBLE (4% chance)
    if random.randint(1, 100) <= 4:
        stats.total_fumbles += 1
        fumble_roll = random.randint(1, 100)
        
        if fumble_roll <= 35:
            stats.fumble_recover += 1
            if SHOW_EACH_ATTACK:
                print(f"  [FUMBLE] Recover (no effect)")
        elif fumble_roll <= 75:
            stats.fumble_drop += 1
            if SHOW_EACH_ATTACK:
                print(f"  [FUMBLE] Drop weapon")
        elif fumble_roll <= 95:
            stats.fumble_break += 1
            damage = random.randint(1, 4) if random.randint(1, 100) <= 50 else 0
            if damage > 0:
                stats.player_hp -= damage
                if SHOW_EACH_ATTACK:
                    print(f"  [FUMBLE] Weapon breaks, you take {damage} damage")
            if SHOW_EACH_ATTACK:
                print(f"  [FUMBLE] Weapon breaks")
        elif fumble_roll <= 99:
            stats.fumble_hit_self += 1
            damage = random.randint(2, 6)
            stats.player_hp -= damage
            if SHOW_EACH_ATTACK:
                print(f"  [FUMBLE] Hit self for {damage} damage")
        else:
            stats.fumble_kill_self += 1
            stats.player_hp = 0
            if SHOW_EACH_ATTACK:
                print(f"  [FUMBLE] Kill self!")
        return
    
    # Calculate HIT CHANCE
    player_agi_bonus = agility_bonus(PLAYER_AGILITY)
    hit_chance = 50 + player_agi_bonus + stats.proficiency - MONSTER_ARMOR_CLASS
    hit_roll = random.randint(1, 100)
    
    if hit_roll > hit_chance:
        stats.total_misses += 1
        if SHOW_EACH_ATTACK:
            print(f"  [MISS] (rolled {hit_roll} vs chance {hit_chance})")
        return
    
    # HIT! Check for CRITICAL (5% chance)
    stats.total_hits += 1
    base_damage = roll(1, 6)  # Sword: 1d6
    damage = base_damage
    ignore_armor = False
    
    if random.randint(1, 100) <= 5:
        stats.total_crits += 1
        crit_roll = random.randint(1, 100)
        
        if crit_roll <= 50:
            stats.crit_ignore_armor += 1
            ignore_armor = True
            if SHOW_EACH_ATTACK:
                print(f"  [CRIT TIER 1] Ignore armor")
        elif crit_roll <= 85:
            stats.crit_15x += 1
            damage = int(damage * 1.5)
            if SHOW_EACH_ATTACK:
                print(f"  [CRIT TIER 2] 1.5× damage: {base_damage} → {damage}")
        elif crit_roll <= 95:
            stats.crit_2x += 1
            damage = damage * 2
            if SHOW_EACH_ATTACK:
                print(f"  [CRIT TIER 3] 2× damage: {base_damage} → {damage}")
        elif crit_roll <= 99:
            stats.crit_3x += 1
            damage = damage * 3
            if SHOW_EACH_ATTACK:
                print(f"  [CRIT TIER 4] 3× damage: {base_damage} → {damage}")
        else:
            stats.crit_instant_kill += 1
            stats.monster_hp = 0
            if SHOW_EACH_ATTACK:
                print(f"  [CRIT TIER 5] INSTANT KILL!")
            return
    
    # Apply armor reduction
    if not ignore_armor:
        damage = max(1, damage - MONSTER_ARMOR_CLASS)
    
    stats.monster_hp -= damage
    stats.total_damage += damage
    
    # Weapon proficiency growth (on hit, not fumble/miss)
    if random.randint(1, 100) < (100 - stats.proficiency):
        stats.proficiency += 2
        if SHOW_EACH_ATTACK:
            print(f"  [GROWTH] Proficiency → {stats.proficiency}%")
    
    if SHOW_EACH_ATTACK:
        print(f"  [HIT] {damage} damage (monster HP: {max(0, stats.monster_hp)})")

def simulate_monster_attack(stats: CombatStats) -> None:
    """Simulate one monster counter-attack"""
    if stats.monster_hp <= 0:
        return
    
    monster_agi_bonus = 0  # Assume 10 AGI (no bonus)
    hit_chance = 50 - agility_bonus(PLAYER_AGILITY) - PLAYER_ARMOR_CLASS
    hit_roll = random.randint(1, 100)
    
    if hit_roll > hit_chance:
        if SHOW_EACH_ATTACK:
            print(f"  [MONSTER MISS] (rolled {hit_roll} vs {hit_chance})")
        return
    
    damage = roll(MONSTER_DAMAGE_DICE, MONSTER_DAMAGE_SIDES)
    damage = max(1, damage - PLAYER_ARMOR_CLASS)
    stats.player_hp -= damage
    
    if SHOW_EACH_ATTACK:
        print(f"  [MONSTER HIT] {damage} damage to you (your HP: {max(0, stats.player_hp)})")

# ── MAIN ──────────────────────────────────────────────────────────────────────

def run_combat_simulation() -> None:
    """Run the full combat simulation"""
    stats = CombatStats()
    
    print("\n" + "="*72)
    print("EAMON REDUX — COMBAT TEST HARNESS")
    print("="*72)
    print()
    print("SETUP:")
    print(f"  Player: AGI {PLAYER_AGILITY}, HP {stats.player_hp}, AC {PLAYER_ARMOR_CLASS}")
    print(f"  Weapon: Sword (1d6), Proficiency {WEAPON_PROFICIENCY}%")
    print(f"  Monster: HP {MONSTER_HP_MAX}, AC {MONSTER_ARMOR_CLASS}, Damage 1d6")
    print(f"\nSIMULATING {NUM_ATTACKS} attacks...")
    print()
    
    attacks_executed = 0
    while attacks_executed < NUM_ATTACKS and stats.monster_hp > 0 and stats.player_hp > 0:
        attacks_executed += 1
        round_num = (attacks_executed + 1) // 2
        
        if SHOW_EACH_ATTACK:
            print(f"Round {round_num}:")
        
        simulate_player_attack(stats)
        if stats.monster_hp <= 0:
            if SHOW_EACH_ATTACK:
                print(f"  Monster defeated!")
            break
        
        simulate_monster_attack(stats)
        if stats.player_hp <= 0:
            if SHOW_EACH_ATTACK:
                print(f"  You have been defeated!")
            break
    
    # ── RESULTS ──────────────────────────────────────────────────────────────
    
    print("\n" + "="*72)
    print("RESULTS")
    print("="*72)
    print()
    
    hit_rate = (stats.total_hits / stats.total_attacks * 100) if stats.total_attacks > 0 else 0
    fumble_rate = (stats.total_fumbles / stats.total_attacks * 100) if stats.total_attacks > 0 else 0
    crit_rate = (stats.total_crits / stats.total_hits * 100) if stats.total_hits > 0 else 0
    
    print(f"Attacks executed: {attacks_executed}")
    print(f"  Total hits: {stats.total_hits} ({hit_rate:.1f}%)")
    print(f"  Total misses: {stats.total_misses} ({100 - hit_rate:.1f}%)")
    print(f"  Total fumbles: {stats.total_fumbles} ({fumble_rate:.1f}%)")
    print()
    
    print(f"Critical hits: {stats.total_crits} ({crit_rate:.1f}% of hits)")
    print(f"  Tier 1 (ignore armor): {stats.crit_ignore_armor}")
    print(f"  Tier 2 (1.5×): {stats.crit_15x}")
    print(f"  Tier 3 (2×): {stats.crit_2x}")
    print(f"  Tier 4 (3×): {stats.crit_3x}")
    print(f"  Tier 5 (instant kill): {stats.crit_instant_kill}")
    print()
    
    print(f"Fumbles: {stats.total_fumbles}")
    print(f"  Recover: {stats.fumble_recover}")
    print(f"  Drop weapon: {stats.fumble_drop}")
    print(f"  Break weapon: {stats.fumble_break}")
    print(f"  Hit self: {stats.fumble_hit_self}")
    print(f"  Kill self: {stats.fumble_kill_self}")
    print()
    
    print(f"Damage dealt: {stats.total_damage} total")
    if stats.total_hits > 0:
        avg_damage = stats.total_damage / stats.total_hits
        print(f"  Average per hit: {avg_damage:.1f}")
    print()
    
    print(f"Proficiency growth: {WEAPON_PROFICIENCY}% → {stats.proficiency}%")
    print()
    
    print(f"Final state:")
    print(f"  Monster HP: {max(0, stats.monster_hp)} / {MONSTER_HP_MAX}")
    print(f"  Your HP: {max(0, stats.player_hp)} / {PLAYER_HARDINESS * 2}")
    print()
    
    # ── VALIDATION ────────────────────────────────────────────────────────────
    
    print("VALIDATION:")
    print()
    
    issues = []
    
    # Check hit rate (should be around 50-70% depending on proficiency)
    if hit_rate < 30 or hit_rate > 90:
        issues.append(f"⚠ Hit rate {hit_rate:.1f}% seems off (expected 40-80%)")
    else:
        print(f"✓ Hit rate {hit_rate:.1f}% is reasonable")
    
    # Check fumble rate (should be ~4%)
    if fumble_rate < 2 or fumble_rate > 6:
        issues.append(f"⚠ Fumble rate {fumble_rate:.1f}% (expected ~4%)")
    else:
        print(f"✓ Fumble rate {fumble_rate:.1f}% is correct (~4%)")
    
    # Check crit rate (should be ~5% of hits)
    if crit_rate < 3 or crit_rate > 7:
        issues.append(f"⚠ Crit rate {crit_rate:.1f}% (expected ~5%)")
    else:
        print(f"✓ Crit rate {crit_rate:.1f}% is correct (~5%)")
    
    # Check proficiency growth
    growth = stats.proficiency - WEAPON_PROFICIENCY
    if growth < 2:
        issues.append(f"⚠ Proficiency growth only +{growth}% (expected +4-10%)")
    else:
        print(f"✓ Proficiency growth +{growth}% is reasonable")
    
    # Check no negative HP
    if stats.player_hp < 0 or stats.monster_hp < -1:
        issues.append(f"⚠ HP went negative (player {stats.player_hp}, monster {stats.monster_hp})")
    else:
        print(f"✓ HP tracking is correct")
    
    print()
    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(issue)
    else:
        print("No issues found! Combat mechanics working correctly.")
    
    print()
    print("="*72)

if __name__ == "__main__":
    random.seed()  # Use current time for randomness
    run_combat_simulation()
