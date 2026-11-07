"""Testes das regras puras (sem Django): cadastro, cartas, decks, recompensas, seeds."""
import json
import os
import random
import unittest
from collections import Counter

from apps.accounts import rules as acc
from apps.cards import schema
from apps.decks import rules as deck
from apps.game.rewards import compute_rewards
from engine.constants import mana_cost_for_power

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AccountRules(unittest.TestCase):
    def test_name(self):
        self.assertEqual(acc.validate_name("Joao"), [])
        self.assertIn("err.name_length", acc.validate_name("Joa"))
        self.assertIn("err.name_length", acc.validate_name("a" * 17))
        self.assertIn("err.name_chars", acc.validate_name("João1"))
        self.assertIn("err.name_chars", acc.validate_name("jo ao"))

    def test_password(self):
        self.assertEqual(acc.validate_password("123456", "123456"), [])
        self.assertIn("err.password_length", acc.validate_password("12345"))
        self.assertIn("err.password_length", acc.validate_password("x" * 33))
        self.assertIn("err.password_mismatch", acc.validate_password("123456", "654321"))

    def test_email(self):
        self.assertEqual(acc.validate_email("a@b.co"), [])
        for bad in ("abc", "a@b", "@b.com", "a@@b.com", "a b@c.com", "a@.com", "a@b.", "x" * 60 + "@b.com"):
            self.assertTrue(acc.validate_email(bad), bad)

    def test_registration(self):
        self.assertEqual(acc.validate_registration("Joao", "123456", "123456", "a@b.com"), {})
        self.assertEqual(set(acc.validate_registration("a", "1", "2", "x")), {"name", "password", "email"})


class CardSchema(unittest.TestCase):
    def good(self, **kw):
        d = {"card_id": 1, "type": "SUMMON", "name": "X", "power": 3, "elements": ["F"]}
        d.update(kw)
        return d

    def test_valid_and_invalid(self):
        self.assertEqual(schema.validate_card_dict(self.good()), [])
        self.assertTrue(schema.validate_card_dict(self.good(card_id=0)))
        self.assertTrue(schema.validate_card_dict(self.good(type="X")))
        self.assertTrue(schema.validate_card_dict(self.good(elements=["Z"])))
        self.assertTrue(schema.validate_card_dict(self.good(mana_gains=[{"element": "F", "value": 9}])))
        self.assertTrue(schema.validate_card_dict(self.good(skills=[{"slot": 1, "name": "a"}] * 2)))

    def test_import_analysis_and_csv_roundtrip(self):
        res = schema.analyze_import([self.good(), self.good(), self.good(card_id=0)])
        self.assertEqual(len(res["valid"]), 1)
        self.assertEqual(res["duplicates"], [1])
        self.assertEqual(len(res["errors"]), 2)
        with open(os.path.join(ROOT, "seeds", "cards.json"), encoding="utf-8") as f:
            cards = json.load(f)["cards"]
        again = schema.parse_csv(schema.to_csv(cards))
        self.assertEqual([schema.normalize_card_dict(c) for c in again], cards)


class DeckRules(unittest.TestCase):
    def test_starter_deck_max_three_copies(self):
        for seed in range(30):
            ids = deck.random_starter_card_ids(range(1, 101), random.Random(seed))
            self.assertEqual(len(ids), 40)
            self.assertLessEqual(max(Counter(ids).values()), 3)
            self.assertTrue(all(1 <= i <= 100 for i in ids))

    def test_starter_small_catalog(self):
        with self.assertRaises(ValueError):
            deck.random_starter_card_ids([1, 2, 3])

    def test_limits(self):
        self.assertEqual(deck.can_add_to_deck([1, 1], 1), "")
        self.assertEqual(deck.can_add_to_deck([1, 1, 1], 1), "err.deck_max_copies")
        self.assertEqual(deck.can_add_to_deck(list(range(40)), 99), "err.deck_full")
        self.assertEqual(deck.can_add_to_grimorium(500), "err.grimorium_full")
        self.assertTrue(deck.slot_allowed(3, False))
        self.assertFalse(deck.slot_allowed(4, False))
        self.assertTrue(deck.slot_allowed(6, True))

    def test_six_decks_allow_eighteen_copies(self):  # D-06: limite é por deck
        decks = [deck.random_starter_card_ids([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14], random.Random(i))
                 for i in range(6)]
        self.assertTrue(all(max(Counter(d).values()) <= 3 for d in decks))


class Rewards(unittest.TestCase):
    def test_all(self):
        st = {"A": {"destroyed": 2}, "B": {"destroyed": 1}}
        r = compute_rewards({"type": "win", "winner": "A", "loser": "B", "reason": "life"}, "versus", st)
        self.assertEqual((r["A"]["battlepoints"], r["B"]["battlepoints"], r["A"]["victories"]), (100, 50, 1))
        self.assertEqual((r["A"]["magicdust"], r["B"]["magicdust"]), (2, 1))
        r = compute_rewards({"type": "draw"}, "versus")
        self.assertEqual((r["A"]["battlepoints"], r["B"]["battlepoints"]), (25, 25))
        r = compute_rewards({"type": "win", "winner": "B", "loser": "A", "reason": "afk"}, "versus")
        self.assertEqual((r["A"]["battlepoints"], r["B"]["battlepoints"]), (0, 10))
        r = compute_rewards({"type": "win", "winner": "B", "loser": "A", "reason": "life"}, "debug")
        self.assertEqual(r["B"]["battlepoints"], 0)
        self.assertEqual(compute_rewards(None, "versus")["A"]["battlepoints"], 0)


class SeedCards(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "seeds", "cards.json"), encoding="utf-8") as f:
            self.cards = json.load(f)["cards"]

    def test_catalog(self):
        self.assertEqual([c["card_id"] for c in self.cards], list(range(1, 101)))
        self.assertEqual(schema.analyze_import(self.cards)["errors"], [])
        self.assertEqual(len({c["name"] for c in self.cards}), 100)

    def test_first_forty_and_costs(self):
        for c in self.cards[:40]:
            self.assertTrue(set(c["elements"]) <= set("EFIA"))
            self.assertTrue(1 <= c["power"] <= 10)
        for c in self.cards:
            self.assertEqual(c["mana_cost"], mana_cost_for_power(c["power"]))
            self.assertTrue(2 <= len(c["mana_gains"]) <= 4)
            self.assertTrue(all(-3 <= g["value"] <= 3 and g["value"] != 0 for g in c["mana_gains"]))
            self.assertEqual(len(c["skills"]), 1)

    def test_skill_groups_of_three(self):
        for i in range(0, 99, 3):
            group = {c["skills"][0]["name"] for c in self.cards[i:i + 3]}
            self.assertEqual(len(group), 1)

    def test_balance_cheap_cards_gain_more(self):
        avg = {}
        for cost in range(4):
            vals = [sum(g["value"] for g in c["mana_gains"]) for c in self.cards if c["mana_cost"] == cost]
            avg[cost] = sum(vals) / len(vals)
        self.assertGreater(avg[0], avg[3])


if __name__ == "__main__":
    unittest.main()


class RewardsAborted(unittest.TestCase):
    def test_aborted_gives_nothing(self):
        r = compute_rewards({"type": "aborted", "winner": None, "loser": None, "reason": "abandon"}, "versus",
                            {"A": {"destroyed": 3}})
        self.assertEqual(r["A"], {"battlepoints": 0, "magicdust": 0, "victories": 0})
