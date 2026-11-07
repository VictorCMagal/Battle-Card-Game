"""Carrega as 100 cartas iniciais (seeds/cards.json) no banco. Idempotente."""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.cards import schema, services


class Command(BaseCommand):
    help = "Importa seeds/cards.json (ou o arquivo informado) para o catálogo de cartas."

    def add_arguments(self, parser):
        parser.add_argument("--file", default=str(Path(settings.BASE_DIR) / "seeds" / "cards.json"))

    def handle(self, *args, **opts):
        with open(opts["file"], encoding="utf-8") as f:
            cards = schema.parse_json(f.read())
        report = services.import_cards(cards)
        self.stdout.write(self.style.SUCCESS(
            f"Cartas: {report['created']} criadas, {report['updated']} atualizadas, "
            f"{len(report['errors'])} com erro."))
