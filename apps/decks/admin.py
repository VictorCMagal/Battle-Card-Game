from django.contrib import admin

from .models import Deck, DeckCarta, Grimorium, GrimoriumCarta

admin.site.register(Deck)
admin.site.register(DeckCarta)
admin.site.register(Grimorium)
admin.site.register(GrimoriumCarta)
