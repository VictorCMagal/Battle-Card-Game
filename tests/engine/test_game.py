import unittest

from engine import GameError
from engine.initiative import draw_initiative, resolve_symbols
from tests.engine.helpers import card, catalog, new_game


class TurnAndSetup(unittest.TestCase):
    def test_initial_state(self):
        g = new_game(catalog(card(1, 3)))
        a, b = g.players["A"], g.players["B"]
        self.assertEqual((a.life, a.mana, len(a.hand)), (20, 1, 5))
        self.assertEqual(len(b.hand), 5)
        self.assertEqual((a.avatar.x, a.avatar.y), (2, 0))
        self.assertEqual((b.avatar.x, b.avatar.y), (2, 4))
        self.assertEqual(g.phase, "ACTION")

    def test_card_id_zero_invalid(self):
        with self.assertRaises(ValueError):
            card(0, 3)

    def test_not_your_turn(self):
        g = new_game(catalog(card(1, 3)))
        with self.assertRaises(GameError):
            g.apply({"type": "walk_avatar", "player": "B", "x": 2, "y": 3})

    def test_meditation_and_draw_to_five(self):
        g = new_game(catalog(card(1, 3)))
        g.apply({"type": "end_turn", "player": "A"})
        self.assertEqual(g.players["A"].mana, 2)  # meditação
        self.assertEqual(g.current, "B")
        self.assertEqual(len(g.players["B"].hand), 5)

    def test_walk_blocks_meditation_and_adjacent_only(self):
        g = new_game(catalog(card(1, 3)))
        with self.assertRaises(GameError):
            g.apply({"type": "walk_avatar", "player": "A", "x": 3, "y": 1})  # diagonal
        g.apply({"type": "walk_avatar", "player": "A", "x": 2, "y": 1})
        with self.assertRaises(GameError):
            g.apply({"type": "walk_avatar", "player": "A", "x": 2, "y": 2})
        g.apply({"type": "end_turn", "player": "A"})
        self.assertEqual(g.players["A"].mana, 1)

    def test_deck_burn(self):
        g = new_game(catalog(card(1, 3)), deck_a=[1] * 5, deck_b=[1] * 40)
        # A: mão 5, deck 0. Ela summona 1 carta e passa; no próximo turno falta 1.
        g.apply({"type": "summon", "player": "A", "uid": "a0", "x": 1, "y": 0, "face_up": False})
        g.apply({"type": "end_turn", "player": "A"})
        g.apply({"type": "end_turn", "player": "B"})
        self.assertEqual(g.players["A"].life, 19)

    def test_draw_when_both_die(self):
        g = new_game(catalog(card(1, 3)))
        g.players["A"].life = 1
        g.players["B"].life = 1
        g.damage_life("A", 1)
        g.damage_life("B", 1)
        g._check_end()
        self.assertEqual(g.result["type"], "draw")

    def test_afk_three_timeouts(self):
        g = new_game(catalog(card(1, 3)))
        g.expire_turn()  # A (1)
        g.expire_turn()  # B
        g.expire_turn()  # A (2)
        g.expire_turn()  # B
        g.expire_turn()  # A (3) -> perde
        self.assertEqual(g.result["reason"], "afk")
        self.assertEqual(g.result["winner"], "B")

    def test_afk_not_in_debug(self):
        g = new_game(catalog(card(1, 3)), mode="debug")
        for _ in range(8):
            g.expire_turn()
        self.assertIsNone(g.result)

    def test_action_resets_afk(self):
        g = new_game(catalog(card(1, 3)))
        g.expire_turn(); g.expire_turn()
        g.apply({"type": "walk_avatar", "player": "A", "x": 2, "y": 1})
        g.expire_turn()
        self.assertEqual(g.players["A"].afk_count, 0)

    def test_initiative(self):
        self.assertEqual(resolve_symbols("X", None), ("X", "O"))
        self.assertEqual(resolve_symbols(None, "X"), ("O", "X"))
        with self.assertRaises(GameError):
            resolve_symbols("X", "X")
        sym, first = draw_initiative("X", "O", rng=type("R", (), {"choice": lambda s, q: "O"})())
        self.assertEqual((sym, first), ("O", "B"))


class Summoning(unittest.TestCase):
    def setUp(self):
        self.cat = catalog(card(1, 3), card(2, 5, cost=2), card(3, 10, cost=3, elements=("I",)))

    def test_adjacent_and_diagonal(self):
        g = new_game(self.cat)
        g.apply({"type": "summon", "player": "A", "uid": "a0", "x": 3, "y": 1, "face_up": True})
        self.assertEqual(g.board[(3, 1)].card_id, 1)
        with self.assertRaises(GameError):  # só uma summon por turno
            g.apply({"type": "summon", "player": "A", "uid": "a1", "x": 1, "y": 1, "face_up": True})

    def test_far_tile_rejected(self):
        g = new_game(self.cat)
        with self.assertRaises(GameError):
            g.apply({"type": "summon", "player": "A", "uid": "a0", "x": 2, "y": 3, "face_up": True})

    def test_double_cast(self):
        g = new_game(self.cat)
        g.apply({"type": "summon", "player": "A", "uid": "a0", "x": 1, "y": 0, "face_up": True})
        g.apply({"type": "double_cast", "player": "A"})
        self.assertEqual(g.players["A"].mana, 0)
        g.apply({"type": "summon", "player": "A", "uid": "a1", "x": 3, "y": 0, "face_up": True})
        self.assertEqual(g.summons_done, 2)

    def test_double_cast_needs_mana_and_summon(self):
        g = new_game(self.cat)
        with self.assertRaises(GameError):
            g.apply({"type": "double_cast", "player": "A"})

    def test_mana_cost_failure(self):
        g = new_game(self.cat, deck_a=[3] * 10)
        g.apply({"type": "summon", "player": "A", "uid": "a0", "x": 1, "y": 0, "face_up": True})
        a = g.players["A"]
        self.assertEqual(a.mana, 0)
        self.assertEqual(a.life, 20 - 2)  # custo 3, mana 1 -> faltou 2
        self.assertNotIn((1, 0), g.board)
        self.assertEqual(len(a.discard), 1)

    def test_mana_cost_charged_once_on_flip(self):
        g = new_game(self.cat, deck_a=[2] * 10)
        g.players["A"].mana = 3
        g.apply({"type": "summon", "player": "A", "uid": "a0", "x": 1, "y": 0, "face_up": False})
        self.assertEqual(g.players["A"].mana, 3)  # face_down não cobra
        g._flip_up(g.board[(1, 0)])
        self.assertEqual(g.players["A"].mana, 1)
        g.board[(1, 0)].face_up = False
        g._flip_up(g.board[(1, 0)])
        self.assertEqual(g.players["A"].mana, 1)  # não cobra de novo

    def test_summon_on_own_card_discards_block_card(self):
        g = new_game(self.cat)
        old = g.spawn("A", 1, 1, 0)
        g.apply({"type": "summon", "player": "A", "uid": "a0", "x": 1, "y": 0, "face_up": False})
        self.assertIsNot(g.board[(1, 0)], old)
        self.assertTrue(any(c is old for c in g.players["A"].discard))

    def test_summon_on_enemy_avatar_only_if_lethal(self):
        g = new_game(self.cat, deck_a=[1] * 10)
        g.board.pop((2, 4))  # afasta o Avatar B para perto de A
        av = g.players["B"].avatar
        av.x, av.y = 2, 1
        g.board[(2, 1)] = av
        with self.assertRaises(GameError):
            g.apply({"type": "summon", "player": "A", "uid": "a0", "x": 2, "y": 1, "face_up": True})
        g.players["B"].life = 3
        g.apply({"type": "summon", "player": "A", "uid": "a0", "x": 2, "y": 1, "face_up": True})
        self.assertEqual(g.result["winner"], "A")

    def test_cooldown_summoned_cannot_move(self):
        g = new_game(self.cat)
        g.apply({"type": "summon", "player": "A", "uid": "a0", "x": 1, "y": 0, "face_up": True})
        with self.assertRaises(GameError):
            g.apply({"type": "move", "player": "A", "uid": "a0", "x": 1, "y": 1})

    def test_non_summon_type_not_implemented(self):
        cat = catalog(card(1, 1, type_="SPELL"))
        g = new_game(cat)
        with self.assertRaises(GameError):
            g.apply({"type": "summon", "player": "A", "uid": "a0", "x": 1, "y": 0, "face_up": True})


class Combat(unittest.TestCase):
    def cat(self):
        return catalog(card(1, 3), card(5, 5, elements=("I",)), card(10, 10), card(7, 5, shield=2),
                       card(8, 5, gains=(("I", 2), ("F", -1))))

    def prep(self, a_id, b_id, ax=1, ay=2):
        g = new_game(self.cat())
        atk = g.spawn("A", a_id, ax, ay)
        tgt = g.spawn("B", b_id, ax + 1, ay)
        return g, atk, tgt

    def test_spec_example_ten_vs_five(self):
        g, atk, tgt = self.prep(10, 5)
        g.apply({"type": "move", "player": "A", "uid": atk.uid, "x": 2, "y": 2})
        self.assertEqual(g.players["B"].life, 15)        # excesso 5
        self.assertEqual(atk.damage, 5)                   # contra-ataque
        self.assertEqual(atk.effective_power, 5)
        self.assertTrue(any(c is tgt for c in g.players["B"].discard))
        self.assertIs(g.board[(2, 2)], atk)               # ocupa o bloco (D-10)
        self.assertNotIn((1, 2), g.board)
        self.assertEqual(g.stats["A"]["destroyed"], 1)

    def test_equal_power_both_destroyed(self):
        g, atk, tgt = self.prep(5, 5)
        g.apply({"type": "move", "player": "A", "uid": atk.uid, "x": 2, "y": 2})
        self.assertNotIn((1, 2), g.board)
        self.assertNotIn((2, 2), g.board)
        self.assertEqual(g.players["A"].life, 20)
        self.assertEqual(g.players["B"].life, 20)

    def test_weaker_attacker_destroyed_with_excess_to_own_life(self):
        g, atk, tgt = self.prep(1, 10)  # C1 power 3 contra power 10
        g.apply({"type": "move", "player": "A", "uid": atk.uid, "x": 2, "y": 2})
        self.assertEqual(g.players["A"].life, 20 - (10 - 3))  # excesso do contra-ataque
        self.assertEqual(tgt.damage, 3)
        self.assertIs(g.board[(2, 2)], tgt)

    def test_shield_reduces_damage_and_never_heals(self):
        g, atk, tgt = self.prep(1, 7)  # ataque 3, shield 2 -> 1 de dano
        g.apply({"type": "move", "player": "A", "uid": atk.uid, "x": 2, "y": 2})
        self.assertEqual(tgt.damage, 1)
        g2, atk2, tgt2 = self.prep(1, 7)
        tgt2.shield = 99
        g2.apply({"type": "move", "player": "A", "uid": atk2.uid, "x": 2, "y": 2})
        self.assertEqual(tgt2.damage, 0)

    def test_survivor_stays_in_origin_when_target_survives(self):
        g = new_game(catalog(card(1, 3), card(11, 4, shield=3), card(12, 5)))
        atk = g.spawn("A", 12, 1, 2)
        tgt = g.spawn("B", 11, 2, 2)
        g.apply({"type": "move", "player": "A", "uid": atk.uid, "x": 2, "y": 2})
        self.assertIs(g.board[(1, 2)], atk)
        self.assertIs(g.board[(2, 2)], tgt)

    def test_mana_gain_by_element(self):
        g, atk, tgt = self.prep(8, 5)  # alvo Ice -> +2
        g.apply({"type": "move", "player": "A", "uid": atk.uid, "x": 2, "y": 2})
        self.assertEqual(g.players["A"].mana, 3)

    def test_mana_gain_clamped(self):
        g, atk, tgt = self.prep(8, 5)
        g.players["A"].mana = 6
        g.apply({"type": "move", "player": "A", "uid": atk.uid, "x": 2, "y": 2})
        self.assertEqual(g.players["A"].mana, 6)

    def test_face_down_target_is_revealed(self):
        g, atk, tgt = self.prep(10, 5)
        tgt.face_up = False
        g.apply({"type": "move", "player": "A", "uid": atk.uid, "x": 2, "y": 2})
        self.assertTrue(any(e["type"] == "flip" for e in g.events))

    def test_flip_cost_failure_aborts_combat(self):
        cat = catalog(card(1, 3), card(9, 5, cost=3))
        g = new_game(cat)
        atk = g.spawn("A", 1, 1, 2)
        tgt = g.spawn("B", 9, 2, 2, face_up=False, paid=False)
        g.apply({"type": "move", "player": "A", "uid": atk.uid, "x": 2, "y": 2})
        self.assertEqual(g.players["B"].life, 18)   # custo 3, MANA 1 -> faltaram 2
        self.assertNotIn((2, 2), g.board)       # alvo descartado, sem combate
        self.assertEqual(atk.damage, 0)

    def test_attack_enemy_avatar(self):
        g = new_game(self.cat())
        atk = g.spawn("A", 10, 2, 3)
        g.apply({"type": "move", "player": "A", "uid": atk.uid, "x": 2, "y": 4})
        self.assertEqual(g.players["B"].life, 10)
        self.assertIs(g.board[(2, 3)], atk)  # não ocupa o bloco do Avatar

    def test_cannot_move_onto_own_avatar(self):
        g = new_game(self.cat())
        c = g.spawn("A", 1, 2, 1)
        with self.assertRaises(GameError):
            g.apply({"type": "move", "player": "A", "uid": c.uid, "x": 2, "y": 0})

    def test_summon_attack_winner_occupies_block(self):
        g = new_game(self.cat(), deck_a=[10] * 10)
        g.players["A"].mana = 6
        tgt = g.spawn("B", 5, 1, 1)
        g.apply({"type": "summon", "player": "A", "uid": "a0", "x": 1, "y": 1, "face_up": True})
        self.assertEqual(g.board[(1, 1)].card_id, 10)
        self.assertEqual(g.board[(1, 1)].owner, "A")
        self.assertTrue(any(c is tgt for c in g.players["B"].discard))

    def test_summon_attack_that_fails_discards_attacker(self):
        g = new_game(self.cat(), deck_a=[1] * 10)
        tgt = g.spawn("B", 10, 1, 1)
        g.apply({"type": "summon", "player": "A", "uid": "a0", "x": 1, "y": 1, "face_up": True})
        self.assertIs(g.board[(1, 1)], tgt)
        self.assertEqual(len(g.players["A"].discard), 1)


class Skills(unittest.TestCase):
    def cat(self):
        sk = lambda n, cost: ((1, n, "2", cost, f"skill.{n}.txt"),)
        return catalog(card(1, 4, skills=sk("Fire Ball", 1)), card(2, 4, skills=sk("Teleport", 2)),
                       card(3, 6, skills=sk("Explosion", 3)), card(4, 4))

    def test_fire_ball(self):
        g = new_game(self.cat())
        c = g.spawn("A", 1, 1, 1)
        t = g.spawn("B", 4, 3, 3)
        g.apply({"type": "use_skill", "player": "A", "uid": c.uid, "slot": 1, "target": {"x": 3, "y": 3}})
        self.assertEqual(t.damage, 2)
        self.assertEqual(g.players["A"].mana, 0)
        with self.assertRaises(GameError):  # uma skill por turno / sem mana
            g.apply({"type": "use_skill", "player": "A", "uid": c.uid, "slot": 1, "target": {"x": 3, "y": 3}})

    def test_skill_not_on_summon_turn_or_after_move(self):
        g = new_game(self.cat(), deck_a=[1] * 10)
        g.players["A"].mana = 5
        g.apply({"type": "summon", "player": "A", "uid": "a0", "x": 1, "y": 0, "face_up": True})
        with self.assertRaises(GameError):
            g.apply({"type": "use_skill", "player": "A", "uid": "a0", "slot": 1, "target": {"x": 3, "y": 3}})
        c = g.spawn("A", 1, 1, 1)
        g.apply({"type": "move", "player": "A", "uid": c.uid, "x": 1, "y": 2})
        with self.assertRaises(GameError):
            g.apply({"type": "use_skill", "player": "A", "uid": c.uid, "slot": 1, "target": {"x": 3, "y": 3}})

    def test_teleport_two_moves_no_attack(self):
        g = new_game(self.cat())
        g.players["A"].mana = 3
        c = g.spawn("A", 2, 0, 2)
        g.spawn("B", 4, 2, 2)
        g.apply({"type": "use_skill", "player": "A", "uid": c.uid, "slot": 1, "target": {}})
        g.apply({"type": "move", "player": "A", "uid": c.uid, "x": 0, "y": 3})
        g.apply({"type": "move", "player": "A", "uid": c.uid, "x": 1, "y": 3})
        self.assertEqual((c.x, c.y), (1, 3))
        with self.assertRaises(GameError):
            g.apply({"type": "move", "player": "A", "uid": c.uid, "x": 1, "y": 2})

    def test_explosion_hits_everyone_around_including_own(self):
        g = new_game(self.cat())
        g.players["A"].mana = 3
        c = g.spawn("A", 3, 2, 2)
        own = g.spawn("A", 4, 1, 1)
        foe = g.spawn("B", 4, 3, 3)
        hidden = g.spawn("B", 4, 2, 3, face_up=False)
        g.apply({"type": "use_skill", "player": "A", "uid": c.uid, "slot": 1, "target": {}})
        self.assertEqual((own.damage, foe.damage, hidden.damage, c.damage), (3, 3, 0, 0))

    def test_explosion_on_avatar_costs_life(self):
        g = new_game(self.cat())
        g.players["A"].mana = 3
        c = g.spawn("A", 3, 2, 3)
        g.apply({"type": "use_skill", "player": "A", "uid": c.uid, "slot": 1, "target": {}})
        self.assertEqual(g.players["B"].life, 17)


class Views(unittest.TestCase):
    def test_hidden_info_not_leaked(self):
        g = new_game(catalog(card(1, 3)))
        g.spawn("B", 1, 3, 3, face_up=False)
        v = g.view_for("A")
        self.assertEqual(v["players"]["B"]["hand"], [])
        self.assertEqual(v["players"]["B"]["hand_count"], 5)
        hidden = [c for c in v["board"] if c["x"] == 3 and c["y"] == 3][0]
        self.assertNotIn("card_id", hidden)
        self.assertEqual(len(g.view_for("A", reveal_all=True)["players"]["B"]["hand"]), 5)


if __name__ == "__main__":
    unittest.main()
