I'm implementing a data-driven flag system for Eamon Redux using this plan. Read the following file for information:

/home/rick/git/Eamon/new_files/CODE_VS_SPEC_GAP_ANALYSIS.md

Repository: ~/git/Eamon/eamon-redux/

PHASE 1: Data Model Updates
=====
Work on these changes ONLY:

1. **world.py**: Add flags dict to Artifact, Monster, Room classes
2. **player.py**: Add quest_flags={}, followers=[], alignment="neutral", combat_kills=0
3. Update JSON loaders to read flags with defaults

Steps:
1. View current Artifact, Monster, Room class definitions
2. Show me the exact changes needed (don't apply yet)
3. I'll review, then you apply them
4. Test by running the existing adventure

Let's start: View world.py and show me the class definitions.
