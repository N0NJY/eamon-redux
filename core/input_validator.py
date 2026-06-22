"""
core/input_validator.py - Safe input functions with retry logic and bounds checking.
Prevents crashes from type mismatches, EOF, interrupts, and malformed input.
"""

from typing import Optional, List, Callable

def safe_input(prompt: str, timeout_secs: int = None) -> str:
    """
    Safely capture user input, handling EOF and interrupt gracefully.

    Returns empty string on EOF/interrupt instead of crashing.
    Strips whitespace automatically.

    Args:
        prompt: Displayed to user
        timeout_secs: NOT USED (for future readline timeout)

    Returns: Stripped input, or empty string on interrupt/EOF
    """
    try:
        return input(prompt).strip()
    except KeyboardInterrupt:
        print("\n(Interrupted)")
        return ""
    except EOFError:
        print("\n(End of input)")
        return ""


def prompt_string(label: str, default: str = "", allow_empty: bool = False) -> str:
    """
    Prompt for free-form text with optional default.

    Args:
        label: Prompt label
        default: Default if user enters nothing
        allow_empty: If False, retry until non-empty (unless default provided)

    Returns: Non-empty string or default
    """
    while True:
        raw = safe_input(f"  {label} [{default}]: " if default else f"  {label}: ")

        if not raw:
            if default:
                return default
            if allow_empty:
                return ""
            print("  Please enter something.")
            continue

        return raw


def prompt_int(
    label: str,
    default: int = 0,
    min_val: Optional[int] = None,
    max_val: Optional[int] = None,
    allow_negative: bool = False
) -> int:
    """
    Prompt for integer with optional bounds checking.
    Retries on non-numeric input, out-of-bounds, negative (if disallowed).

    Args:
        label: Prompt label
        default: Default value if user enters nothing
        min_val: Minimum allowed (inclusive)
        max_val: Maximum allowed (inclusive)
        allow_negative: If False, reject negative numbers

    Returns: Valid integer within bounds
    """
    bounds_msg = f"({min_val}–{max_val})" if (min_val is not None and max_val is not None) else \
                 f"(≥ {min_val})" if min_val is not None else \
                 f"(≤ {max_val})" if max_val is not None else ""

    while True:
        raw = safe_input(f"  {label} [{default}]: ").strip()

        if not raw:
            return default

        # Type validation
        try:
            val = int(raw)
        except ValueError:
            print("  Please enter a valid number.")
            continue

        # Negativity check
        if not allow_negative and val < 0:
            print("  Please enter a positive number.")
            continue

        # Bounds check
        if min_val is not None and val < min_val:
            print(f"  Minimum value is {min_val}.")
            continue
        if max_val is not None and val > max_val:
            print(f"  Maximum value is {max_val}.")
            continue

        return val


def prompt_bool(label: str, default: bool = False) -> bool:
    """
    Prompt for yes/no with clear feedback.
    Accepts: y, yes, n, no (case-insensitive).
    Empty input returns default.

    Args:
        label: Prompt label
        default: Default if user enters nothing

    Returns: Boolean
    """
    d_str = "Y/n" if default else "y/N"

    while True:
        raw = safe_input(f"  {label} [{d_str}]: ").strip().lower()

        if not raw:
            return default

        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False

        print("  Please enter 'y' or 'n'.")


def prompt_choice(
    items: List[str],
    title: str = "Choose",
    allow_cancel: bool = True
) -> Optional[int]:
    """
    Display numbered list, return 1-based index or None if cancelled.

    Args:
        items: List of choice strings
        title: Title displayed above choices
        allow_cancel: If True, option 0 cancels (returns None)

    Returns: 1-based index (1..len(items)), or None if cancelled
    """
    if not items:
        print("  (No items to choose from)")
        return None

    print(f"\n  {title}")
    print(f"  {'-' * 40}")

    for i, item in enumerate(items, 1):
        print(f"  {i:>3}. {item}")

    if allow_cancel:
        print(f"    0. Cancel")

    while True:
        raw = safe_input("  > ").strip()

        try:
            choice = int(raw)
        except ValueError:
            print("  Invalid choice. Please enter a number.")
            continue

        if choice == 0:
            if allow_cancel:
                return None
            print("  Invalid choice.")
            continue

        if 1 <= choice <= len(items):
            return choice

        print(f"  Please choose 1–{len(items)}.")


def prompt_from_options(
    label: str,
    options: List[str],
    default: Optional[str] = None,
    case_sensitive: bool = False
) -> str:
    """
    Prompt for one of a fixed set of options.
    Matches input against options list (fuzzy or exact).

    Args:
        label: Prompt label
        options: List of valid strings
        default: Default if user enters nothing
        case_sensitive: If False, match case-insensitively

    Returns: Matched option from list
    """
    options_lower = [o.lower() for o in options] if not case_sensitive else options

    while True:
        default_str = f" [{default}]" if default else ""
        raw = safe_input(f"  {label}{default_str}: ").strip()

        if not raw:
            if default and default in options:
                return default
            print(f"  Please enter one of: {', '.join(options)}")
            continue

        # Match (case-insensitive by default)
        check_raw = raw.lower() if not case_sensitive else raw

        for i, opt in enumerate(options_lower if not case_sensitive else options):
            if opt == check_raw or opt.startswith(check_raw):
                return options[i]

        print(f"  Unknown option. Valid choices: {', '.join(options)}")


def prompt_direction(label: str = "Direction") -> Optional[str]:
    """
    Prompt for cardinal direction with full validation.
    Accepts: N S E W U D NE NW SE SW and spelled-out forms.

    Args:
        label: Prompt label

    Returns: Canonical direction (lowercase), or None if cancelled
    """
    from world import DIRECTIONS, DIR_ABBREV

    valid_abbrevs = ["n", "s", "e", "w", "u", "d", "ne", "nw", "se", "sw"]

    while True:
        raw = safe_input(f"  {label} [N/S/E/W/U/D or cancel with empty]: ").strip().lower()

        if not raw:
            return None

        # Try exact match
        if raw in DIRECTIONS:
            return raw

        # Try abbreviation
        if raw in valid_abbrevs:
            if raw in DIR_ABBREV:
                return DIR_ABBREV[raw]
            # Map manually
            mapping = {
                "n": "north", "s": "south", "e": "east", "w": "west",
                "u": "up", "d": "down",
                "ne": "northeast", "nw": "northwest",
                "se": "southeast", "sw": "southwest"
            }
            return mapping.get(raw)

        print(f"  Invalid direction. Try: N, S, E, W, U, D, NE, NW, SE, SW")


def prompt_quantity(
    label: str,
    max_qty: int,
    default: int = 1,
    allow_zero: bool = False
) -> int:
    """
    Prompt for quantity with max bounds.

    Args:
        label: Prompt label
        max_qty: Maximum allowed quantity
        default: Default if user enters nothing
        allow_zero: If True, allow 0; otherwise minimum is 1

    Returns: Valid quantity in range
    """
    min_qty = 0 if allow_zero else 1

    while True:
        raw = safe_input(f"  {label} ({min_qty}–{max_qty}) [{default}]: ").strip()

        if not raw:
            return default

        try:
            qty = int(raw)
        except ValueError:
            print("  Please enter a number.")
            continue

        if qty < min_qty or qty > max_qty:
            print(f"  Must be between {min_qty} and {max_qty}.")
            continue

        return qty


def prompt_artifact_from_list(
    label: str,
    artifacts: List,
    allow_cancel: bool = True
) -> Optional:
    """
    Prompt to select an artifact from a list by name.
    Fuzzy-matches input against artifact names.

    Args:
        label: Prompt label
        artifacts: List of Artifact objects
        allow_cancel: If True, empty input cancels

    Returns: Selected Artifact, or None if cancelled
    """
    if not artifacts:
        print("  (No artifacts available)")
        return None

    while True:
        raw = safe_input(f"  {label}: ").strip()

        if not raw:
            if allow_cancel:
                return None
            print("  Please choose an artifact.")
            continue

        # Case-insensitive fuzzy match
        candidates = [a for a in artifacts
                      if raw.lower() in a.name.lower()
                      or a.name.lower().startswith(raw.lower())]

        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) > 1:
            print(f"  Ambiguous. Matches: {', '.join(c.name for c in candidates)}")
            continue
        else:
            print(f"  No artifact matches '{raw}'.")
            continue


def prompt_monster_from_list(
    label: str,
    monsters: List,
    allow_cancel: bool = True
) -> Optional:
    """
    Prompt to select a monster/NPC from a list by name.
    Fuzzy-matches input against monster names.

    Args:
        label: Prompt label
        monsters: List of Monster objects
        allow_cancel: If True, empty input cancels

    Returns: Selected Monster, or None if cancelled
    """
    if not monsters:
        print("  (No creatures here)")
        return None

    while True:
        raw = safe_input(f"  {label}: ").strip()

        if not raw:
            if allow_cancel:
                return None
            print("  Please choose a creature.")
            continue

        # Case-insensitive fuzzy match
        candidates = [m for m in monsters
                      if raw.lower() in m.name.lower()
                      or m.name.lower().startswith(raw.lower())]

        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) > 1:
            print(f"  Ambiguous. Matches: {', '.join(c.name for c in candidates)}")
            continue
        else:
            print(f"  No creature matches '{raw}'.")
            continue
