    # ── COMBAT SYSTEM (WITH WEAPON PROFICIENCIES) ───────────────────────────────

    def cmd_attack(self, noun: str) -> None:
        """
        ATTACK <monster>
        With weapon proficiencies, critical hits (5%), and fumbles (4%).
        """
        if not noun:
            print(self.tc("Attack what?", "error"))
            return
        
        monsters = self.world.monsters_in_room(self.player.room_id)
        monster = self.world.find_monster_by_name(noun, monsters)
        
        if not monster:
            print(self.tc(f"You don't see a {noun} here.", "error"))
            return
        
        if not monster.is_alive:
            print(self.tc(f"The {monster.name} is already dead.", "error"))
            return
        
        # ── Get weapon and proficiency ────────────────────────────────────────
        
        weapon = self.player.equipped_weapon(self.world)
        weapon_type = weapon.weapon_type if weapon and hasattr(weapon, 'weapon_type') else None
        weapon_prof = self.player.weapon_proficiencies.get(weapon_type, 0) if weapon_type else 0
        
        # ── Roll for hit ──────────────────────────────────────────────────────
        
        agility_bonus = self.player.agility_bonus
        monster_ac = monster.armor_class
        
        # Hit chance = 50 + agility_bonus + weapon_proficiency - monster_ac
        hit_chance = 50 + agility_bonus + weapon_prof - monster_ac
        hit_roll = random.randint(1, 100)
        
        is_hit = hit_roll <= hit_chance
        
        # ── Check for FUMBLE (4% chance on ANY attack) ────────────────────────
        
        if random.randint(1, 100) <= 4:
            # FUMBLE!
            fumble_roll = random.randint(1, 100)
            
            if fumble_roll <= 35:
                # Recover (no effect)
                print(self.tc(f"You fumble the attack but recover!", "warn"))
                self.monster_round(monster)
                return
            elif fumble_roll <= 75:
                # Drop weapon
                print(self.tc(f"You drop your {weapon.name if weapon else 'weapon'}!", "error"))
                if weapon:
                    self.player.unequip_artifact(weapon, self.world)
                self.monster_round(monster)
                return
            elif fumble_roll <= 95:
                # Break weapon
                print(self.tc(f"Your weapon breaks!", "error"))
                if weapon:
                    self.player.unequip_artifact(weapon, self.world)
                    weapon.room_id = self.player.room_id
                
                # 50% chance also injures player
                if random.randint(1, 100) <= 50:
                    damage = random.randint(1, 4)
                    self.player.hp -= damage
                    print(self.tc(f"The broken weapon cuts you for {damage} damage!", "dmg"))
                
                self.monster_round(monster)
                return
            elif fumble_roll <= 99:
                # Hit self
                damage = random.randint(2, 6)
                self.player.hp -= damage
                print(self.tc(f"You accidentally hit yourself for {damage} damage!", "error"))
                self.monster_round(monster)
                return
            else:
                # Kill self
                self.player.hp = 0
                print(self.tc(f"You fatally wound yourself!", "die"))
                return
        
        # ── Normal attack resolution ──────────────────────────────────────────
        
        if not is_hit:
            print(self.tc(f"You miss the {monster.name}.", "warn"))
            self.monster_round(monster)
            return
        
        # ── HIT! Roll damage ──────────────────────────────────────────────────
        
        if weapon:
            damage_dice = weapon.damage_dice
            damage_sides = weapon.damage_sides
            base_damage = roll(damage_dice, damage_sides)
        else:
            # Unarmed
            base_damage = self.roll(self.player.damage_dice, self.player.damage_sides)
        
        # ── Check for CRITICAL HIT (5% chance on successful hit) ──────────────
        
        damage = base_damage
        ignore_armor = False
        
        if random.randint(1, 100) <= 5:
            # CRITICAL HIT!
            crit_roll = random.randint(1, 100)
            
            if crit_roll <= 50:
                # Ignore armor (full damage)
                print(self.tc(f"CRITICAL HIT! You bypass the armor!", "hit"))
                ignore_armor = True
            elif crit_roll <= 85:
                # 1.5× damage
                damage = int(damage * 1.5)
                print(self.tc(f"CRITICAL HIT! {damage} damage!", "hit"))
            elif crit_roll <= 95:
                # 2× damage
                damage = damage * 2
                print(self.tc(f"CRITICAL HIT! {damage} damage!", "hit"))
            elif crit_roll <= 99:
                # 3× damage
                damage = damage * 3
                print(self.tc(f"CRITICAL HIT! {damage} damage!", "hit"))
            else:
                # Instant kill
                print(self.tc(f"INSTANT KILL!", "combat_win"))
                monster.hp = 0
                monster.is_alive = False
                return
        
        # ── Apply armor reduction ─────────────────────────────────────────────
        
        if not ignore_armor:
            damage = max(1, damage - monster_ac)
        
        # ── Apply damage ──────────────────────────────────────────────────────
        
        monster.hp -= damage
        print(self.tc(f"You hit {monster.name} for {damage} damage!", "dmg"))
        
        # ── Monster dies? ─────────────────────────────────────────────────────
        
        if monster.hp <= 0:
            print(self.tc(f"{monster.name} {monster.death_message}", "win"))
            monster.is_alive = False
            
            # Gain XP
            xp_value = monster.xp_value or (monster.hp_max * 10)
            self.player.xp += xp_value
            print(self.tc(f"You gain {xp_value} XP!", "heal"))
            
            # Drop loot
            if monster.loot_id:
                loot = self.world.artifacts.get(monster.loot_id)
                if loot:
                    loot.room_id = self.player.room_id
                    print(self.tc(f"{monster.name} drops {loot.name}!", "item"))
            
            return
        
        # ── Weapon proficiency growth (only on successful hit) ────────────────
        
        if weapon_type:
            failure_chance = 100 - weapon_prof
            growth_roll = random.randint(1, 100)
            if growth_roll < failure_chance:
                old_prof = self.player.weapon_proficiencies[weapon_type]
                self.player.weapon_proficiencies[weapon_type] += 2
                new_prof = self.player.weapon_proficiencies[weapon_type]
                print(self.tc(f"Your {weapon_type} proficiency increased: {old_prof}% → {new_prof}%", "success"))
        
        # ── Monster attacks back ──────────────────────────────────────────────
        
        print(self.tc(f"{monster.name} {monster.health_desc()}", "sys"))
        self.monster_round(monster)

    def monster_round(self, monster) -> None:
        """Monster attacks the player."""
        if not monster.is_alive:
            return
        
        # Roll for hit
        hit_chance = 50 - self.player.agility_bonus - self.player.armor_class(self.world)
        hit_roll = random.randint(1, 100)
        
        if hit_roll > hit_chance:
            print(self.tc(f"{monster.name} misses you.", "sys"))
        else:
            damage = roll(monster.damage_dice, monster.damage_sides)
            ac_reduction = self.player.armor_class(self.world)
            damage = max(1, damage - ac_reduction)
            self.player.hp -= damage
            print(self.tc(f"{monster.name} hits you for {damage} damage!", "dmg"))
        
        # Decrement speed spell duration
        if self.player.speed_active:
            self.player.tick_speed_duration()
            if not self.player.speed_active:
                print(self.tc("Your speed enhancement fades.", "sys"))

    def cmd_flee(self) -> None:
        """Flee from combat."""
        monsters = self.world.monsters_in_room(self.player.room_id)
        if not monsters:
            print(self.tc("You're not in combat.", "sys"))
            return
        
        # Random direction
        direction = random.choice(DIRECTIONS)
        room = self.world.get_room(self.player.room_id)
        
        if direction not in room.exits:
            print(self.tc(f"You can't flee {direction}!", "warn"))
            return
        
        print(self.tc(f"You flee {direction}!", "warn"))
        self.player.room_id = room.exits[direction]
        
        # Monsters get a free attack
        for monster in monsters:
            if monster.is_alive:
                print(self.tc(f"{monster.name} strikes as you flee!", "dmg"))
                self.monster_round(monster)
                break

    # ── NPC Interaction ────────────────────────────────────────────────────────

    def cmd_talk(self, noun: str) -> None:
        """Talk to an NPC."""
        if not noun:
            print(self.tc("Talk to whom?", "error"))
            return
        
        monsters = self.world.monsters_in_room(self.player.room_id)
        npc = self.world.find_monster_by_name(noun, monsters)
        
        if not npc:
            print(self.tc(f"You don't see a {noun} here.", "error"))
            return
        
        if npc.attitude == Attitude.HOSTILE:
            print(self.tc(f"The {npc.name} snarls at you.", "warn"))
            return
        
        # Display dialogue
        if npc.dialogue:
            print()
            print(self.tc(npc.dialogue, "desc"))
            print()
        else:
            print(self.tc(f"The {npc.name} has nothing to say.", "sys"))

    # ── Save/Load System ───────────────────────────────────────────────────────

    def cmd_save(self, noun: str) -> None:
        """Save game to a slot."""
        print(self.tc("Save feature coming soon.", "sys"))

    def cmd_load(self, noun: str) -> None:
        """Load a saved game."""
        print(self.tc("Load feature coming soon.", "sys"))

    # ── Help & Quit ────────────────────────────────────────────────────────────

    def cmd_help(self) -> None:
        """Show available commands."""
        print()
        print(self.tc("ADVENTURE COMMANDS", "title"))
        print()
        print(self.tc("Movement", "sys"))
        print(self.tc("  N/S/E/W/U/D, GO <direction>, FLEE", "help"))
        print()
        print(self.tc("Interaction", "sys"))
        print(self.tc("  LOOK, EXAMINE <thing>, READ <item>, TALK TO <npc>", "help"))
        print()
        print(self.tc("Inventory", "sys"))
        print(self.tc("  INVENTORY, GET <item>, DROP <item>, EQUIP <item>", "help"))
        print()
        print(self.tc("Combat", "sys"))
        print(self.tc("  ATTACK <monster>", "help"))
        print()
        print(self.tc("Magic", "sys"))
        print(self.tc("  CAST <spell>, SPELLS (show proficiencies)", "help"))
        print()
        print(self.tc("Status", "sys"))
        print(self.tc("  HEALTH, REST, EQUIPMENT", "help"))
        print()
        print(self.tc("Game", "sys"))
        print(self.tc("  SAVE, LOAD, QUIT, HELP", "help"))
        print()

    def cmd_quit(self) -> int:
        """Quit without confirmation."""
        return 0

    def cmd_quit_with_confirm(self) -> int:
        """Quit with confirmation."""
        response = input(self.tc("Really quit? (y/n): ", "warn"))
        if response.lower() == 'y':
            return 0
        return -1  # Continue


# ── Game Runner ───────────────────────────────────────────────────────────────

def run_adventure(character, adventure_path: str) -> int:
    """
    Run an adventure with the given character.
    Returns: 0=quit, 1=won, 2=died
    """
    world = World.load(adventure_path)
    engine = Engine(world, character)
    
    # Intro
    print()
    print(engine.tc(world.title, "title"))
    print(engine.tc(f"by {world.author}", "sys"))
    print(engine.tc("─" * 72, "exits"))
    print(engine.tc(wrap(world.intro), "intro"))
    print()
    
    # Initial look
    engine.look()
    
    # Main game loop
    while True:
        try:
            raw_input = input(engine.tc("[Adventure] > ", "sys")).strip()
        except KeyboardInterrupt:
            print()
            print(engine.tc("(Interrupted)", "sys"))
            result = engine.cmd_quit_with_confirm()
            if result == 0:
                return 0
            continue
        except EOFError:
            return 0
        
        if not raw_input:
            continue
        
        result = engine.handle(raw_input)
        
        if result == 1:
            # Won!
            print()
            print(engine.tc("★ " * 36, "win"))
            print(engine.tc(world.win_condition.get("message", "You have won!"), "win"))
            print(engine.tc("★ " * 36, "win"))
            print()
            
            # Sync proficiencies back to character
            character.spell_proficiencies = engine.player.spell_proficiencies.copy()
            character.weapon_proficiencies = engine.player.weapon_proficiencies.copy()
            character.gold = engine.player.gold
            character.xp = engine.player.xp
            character.save()
            
            return 1
        elif result == 2:
            # Died!
            print()
            print(engine.tc("╔" + "═" * 70 + "╗", "die"))
            print(engine.tc("║" + " " * 70 + "║", "die"))
            print(engine.tc("║" + "YOU HAVE DIED".center(70) + "║", "die"))
            print(engine.tc("║" + " " * 70 + "║", "die"))
            print(engine.tc("╚" + "═" * 70 + "╝", "die"))
            print()
            
            # Sync proficiencies back to character
            character.spell_proficiencies = engine.player.spell_proficiencies.copy()
            character.weapon_proficiencies = engine.player.weapon_proficiencies.copy()
            character.gold = engine.player.gold
            character.xp = engine.player.xp
            character.save()
            
            return 2
        elif result == 0:
            # Quit
            response = input(engine.tc("Save progress? (y/n): ", "warn"))
            if response.lower() == 'y':
                character.spell_proficiencies = engine.player.spell_proficiencies.copy()
                character.weapon_proficiencies = engine.player.weapon_proficiencies.copy()
                character.gold = engine.player.gold
                character.xp = engine.player.xp
                character.save()
                print(engine.tc("Progress saved.", "sys"))
            
            return 0


if __name__ == "__main__":
    print(engine.tc("Run via tavern.py", "error"))
