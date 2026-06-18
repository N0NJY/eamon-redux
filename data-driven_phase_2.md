I'm building Phase 2 of the data-driven flag system for Eamon Redux.

Phase 2a: Add Monsters & NPCs Menu to Designer

Current state:
- world.py has Monster, Artifact, Room classes with flags dicts ✅
- player.py has quest_flags, followers, etc. ✅
- designer.py has menus for adventure settings, rooms, artifacts

What I need:
Add a "4. Monsters & NPCs" menu option to designer.py that allows:
1. List all monsters in the adventure
2. Add a new monster
3. Edit a monster (name, description, HP, damage, attitude, dialogue, heal mechanics)
4. Delete a monster
5. Go back to main menu

The flag editing can come in Phase 2b. For now, just the basic CRUD for monsters.

Repository: ~/git/Eamon/eamon-redux/
Main file: designer.py

Steps:
1. View designer.py around line 350 (main menu)
2. View the existing menu_rooms() method as a template
3. Show me the new methods you'll add for monsters menu
4. Apply the changes
5. Test by running: python3 designer.py adventures/sample

Let's start: View the main menu section and menu_rooms() template.
