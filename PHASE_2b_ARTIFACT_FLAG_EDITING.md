# PHASE 2b: Artifact Flag Editing in Designer

**Status**: Ready for Claude Code implementation  
**Dependency**: Phase 2a completed, world.py has flags dict on Artifact  
**Estimated Time**: 2-3 hours

---

## Objective

Enhance `designer.py` artifact editing menu to allow setting flags that control behavior:
- Tradeable items (trade with NPCs)
- Escape vehicles (boat, portal, etc.)
- Quest items (can't be sold)
- Event triggers

---

## Current State

**designer.py edit_artifact() (around line 450):**
```python
def edit_artifact(self) -> None:
    aid = self._pick_artifact("Edit which artifact?")
    if aid is None:
        return

    a = self.world.artifacts[aid]

    print(f"\n EDIT ARTIFACT #{aid}")

    a.name = prompt("Name", a.name)
    a.description = prompt("Description", a.description)
    a.weight = prompt_int("Weight", a.weight)

    syns = ", ".join(a.synonyms)
    syns_new = prompt("Synonyms (comma-separated)", syns)
    a.synonyms = [s.strip() for s in syns_new.split(",") if s.strip()]

    if a.artifact_type == ArtifactType.READABLE:
        a.read_text = prompt("Read text", a.read_text or "")

    if a.is_container:
        a.is_open = prompt_bool("Currently open?", a.is_open)

    print(" Artifact updated.")
```

---

## Deliverable

After edit_artifact() completes (before "print Artifact updated"), add a submenu for flags:

```python
# After existing edit_artifact() code, add:

def _edit_artifact_flags(self, artifact) -> None:
    """Edit flags for an artifact (tradeable, escape vehicle, quest, etc.)."""
    print(f"\n ARTIFACT FLAGS — {artifact.name}")
    print(f" {self.hr('─', 40)}")
    
    flags = artifact.flags or {}
    
    # --- TRADEABLE ---
    is_tradeable = prompt_bool("Is this tradeable to NPCs?", flags.get('is_tradeable', False))
    if is_tradeable:
        trade_npc = prompt("Trade with which NPC?", flags.get('trade_npc', ''))
        trade_dialogue = prompt("Dialogue when traded?", flags.get('trade_dialogue', ''))
        flags['is_tradeable'] = True
        flags['trade_npc'] = trade_npc
        flags['trade_dialogue'] = trade_dialogue
    else:
        flags.pop('is_tradeable', None)
        flags.pop('trade_npc', None)
        flags.pop('trade_dialogue', None)
    
    # --- ESCAPE VEHICLE ---
    is_escape = prompt_bool("Is this an escape vehicle (boat, portal)?", flags.get('is_escape_vehicle', False))
    if is_escape:
        escape_dialogue = prompt("Dialogue when used to escape?", flags.get('escape_dialogue', 'You escape!'))
        flags['is_escape_vehicle'] = True
        flags['escape_dialogue'] = escape_dialogue
    else:
        flags.pop('is_escape_vehicle', None)
        flags.pop('escape_dialogue', None)
    
    # --- QUEST ITEM ---
    is_quest = prompt_bool("Is this a quest item (can't be sold)?", flags.get('is_quest_item', False))
    if is_quest:
        quest_id = prompt("Quest ID (for tracking)", flags.get('quest_id', ''))
        flags['is_quest_item'] = True
        flags['quest_id'] = quest_id
    else:
        flags.pop('is_quest_item', None)
        flags.pop('quest_id', None)
    
    # --- EVENT TRIGGER ---
    triggers = prompt_bool("Does using this trigger an event?", flags.get('triggers_event', False))
    if triggers:
        event_id = prompt("Event ID to trigger", flags.get('triggers_event', ''))
        flags['triggers_event'] = event_id
    else:
        flags.pop('triggers_event', None)
    
    artifact.flags = flags if flags else {}
    print(" Flags updated.")
```

---

## Integration Points

**1. In edit_artifact() method:**

Replace the "print Artifact updated" line with:

```python
    # Ask if user wants to edit flags
    if prompt_bool("Edit flags (special behaviors)?", False):
        self._edit_artifact_flags(a)
    
    print(" Artifact updated.")
```

**2. Verify flags are saved:**

Make sure `world.save()` already handles the flags dict (it should, from Phase 1).

**3. Test:**
```bash
python3 designer.py adventures/sample
# Edit an artifact
# Set flags
# Save and check adventure.json for flags dict
```

---

## Expected JSON Output

After editing an artifact with flags, adventure.json should contain:

```json
{
  "id": 5,
  "name": "silver amulet",
  "description": "A glowing silver amulet",
  "room_id": 2,
  "artifact_type": "generic",
  "weight": 1,
  "value": 50,
  "synonyms": ["amulet"],
  "flags": {
    "is_tradeable": true,
    "trade_npc": "henrich",
    "trade_dialogue": "Ah! The amulet! I'll join you!",
    "is_quest_item": true,
    "quest_id": "amulet_for_henrich"
  }
}
```

---

## Checklist for Claude Code

- [ ] View current edit_artifact() method
- [ ] Add _edit_artifact_flags() method
- [ ] Integrate flag editing into edit_artifact()
- [ ] Test: Create artifact with flags
- [ ] Verify flags save to adventure.json
- [ ] Verify flags load from adventure.json when editing again

---

## Notes

- Flags should be optional (artifact.flags can be empty dict)
- If user says "no" to a flag, remove it from flags dict (don't save False)
- The prompt_bool, prompt, hr() functions already exist in designer.py
- Make sure editing an existing artifact LOADS its flags first

---

## Claude Code Session Start

```
I'm implementing Phase 2b: Artifact Flag Editing for Eamon Redux designer.

PHASE 2b: Artifact Flag Editing

Reference document: PHASE_2b_ARTIFACT_FLAG_EDITING.md

Current situation:
- Phase 2a (monsters menu) completed ✅
- world.py has flags dict on Artifact ✅
- designer.py has basic artifact editing (no flags)

Deliverable:
Add flag-editing submenu to designer.py artifact editing.
When editing an artifact, user can set:
- is_tradeable (NPC trade mechanics)
- is_escape_vehicle (boat/portal escape)
- is_quest_item (can't be sold)
- triggers_event (special event firing)

Repository: ~/git/Eamon/eamon-redux/

Steps:
1. View designer.py edit_artifact() method (around line 450)
2. I'll provide the _edit_artifact_flags() code to add
3. Integrate it into edit_artifact()
4. Test: python3 designer.py adventures/sample

Let's start: View the edit_artifact() method.
```

---

**Next**: After Phase 2b passes testing, move to **PHASE_2c_ROOM_FLAG_EDITING.md**
