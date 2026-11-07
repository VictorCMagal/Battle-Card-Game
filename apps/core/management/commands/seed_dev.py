"""Dados de TESTE (O§2.5): 3 contas, 9 decks de 40 cartas aleatórias (máx. 3 iguais por deck),
3 Grimoriums vazios (D-03). Sem Foil/Shiny. NÃO use em produção.

Contas: TesteA e TesteB (jogadores) e TesteC (ADMIN, para acessar o painel).
Senha: variável SEED_TEST_PASSWORD do .env."""
import random

import environ
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import AccCode, Conta
from apps.cards.models import Carta
from apps.decks.services import create_starter_setup

ACCOUNTS = [("TesteA", "testea@example.test", AccCode.GREEN),
            ("TesteB", "testeb@example.test", AccCode.GREEN),
            ("TesteC", "testec@example.test", AccCode.ADMIN)]


class Command(BaseCommand):
    help = "Cria as contas/decks de teste (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=None, help="semente do sorteio (reprodutível)")

    def handle(self, *args, **opts):
        password = environ.Env()("SEED_TEST_PASSWORD", default="")
        if not password:
            raise CommandError("Defina SEED_TEST_PASSWORD no .env.")
        call_command("bootstrap")
        if not Carta.objects.exists():
            raise CommandError("Catálogo vazio: rode seed_cards.")
        rng = random.Random(opts["seed"]) if opts["seed"] is not None else random.SystemRandom()
        for name, email, code in ACCOUNTS:
            if Conta.objects.filter(name__iexact=name).exists():
                self.stdout.write(f"{name} já existe (ignorada).")
                continue
            conta = Conta.objects.create_conta(name, email, password, acc_code=code)
            create_starter_setup(conta, rng=rng, deck_count=3)
            self.stdout.write(self.style.SUCCESS(f"{name} ({code}) criada com 3 decks de 40 cartas."))
