"""Inicializa dados essenciais: servidor padrão e catálogo de 100 cartas. Idempotente."""
from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.cards.models import Carta
from apps.core.models import Servidor


class Command(BaseCommand):
    help = "Cria o 'Servidor 1' (se não houver) e carrega as cartas iniciais (se o catálogo estiver vazio)."

    def handle(self, *args, **opts):
        if not Servidor.objects.exists():
            Servidor.objects.create(name="Servidor 1")
            self.stdout.write("Servidor 1 criado.")
        if not Carta.objects.exists():
            call_command("seed_cards")
        else:
            self.stdout.write(f"Catálogo já possui {Carta.objects.count()} cartas (use seed_cards para recarregar).")
