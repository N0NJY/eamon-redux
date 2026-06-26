#!/usr/bin/env python3
"""
Adventurer's Gate — animated parchment scroll banner.

The scroll starts wound up at the top and unrolls downward line by
line.  The bottom roller only appears when the scroll is fully open.

Run standalone:  python3 banner.py
Import later via:  from banner import scroll_open
"""

import sys
import time

# ── Colors ────────────────────────────────────────────────────────────
_GOLD  = "\033[1;33m"   # bright yellow  — title
_AMBER = "\033[0;33m"   # yellow/amber   — rods, borders
_CYAN  = "\033[0;36m"   # cyan           — tagline
_DIM   = "\033[0;37m"   # dim white      — subtitle / credits
_RESET = "\033[0m"

PAD = "  "   # left margin — gives the scroll breathing room
W   = 68     # inner content width

# ── Scroll part builders ──────────────────────────────────────────────
#
#  The finished scroll looks like:
#
#   ,____W____,    ← cap_top   rigid edge of the top roller
#   )====W====(    ← rod_top   the top wooden roller (cylinder)
#   |    W     |   ← blank     open parchment
#   |  content |   ← center    a line of text, centred
#   |  ~~~~~~  |   ← rule      decorative crease across the parchment
#   (====W====)    ← rod_bot   the bottom roller
#   `~~~~W~~~~'    ← cap_bot   trailing edge of bottom roller
#
#  During animation, the paper still being unrolled is shown as:
#
#   )~~~~W~~~~(    ← rolling   the curled paper edge still spooling out

def _cap_top() -> str:
    return f"{_AMBER}{PAD},{'_' * W},{_RESET}"

def _rod_top() -> str:
    return f"{_AMBER}{PAD}){'=' * W}({_RESET}"

def _rolling() -> str:
    """The curled paper edge visible while the scroll is still unrolling."""
    return f"{_AMBER}{PAD}){_DIM}{'~' * W}{_AMBER}({_RESET}"

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
#  TOP (stays fixed while content rolls out below):
#    cap_top  rod_top
#
#  CONTENT (unrolls line by line):
#    blank  title  blank  rule  blank  tagline  blank  subtitle  copyright  blank
#
#  BOTTOM (appears only when fully unrolled):
#    rod_bot  cap_bot

_TOP = [
    _cap_top(),
    _rod_top(),
]

_CONTENT = [
    _blank(),
    _center("A D V E N T U R E R ' S   G A T E", _GOLD),
    _blank(),
    _rule(),
    _blank(),
    _center("Where Heroes are made, and Legends begin", _CYAN),
    _blank(),
    _center("A D&D / Eamon Adventure Engine", _DIM),
    _center("(C) 2026, Rick Donaldson", _DIM),
    _blank(),
]

_BOTTOM = [
    _rod_bot(),
    _cap_bot(),
]

BANNER = _TOP + _CONTENT + _BOTTOM   # full static version

# ── Animation ─────────────────────────────────────────────────────────

def scroll_open() -> None:
    """
    Print the top roller, then unroll content line by line downward.
    The curled-paper indicator ( )~~~( ) sits below the content until
    the scroll is fully open, then the bottom roller snaps into place.
    """

    # ── Print the fixed top of the scroll ─────────────────────────────
    for line in _TOP:
        print(line)
    sys.stdout.flush()
    time.sleep(0.35)   # brief pause — the scroll is about to drop

    # ── Show the initial curled-paper edge ────────────────────────────
    rolling = _rolling()
    print(rolling)
    sys.stdout.flush()

    # ── Unroll each content line ───────────────────────────────────────
    #  Speed: starts slow (stiff parchment), eases faster as it gains momentum
    delays = [0.14, 0.13, 0.11, 0.09, 0.08, 0.07, 0.07, 0.07, 0.07, 0.08]

    for i, line in enumerate(_CONTENT):
        time.sleep(delays[i] if i < len(delays) else 0.08)

        # Overwrite the rolling indicator with the new content line,
        # then print a fresh rolling indicator below it
        sys.stdout.write("\033[1A\033[2K")
        print(line)
        print(rolling)
        sys.stdout.flush()

    # ── Snap the bottom roller into place ─────────────────────────────
    time.sleep(0.30)   # brief pause before the scroll locks open
    sys.stdout.write("\033[1A\033[2K")
    for line in _BOTTOM:
        print(line)
    sys.stdout.flush()

    print()


if __name__ == "__main__":
    scroll_open()
