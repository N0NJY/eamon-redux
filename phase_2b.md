I'm continuing Phase 2 of the data-driven flag system for Eamon Redux.

PHASE 2b: Artifact Flag Editing in Designer

Reference documents:
- CODE_VS_SPEC_GAP_ANALYSIS.md (Phase 2 section)
- INTEGRATED_FLAG_HANDLER_ARCHITECTURE.md (background)

What I need:
Enhance the artifact editing in designer.py to include flag editing.

When designer edits an artifact, they should be able to set:
- is_tradeable (checkbox)
- trade_npc (text, if is_tradeable)
- trade_dialogue (text, if is_tradeable)
- is_escape_vehicle (checkbox)
- escape_dialogue (text, if is_escape_vehicle)
- is_quest_item (checkbox)
- quest_id (text, if is_quest_item)
- triggers_event (text field)

These should save to the artifact's flags dict in adventure.json.

Current state:
- world.py has flags dict on Artifact ✅
- designer.py has basic artifact editing (no flags yet)
- Phase 2a (monsters menu) is completed

Steps:
1. View designer.py edit_artifact() method
2. Show me the new flag-editing UI you'll add
3. Apply changes
4. Test: python3 designer.py adventures/sample
   - Edit an artifact
   - Verify flags save to adventure.json

Repository: ~/git/Eamon/eamon-redux/

Let's start: View the edit_artifact() method.
