#!/usr/bin/env python3
"""
Adventurer's Gate — animated parchment scroll banner.
Run standalone:  python3 banner.py
Import into tavern.py later via:  from banner import scroll_open
"""

import sys
import time

# ── Colors ────────────────────────────────────────────────────────────
_GOLD  = "\033[1;33m"   # bright yellow  — title
_AMBER = "\033[0;33m"   # yellow/amber   — scroll body, rods, caps
_CYAN  = "\033[0;36m"   # cyan           — tagline
_DIM   = "\033[0;37m"   # dim white      — subtitle / credits
_RESET = "\033[0m"

PAD = "  "    # left indent — gives the scroll some breathing room
W   = 68      # inner content width (between the | sides)

# ── Scroll part builders ──────────────────────────────────────────────
#
#   ,____W____,       ← cap_top   (rigid top edge of top rod)
#   )====W=====(      ← rod_top   (the rolled cylinder at the top)
#   |    W     |      ← blank     (open parchment)
#   |  content |      ← center    (text line, centered in W)
#   |  ~~~~~~  |      ← rule      (decorative parchment crease)
#   (====W=====)      ← rod_bot   (the rolled cylinder at the bottom)
#   `~~~~W~~~~~'      ← cap_bot   (trailing edge of bottom rod)

def _cap_top() -> str:
    return f"{_AMBER}{PAD},{'_' * W},{_RESET}"

def _rod_top() -> str:
    return f"{_AMBER}{PAD}){'=' * W}({_RESET}"

def _blank() -> str:
    return f"{_AMBER}{PAD}|{_RESET}{' ' * W}{_AMBER}|{_RESET}"

def _rule() -> str:
    inner = " " + "~" * (W - 2) + " "
    return f"{_AMBER}{PAD}|{_DIM}{inner}{_AMBER}|{_RESET}"

def _center(text: str, color: str = _RESET) -> str:
    pad   = (W - len(text)) // 2
    extra = W - len(text) - pad * 2
    inner = " " * pad + color + text + _RESET + " " * (pad + extra)
    return f"{_AMBER}{PAD}|{_RESET}{inner}{_AMBER}|{_RESET}"

def _rod_bot() -> str:
    return f"{_AMBER}{PAD}({'=' * W}){_RESET}"

def _cap_bot() -> str:
    return f"{_AMBER}{PAD}`{'~' * W}'{_RESET}"

# ── Scroll contents ───────────────────────────────────────────────────
#
#  The ANCHOR is the first line revealed — the scroll unrolls outward
#  from that point.  Putting the title at ANCHOR means it appears
#  first; the rods and caps roll in from above and below.
#
#   0   cap_top
#   1   rod_top
#   2   blank
#   3   TITLE          ← ANCHOR
#   4   blank
#   5   rule  (~~~~~)
#   6   blank
#   7   tagline
#   8   blank
#   9   subtitle
#  10   copyright
#  11   blank
#  12   rod_bot
#  13   cap_bot

ANCHOR = 3

BANNER = [
    _cap_top(),                                                        #  0
    _rod_top(),                                                        #  1
    _blank(),                                                          #  2
    _center("A D V E N T U R E R ' S   G A T E", _GOLD),            #  3  ANCHOR
    _blank(),                                                          #  4
    _rule(),                                                           #  5
    _blank(),                                                          #  6
    _center("Where Legend Begins and Gold Changes Hands", _CYAN),     #  7
    _blank(),                                                          #  8
    _center("A D&D / Eamon Adventure Engine", _DIM),                  #  9
    _center("(C) 2026, Rick Donaldson", _DIM),                        # 10
    _blank(),                                                          # 11
    _rod_bot(),                                                        # 12
    _cap_bot(),                                                        # 13
]

# ── Animation ─────────────────────────────────────────────────────────

def scroll_open(pause_on_title: float = 0.45, step_delay: float = 0.09) -> None:
    """
    Unroll the scroll from the title outward.

    pause_on_title  — seconds to hold on the gold title line alone
    step_delay      — seconds between each expansion step
    """
    total = len(BANNER)
    top   = ANCHOR
    bot   = ANCHOR

    # ── Title appears first ────────────────────────────────────────────
    print(BANNER[ANCHOR])
    sys.stdout.flush()
    time.sleep(pause_on_title)

    lines_shown = 1

    # ── Scroll unrolls one line at a time in each direction ────────────
    while top > 0 or bot < total - 1:
        new_top = max(0, top - 1)
        new_bot = min(total - 1, bot + 1)

        # Return cursor to the top of what's already on screen
        sys.stdout.write(f"\033[{lines_shown}A")
        sys.stdout.flush()

        for i in range(new_top, new_bot + 1):
            sys.stdout.write("\033[2K")
            print(BANNER[i])

        lines_shown = new_bot - new_top + 1
        top = new_top
        bot = new_bot
        sys.stdout.flush()
        time.sleep(step_delay)

    print()


if __name__ == "__main__":
    scroll_open()
