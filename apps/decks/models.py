"""Decks e Grimorium (O§2.2/O§2.3). Cada cópia de carta é uma linha com identidade própria
(`card_uid`), pois Foil/Shiny valem por cópia e Card_ID se repete (até 3x por deck)."""
import uuid

from django.conf import settings
from django.db import models


class Deck(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="decks")
    slot = models.PositiveSmallIntegerField()  # 1..6 (4..6 exigem premium_check)
    name = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Deck"
        unique_together = [("owner", "slot")]

    def __str__(self):
        return f"{self.owner_id}/{self.slot} {self.name}"


class DeckCarta(models.Model):
    card_uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="cards")
    carta = models.ForeignKey("cards.Carta", on_delete=models.PROTECT, related_name="+")
    is_foil = models.BooleanField(default=False)
    is_shiny = models.BooleanField(default=False)

    class Meta:
        db_table = "Deck_Carta"
        indexes = [models.Index(fields=["deck", "carta"])]


class Grimorium(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="grimoriums")

    class Meta:
        db_table = "Grimorium"


class GrimoriumCarta(models.Model):
    card_uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    grimorium = models.ForeignKey(Grimorium, on_delete=models.CASCADE, related_name="cards")
    carta = models.ForeignKey("cards.Carta", on_delete=models.PROTECT, related_name="+")
    is_foil = models.BooleanField(default=False)
    is_shiny = models.BooleanField(default=False)

    class Meta:
        db_table = "Grimorium_Carta"
