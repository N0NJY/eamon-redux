#!/usr/bin/env python3
"""
Adventurer's Gate — animated scroll banner.
Run standalone:  python3 banner.py
Incorporate into tavern.py later via:  from banner import scroll_open
"""

import sys
import time

# ── Colors ────────────────────────────────────────────────────────────
_GOLD   = "\033[1;33m"   # bright yellow  — title
_BORDER = "\033[0;33m"   # yellow         — scroll border / frame
_CYAN   = "\033[0;36m"   # cyan           — tagline
_DIM    = "\033[0;37m"   # dim white      — subtitle / credits
_PARCH  = "\033[0;33m"   # amber          — scroll roll texture
_RESET  = "\033[0m"

W = 70   # visible inner width of the scroll (total line = W + 2 borders)

# ── Line builders ─────────────────────────────────────────────────────

def _frame(left: str, fill: str, right: str) -> str:
    return f"{_BORDER}{left}{fill * W}{right}{_RESET}"

def _roll() -> str:
    return f"{_BORDER}║{_PARCH}{'▓' * W}{_BORDER}║{_RESET}"

def _blank() -> str:
    return f"{_BORDER}║{' ' * W}║{_RESET}"

def _rule() -> str:
    inner = "  " + "─" * (W - 4) + "  "
    return f"{_BORDER}║{_DIM}{inner}{_BORDER}║{_RESET}"

def _center(text: str, color: str = _RESET) -> str:
    pad   = (W - len(text)) // 2
    extra = W - len(text) - pad * 2   # absorb odd width
    inner = " " * pad + color + text + _RESET + " " * (pad + extra)
    return f"{_BORDER}║{_RESET}{inner}{_BORDER}║{_RESET}"

# ── Banner definition — ANCHOR marks the first line that appears ──────
#
#   0   ╔══...══╗   top frame
#   1   ║▓▓...▓▓║   parchment roll
#   2   ╠══...══╣   roll edge
#   3   ║        ║   space
#   4   ║ TITLE  ║   ← ANCHOR (title appears first)
#   5   ║        ║   space
#   6   ║ ─────  ║   decorative rule
#   7   ║        ║   space
#   8   ║ tagline║   tagline
#   9   ║        ║   space
#  10   ║ subtitle   subtitle
#  11   ║ copyright  copyright
#  12   ║        ║   space
#  13   ╠══...══╣   roll edge
#  14   ║▓▓...▓▓║   parchment roll
#  15   ╚══...══╝   bottom frame

ANCHOR = 4   # title line — scroll unrolls outward from here

BANNER = [
    _frame("╔", "═", "╗"),                                            #  0
    _roll(),                                                            #  1
    _frame("╠", "═", "╣"),                                            #  2
    _blank(),                                                           #  3
    _center("A D V E N T U R E R ' S   G A T E", _GOLD),             #  4  ← ANCHOR
    _blank(),                                                           #  5
    _rule(),                                                            #  6
    _blank(),                                                           #  7
    _center("Where Legend Begins and Gold Changes Hands", _CYAN),      #  8
    _blank(),                                                           #  9
    _center("A D&D / Eamon Adventure Engine", _DIM),                   # 10
    _center("(C) 2026, Rick Donaldson", _DIM),                         # 11
    _blank(),                                                           # 12
    _frame("╠", "═", "╣"),                                            # 13
    _roll(),                                                            # 14
    _frame("╚", "═", "╝"),                                            # 15
]

# ── Animation ─────────────────────────────────────────────────────────

def scroll_open(pause_on_title: float = 0.40, step_delay: float = 0.08) -> None:
    """
    Unfurl the scroll banner from the title line outward.

    pause_on_title  — seconds to hold on the title before unrolling
    step_delay      — seconds between each expansion step
    """
    total = len(BANNER)
    top   = ANCHOR
    bot   = ANCHOR

    # ── Seed: title line only ──────────────────────────────────────────
    print(BANNER[ANCHOR])
    sys.stdout.flush()
    time.sleep(pause_on_title)

    lines_shown = 1

    # ── Unfurl: expand one line up and one line down each step ─────────
    while top > 0 or bot < total - 1:
        new_top = max(0, top - 1)
        new_bot = min(total - 1, bot + 1)

        # Return cursor to the first printed line
        sys.stdout.write(f"\033[{lines_shown}A")
        sys.stdout.flush()

        for i in range(new_top, new_bot + 1):
            sys.stdout.write("\033[2K")   # erase old content on this line
            print(BANNER[i])

        lines_shown = new_bot - new_top + 1
        top = new_top
        bot = new_bot
        sys.stdout.flush()
        time.sleep(step_delay)

    print()


if __name__ == "__main__":
    scroll_open()
