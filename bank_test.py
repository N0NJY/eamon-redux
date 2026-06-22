#!/usr/bin/env python3
"""
bank_test.py — Tests for DEPOSIT / WITHDRAW / BALANCE and shop persistence.

Run:  python3 bank_test.py
"""

import io, json, os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import character as char_mod
from character import Character
import tavern

# ── test helpers ──────────────────────────────────────────────────────────────

def _make_char(gold=500, bank_balance=0, name="TestChar"):
    ch = Character(name=name, hardiness=12, agility=10, charisma=10,
                   intelligence=10, strength=10)
    ch.gold = gold
    ch.bank_balance = bank_balance
    ch.hp = ch.hp_max
    return ch

_no_color  = lambda text, role: text        # strip ANSI for output capture
_no_tprint = lambda text, role="desc": None # silence tprint noise in tests

def _deposit(ch, amt_str, confirm="y"):
    with patch("tavern.tinput", return_value=confirm), \
         patch.object(ch, "save"), \
         redirect_stdout(io.StringIO()):
        tavern._bank_deposit(amt_str, ch)

def _withdraw(ch, amt_str, confirm="y"):
    with patch("tavern.tinput", return_value=confirm), \
         patch.object(ch, "save"), \
         redirect_stdout(io.StringIO()):
        tavern._bank_withdraw(amt_str, ch)

# ── DEPOSIT ───────────────────────────────────────────────────────────────────

class TestDeposit(unittest.TestCase):

    def test_valid_partial_deposit(self):
        ch = _make_char(gold=500, bank_balance=0)
        _deposit(ch, "100")
        self.assertEqual(ch.gold, 400)
        self.assertEqual(ch.bank_balance, 100)

    def test_deposit_all_keyword(self):
        ch = _make_char(gold=300, bank_balance=50)
        _deposit(ch, "all")
        self.assertEqual(ch.gold, 0)
        self.assertEqual(ch.bank_balance, 350)

    def test_deposit_exact_purse(self):
        ch = _make_char(gold=200)
        _deposit(ch, "200")
        self.assertEqual(ch.gold, 0)
        self.assertEqual(ch.bank_balance, 200)

    def test_deposit_more_than_carried_rejected(self):
        ch = _make_char(gold=100, bank_balance=0)
        _deposit(ch, "999")
        self.assertEqual(ch.gold, 100)
        self.assertEqual(ch.bank_balance, 0)

    def test_deposit_zero_rejected(self):
        ch = _make_char(gold=200, bank_balance=50)
        _deposit(ch, "0")
        self.assertEqual(ch.gold, 200)
        self.assertEqual(ch.bank_balance, 50)

    def test_deposit_negative_rejected(self):
        ch = _make_char(gold=200, bank_balance=50)
        _deposit(ch, "-50")
        self.assertEqual(ch.gold, 200)
        self.assertEqual(ch.bank_balance, 50)

    def test_deposit_non_numeric_rejected(self):
        ch = _make_char(gold=200)
        _deposit(ch, "twelve gold")
        self.assertEqual(ch.gold, 200)
        self.assertEqual(ch.bank_balance, 0)

    def test_deposit_float_rejected(self):
        # int() on "3.5" raises ValueError — should be rejected
        ch = _make_char(gold=200)
        _deposit(ch, "3.5")
        self.assertEqual(ch.gold, 200)
        self.assertEqual(ch.bank_balance, 0)

    def test_deposit_cancelled_by_user(self):
        ch = _make_char(gold=500)
        _deposit(ch, "100", confirm="n")
        self.assertEqual(ch.gold, 500)
        self.assertEqual(ch.bank_balance, 0)

    def test_deposit_from_empty_purse(self):
        ch = _make_char(gold=0)
        _deposit(ch, "50")
        self.assertEqual(ch.gold, 0)
        self.assertEqual(ch.bank_balance, 0)

    def test_deposit_all_from_empty_purse(self):
        # "all" with 0 gold → amt=0 → rejected silently
        ch = _make_char(gold=0, bank_balance=100)
        _deposit(ch, "all")
        self.assertEqual(ch.bank_balance, 100)  # unchanged

# ── WITHDRAW ──────────────────────────────────────────────────────────────────

class TestWithdraw(unittest.TestCase):

    def test_valid_partial_withdraw(self):
        ch = _make_char(gold=100, bank_balance=300)
        _withdraw(ch, "150")
        self.assertEqual(ch.bank_balance, 150)
        self.assertEqual(ch.gold, 250)

    def test_withdraw_all_keyword(self):
        ch = _make_char(gold=50, bank_balance=200)
        _withdraw(ch, "all")
        self.assertEqual(ch.bank_balance, 0)
        self.assertEqual(ch.gold, 250)

    def test_withdraw_exact_balance(self):
        ch = _make_char(gold=0, bank_balance=100)
        _withdraw(ch, "100")
        self.assertEqual(ch.bank_balance, 0)
        self.assertEqual(ch.gold, 100)

    def test_withdraw_over_balance_rejected(self):
        ch = _make_char(gold=50, bank_balance=100)
        _withdraw(ch, "500")
        self.assertEqual(ch.bank_balance, 100)
        self.assertEqual(ch.gold, 50)

    def test_withdraw_zero_rejected(self):
        ch = _make_char(gold=100, bank_balance=200)
        _withdraw(ch, "0")
        self.assertEqual(ch.bank_balance, 200)
        self.assertEqual(ch.gold, 100)

    def test_withdraw_negative_rejected(self):
        ch = _make_char(gold=100, bank_balance=200)
        _withdraw(ch, "-10")
        self.assertEqual(ch.bank_balance, 200)
        self.assertEqual(ch.gold, 100)

    def test_withdraw_non_numeric_rejected(self):
        ch = _make_char(gold=100, bank_balance=200)
        _withdraw(ch, "a lot")
        self.assertEqual(ch.bank_balance, 200)
        self.assertEqual(ch.gold, 100)

    def test_withdraw_float_rejected(self):
        ch = _make_char(gold=0, bank_balance=200)
        _withdraw(ch, "10.5")
        self.assertEqual(ch.bank_balance, 200)

    def test_withdraw_cancelled_by_user(self):
        ch = _make_char(gold=50, bank_balance=200)
        _withdraw(ch, "100", confirm="n")
        self.assertEqual(ch.bank_balance, 200)
        self.assertEqual(ch.gold, 50)

    def test_withdraw_from_empty_bank_rejected(self):
        ch = _make_char(gold=200, bank_balance=0)
        _withdraw(ch, "50")
        self.assertEqual(ch.bank_balance, 0)
        self.assertEqual(ch.gold, 200)

    def test_withdraw_all_from_empty_bank(self):
        # "all" with balance=0 → amt=0 → rejected
        ch = _make_char(gold=200, bank_balance=0)
        _withdraw(ch, "all")
        self.assertEqual(ch.gold, 200)   # unchanged

# ── BALANCE display ───────────────────────────────────────────────────────────

class TestBalance(unittest.TestCase):

    def test_shows_both_gold_and_bank(self):
        ch = _make_char(gold=333, bank_balance=777)
        buf = io.StringIO()
        with patch("tavern.tc", side_effect=_no_color), redirect_stdout(buf):
            tavern._show_balance(ch)
        out = buf.getvalue()
        self.assertIn("333", out)
        self.assertIn("777", out)

    def test_shows_zeroes_when_both_empty(self):
        ch = _make_char(gold=0, bank_balance=0)
        buf = io.StringIO()
        with patch("tavern.tc", side_effect=_no_color), redirect_stdout(buf):
            tavern._show_balance(ch)
        out = buf.getvalue()
        self.assertIn("0", out)

    def test_does_not_modify_character(self):
        ch = _make_char(gold=100, bank_balance=50)
        with redirect_stdout(io.StringIO()):
            tavern._show_balance(ch)
        self.assertEqual(ch.gold, 100)
        self.assertEqual(ch.bank_balance, 50)

# ── Persistence ───────────────────────────────────────────────────────────────

class TestPersistence(unittest.TestCase):
    """Real disk I/O — each test saves and reloads a character."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._orig_dir = char_mod.CHARACTERS_DIR
        char_mod.CHARACTERS_DIR = self.tmpdir

    def tearDown(self):
        char_mod.CHARACTERS_DIR = self._orig_dir
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _deposit(self, ch, amt_str):
        with patch("tavern.tinput", return_value="y"), \
             redirect_stdout(io.StringIO()):
            tavern._bank_deposit(amt_str, ch)   # real character.save()

    def _withdraw(self, ch, amt_str):
        with patch("tavern.tinput", return_value="y"), \
             redirect_stdout(io.StringIO()):
            tavern._bank_withdraw(amt_str, ch)

    def test_deposit_survives_reload(self):
        ch = _make_char(gold=500, bank_balance=0, name="P_Dep")
        self._deposit(ch, "250")
        loaded = Character.load("P_Dep")
        self.assertIsNotNone(loaded, "save() must have been called")
        self.assertEqual(loaded.bank_balance, 250)
        self.assertEqual(loaded.gold, 250)

    def test_withdraw_survives_reload(self):
        ch = _make_char(gold=0, bank_balance=400, name="P_Wdw")
        self._withdraw(ch, "100")
        loaded = Character.load("P_Wdw")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.bank_balance, 300)
        self.assertEqual(loaded.gold, 100)

    def test_deposit_reload_withdraw_round_trip(self):
        ch = _make_char(gold=1000, bank_balance=0, name="P_RT")
        self._deposit(ch, "400")

        mid = Character.load("P_RT")
        self.assertEqual(mid.bank_balance, 400)
        self.assertEqual(mid.gold, 600)

        self._withdraw(mid, "150")

        final = Character.load("P_RT")
        self.assertEqual(final.bank_balance, 250)
        self.assertEqual(final.gold, 750)

    def test_bank_balance_survives_adventure_save(self):
        """bank_balance written by the bank is not clobbered by a later save()
        that the adventure engine might issue (simulated here)."""
        ch = _make_char(gold=500, bank_balance=0, name="P_Adv")
        self._deposit(ch, "200")          # bank_balance=200, gold=300

        # Engine modifies character in-place and saves (e.g., loot, hp)
        ch.gold  += 50
        ch.hp     = ch.hp_max
        ch.is_beginner = False
        ch.adventures_completed.append("The Test Dungeon")
        ch.save()                          # the engine/handle_engine_return save

        loaded = Character.load("P_Adv")
        self.assertEqual(loaded.bank_balance, 200,
                         "bank_balance must survive the engine save")
        self.assertEqual(loaded.gold, 350)
        self.assertFalse(loaded.is_beginner)

    def test_multiple_deposits_accumulate(self):
        ch = _make_char(gold=900, bank_balance=0, name="P_Multi")
        self._deposit(ch, "100")
        self._deposit(ch, "200")
        self._deposit(ch, "50")
        loaded = Character.load("P_Multi")
        self.assertEqual(loaded.bank_balance, 350)
        self.assertEqual(loaded.gold, 550)

# ── Shop persistence ──────────────────────────────────────────────────────────

class TestShopPersistence(unittest.TestCase):
    """Verify that shop purchases persist to disk without launching an adventure."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._orig_dir      = char_mod.CHARACTERS_DIR
        self._orig_item_path = tavern._items_path
        char_mod.CHARACTERS_DIR = self.tmpdir
        # Redirect items file to tmpdir so we don't pollute the real characters/
        tavern._items_path = lambda ch: os.path.join(
            self.tmpdir,
            ch.name.lower().replace(" ", "_") + "_items.json"
        )

    def tearDown(self):
        char_mod.CHARACTERS_DIR = self._orig_dir
        tavern._items_path      = self._orig_item_path
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _buy(self, ch, template):
        """Simulate a shop purchase: deduct gold, add item, save both."""
        ch.gold -= template["price"]
        with redirect_stdout(io.StringIO()):
            tavern._add_to_inventory(ch, template)  # writes items file
        ch.save()                                    # writes character file

    def test_gold_deduction_persists(self):
        ch = _make_char(gold=500, name="Shop_G")
        self._buy(ch, {"name": "Iron Sword", "artifact_type": "weapon",
                       "price": 80, "weight": 3,
                       "damage_dice": 1, "damage_sides": 8, "value": 80})
        loaded = Character.load("Shop_G")
        self.assertEqual(loaded.gold, 420)

    def test_item_appears_in_inventory(self):
        ch = _make_char(gold=500, name="Shop_I")
        self._buy(ch, {"name": "Iron Sword", "artifact_type": "weapon",
                       "price": 80, "weight": 3,
                       "damage_dice": 1, "damage_sides": 8, "value": 80})
        loaded  = Character.load("Shop_I")
        carried = tavern._load_carried(loaded)
        self.assertIn("Iron Sword", [a.name for a in carried])

    def test_no_adventure_needed(self):
        """Two items bought, no adventure; both survive reload."""
        ch = _make_char(gold=1000, name="Shop_NA")
        for tmpl in [
            {"name": "Shortsword",    "artifact_type": "weapon",
             "price": 50, "weight": 2, "damage_dice": 1, "damage_sides": 6, "value": 50},
            {"name": "Leather Armor", "artifact_type": "armor",
             "price": 30, "weight": 5, "armor_class": 2, "value": 30},
        ]:
            self._buy(ch, tmpl)

        loaded  = Character.load("Shop_NA")
        self.assertEqual(loaded.gold, 920)
        carried = tavern._load_carried(loaded)
        names   = [a.name for a in carried]
        self.assertIn("Shortsword",    names)
        self.assertIn("Leather Armor", names)

    def test_bought_item_equippable(self):
        """After buying and equipping in tavern, equipped slot persists."""
        ch = _make_char(gold=500, name="Shop_E")
        tmpl = {"name": "Longsword", "artifact_type": "weapon",
                "price": 100, "weight": 4, "damage_dice": 1, "damage_sides": 10, "value": 100}
        self._buy(ch, tmpl)

        # Equip via tavern helper
        with patch("tavern.tinput", return_value=""), \
             redirect_stdout(io.StringIO()):
            tavern.cmd_equip_tavern("Longsword", ch)

        loaded = Character.load("Shop_E")
        self.assertEqual(loaded.equipped.get("weapon"), "Longsword")

# ── runner ────────────────────────────────────────────────────────────────────

class _TrackingResult(unittest.TextTestResult):
    """Subclass that collects per-test pass/fail details."""
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self._log = []          # (status, name, detail)

    def addSuccess(self, test):
        super().addSuccess(test)
        self._log.append(("PASS", test._testMethodName, ""))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._log.append(("FAIL", test._testMethodName, str(err[1]).splitlines()[0]))

    def addError(self, test, err):
        super().addError(test, err)
        self._log.append(("ERROR", test._testMethodName, str(err[1]).splitlines()[0]))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._log.append(("SKIP", test._testMethodName, reason))


if __name__ == "__main__":
    suites = [
        unittest.TestLoader().loadTestsFromTestCase(c)
        for c in (TestDeposit, TestWithdraw, TestBalance,
                  TestPersistence, TestShopPersistence)
    ]
    master = unittest.TestSuite(suites)

    stream = io.StringIO()
    runner = unittest.TextTestRunner(
        stream=stream, resultclass=_TrackingResult, verbosity=0)
    result = runner.run(master)

    W_NAME = 45
    sections = [
        ("DEPOSIT",          TestDeposit),
        ("WITHDRAW",         TestWithdraw),
        ("BALANCE",          TestBalance),
        ("PERSISTENCE",      TestPersistence),
        ("SHOP PERSISTENCE", TestShopPersistence),
    ]
    # Map method names back to their class for section grouping
    class_of = {}
    for cls in (TestDeposit, TestWithdraw, TestBalance,
                TestPersistence, TestShopPersistence):
        for name in dir(cls):
            if name.startswith("test_"):
                class_of[name] = cls.__name__

    logs_by_class = {}
    for status, name, detail in result._log:
        cls_name = class_of.get(name, "?")
        logs_by_class.setdefault(cls_name, []).append((status, name, detail))

    print()
    print("=" * 60)
    print("  Bank & Shop Persistence — Test Results")
    print("=" * 60)

    passes = fails = 0
    for section_label, cls in [
        ("DEPOSIT",          TestDeposit),
        ("WITHDRAW",         TestWithdraw),
        ("BALANCE",          TestBalance),
        ("PERSISTENCE",      TestPersistence),
        ("SHOP PERSISTENCE", TestShopPersistence),
    ]:
        entries = logs_by_class.get(cls.__name__, [])
        if not entries:
            continue
        print(f"\n  ── {section_label} {'─' * (50 - len(section_label))}")
        for status, name, detail in entries:
            icon = "✅" if status == "PASS" else "❌"
            label = name.replace("test_", "").replace("_", " ")
            print(f"  {icon} {status:<5}  {label}")
            if detail:
                print(f"         └─ {detail}")
            if status == "PASS":
                passes += 1
            else:
                fails += 1

    print()
    print("─" * 60)
    total = passes + fails
    if fails == 0:
        print(f"  All {total} tests PASSED")
    else:
        print(f"  {passes}/{total} passed — {fails} FAILED")
    print("─" * 60)
    print()

    # Edge case notes
    print("  Edge case observations:")
    print("  • float input ('3.5') is rejected by int() → ValueError → correct")
    print("  • 'DEPOSIT ALL' with 0 gold → amt=0 → rejected by <=0 guard → correct")
    print("  • 'WITHDRAW ALL' with 0 balance → same guard → correct")
    print("  • Negative input is caught by the <=0 guard (not a separate check)")
    print("  • bank_balance field is included in every character.save() call")
    print("    so it cannot be silently dropped by an adventure engine save")
    print()

    sys.exit(1 if fails else 0)
