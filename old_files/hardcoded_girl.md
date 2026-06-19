QUICK FIX: Remove hardcoded "girl" from win condition check

I need to fix a hardcoding issue in the win condition system.

PROBLEM:
- base_handlers.py has: elif cond_type == "has_rescued_girl"
- This only checks for id='girl' (too specific)
- Should support ANY follower or quest flags

SOLUTION:
1. In core/base_handlers.py, in _check_win_condition() method:
   - REMOVE the hardcoded "has_rescued_girl" section
   - ADD these new types:
     * has_follower:ID (check for follower with specific ID)
     * has_any_follower (check if ANY follower recruited)

2. In adventures/001-beginners-cave/adventure.json:
   - Find the win room (id=10, "The Exit")
   - Change: "win_condition": "has_rescued_girl"
   - To: "win_condition": "quest_completed:rescued_captive"

Repository: ~/git/Eamon/eamon-redux/

Steps:
1. View core/base_handlers.py around the _check_win_condition() method
2. Find the "has_rescued_girl" section (should be around line 100-110)
3. I'll show you the replacement code
4. Apply the changes
5. View and update adventure.json win_condition
6. Test: python3 tavern.py

Let's start: View core/base_handlers.py _check_win_condition() method
