from django.contrib import admin

from .models import Carta, CartaElemento, CartaManaGain, CartaSkill, Combinacao


class _Inline:
    extra = 0


class ElementoInline(_Inline, admin.TabularInline):
    model = CartaElemento


class ManaGainInline(_Inline, admin.TabularInline):
    model = CartaManaGain


class SkillInline(_Inline, admin.TabularInline):
    model = CartaSkill


@admin.register(Carta)
class CartaAdmin(admin.ModelAdmin):
    list_display = ("card_id", "name", "type", "power", "mana_cost")
    inlines = [ElementoInline, ManaGainInline, SkillInline]


admin.site.register(Combinacao)
