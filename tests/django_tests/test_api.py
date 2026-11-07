"""Testes de integração Django (NÃO executados no ambiente de desenvolvimento do projeto).

Rode com:  DB_ENGINE=sqlite python manage.py test tests.django_tests
(ou com MySQL configurado no .env; o usuário do banco precisa de permissão para criar o banco de teste)."""
import json
from pathlib import Path

from django.conf import settings
from django.test import Client, TestCase

from apps.accounts.models import Conta
from apps.cards import schema, services as card_services
from apps.core.models import Servidor
from apps.decks.models import Deck, DeckCarta, Grimorium, GrimoriumCarta
from apps.decks import services as deck_services


def load_cards():
    text = (Path(settings.BASE_DIR) / "seeds" / "cards.json").read_text(encoding="utf-8")
    card_services.import_cards(schema.parse_json(text))
    Servidor.objects.get_or_create(name="Servidor 1")


class AccountApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        load_cards()

    def register(self, c, name="Jogador1", pw="senha123", email="j1@example.com"):
        return c.post("/api/contas/", json.dumps({"name": name, "password": pw, "password2": pw, "email": email}),
                      content_type="application/json")

    def test_register_creates_starter_deck_and_empty_grimorium(self):
        c = Client()
        r = self.register(c)
        self.assertEqual(r.status_code, 201)
        conta = Conta.objects.get(name="Jogador1")
        self.assertNotEqual(conta.password, "senha123")          # hash do Django
        self.assertLessEqual(len(conta.password), 128)
        self.assertEqual(conta.acc_status, 1)
        deck = Deck.objects.get(owner=conta, slot=1)
        self.assertEqual(deck.cards.count(), 40)
        ids = list(deck.cards.values_list("carta_id", flat=True))
        self.assertLessEqual(max(ids.count(i) for i in set(ids)), 3)
        self.assertFalse(deck.cards.filter(is_foil=True).exists() or deck.cards.filter(is_shiny=True).exists())
        self.assertEqual(Grimorium.objects.get(owner=conta).cards.count(), 0)

    def test_validation_and_duplicates(self):
        c = Client()
        self.assertEqual(self.register(c, name="ab").status_code, 422)
        self.assertEqual(self.register(c).status_code, 201)
        self.assertEqual(self.register(c, name="jogador1", email="x@example.com").status_code, 409)  # nome (case-insens.)
        self.assertEqual(self.register(c, name="Outro1").status_code, 409)                          # e-mail

    def test_login_logout_and_single_session(self):
        c1, c2 = Client(), Client()
        self.register(c1)
        body = json.dumps({"name": "Jogador1", "password": "senha123"})
        self.assertEqual(c1.post("/api/login/", body, content_type="application/json").status_code, 200)
        self.assertEqual(c1.get("/api/me/").status_code, 200)
        self.assertEqual(c2.post("/api/login/", body, content_type="application/json").status_code, 200)
        self.assertEqual(c1.get("/api/me/").status_code, 401)     # sessão anterior derrubada (D-26)
        bad = json.dumps({"name": "Jogador1", "password": "errada1"})
        self.assertEqual(Client().post("/api/login/", bad, content_type="application/json").status_code, 401)

    def test_blocked_account_cannot_login(self):
        c = Client()
        self.register(c)
        Conta.objects.filter(name="Jogador1").update(acc_code="RED")
        r = c.post("/api/login/", json.dumps({"name": "Jogador1", "password": "senha123"}), content_type="application/json")
        self.assertEqual(r.status_code, 401)


class DeckServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        load_cards()

    def setUp(self):
        self.user = Conta.objects.create_conta("Dono1", "d@example.com", "senha123")
        deck_services.create_starter_setup(self.user, deck_count=2)

    def test_move_between_deck_and_grimorium(self):
        d1 = Deck.objects.get(owner=self.user, slot=1)
        uid = d1.cards.first().card_uid
        deck_services.move_card(self.user, str(uid), "grimorium")
        self.assertEqual(d1.cards.count(), 39)
        self.assertEqual(GrimoriumCarta.objects.filter(grimorium__owner=self.user).count(), 1)
        deck_services.move_card(self.user, str(uid), "deck", d1.id)
        self.assertEqual(d1.cards.count(), 40)

    def test_deck_limits(self):
        d1 = Deck.objects.get(owner=self.user, slot=1)
        g = Grimorium.objects.get(owner=self.user)
        extra = GrimoriumCarta.objects.create(grimorium=g, carta_id=1)
        with self.assertRaises(Exception):   # deck cheio (40)
            deck_services.move_card(self.user, str(extra.card_uid), "deck", d1.id)

    def test_premium_slots_locked(self):
        with self.assertRaises(Exception):
            deck_services.create_deck(self.user, 4)

    def test_other_users_cards_untouchable(self):
        other = Conta.objects.create_conta("Outro2", "o@example.com", "senha123")
        deck_services.create_starter_setup(other)
        foreign = DeckCarta.objects.filter(deck__owner=other).first()
        with self.assertRaises(Exception):
            deck_services.move_card(self.user, str(foreign.card_uid), "grimorium")

    def test_battle_deck_requires_40(self):
        self.assertEqual(len(deck_services.build_battle_deck(self.user)), 40)
        d1 = Deck.objects.get(owner=self.user, slot=1)
        d1.cards.first().delete()
        with self.assertRaises(Exception):
            deck_services.build_battle_deck(self.user)


class CatalogTests(TestCase):
    def test_import_report(self):
        load_cards()
        rep = card_services.import_cards([{"card_id": 0, "type": "SUMMON", "name": "x"},
                                          {"card_id": 500, "type": "SUMMON", "name": "Nova", "power": 2, "elements": ["F"]}])
        self.assertEqual(rep["created"], 1)
        self.assertEqual(len(rep["errors"]), 1)
        self.assertIn(500, card_services.load_catalog())
