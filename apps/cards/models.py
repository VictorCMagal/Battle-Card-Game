"""Catálogo de cartas (O§4). Dados ficam no MySQL; nada de carta é embutido no código (P§13)."""
from django.db import models
from django.db.models import Q


class Carta(models.Model):
    """Definição de carta. Card_ID 0 é inválido (constraint)."""
    card_id = models.PositiveIntegerField(primary_key=True)
    type = models.CharField(max_length=10, default="SUMMON")
    name = models.CharField(max_length=64)
    rarity = models.CharField(max_length=16, default="common")
    power = models.SmallIntegerField(default=0)
    power_bonus = models.SmallIntegerField(default=0)
    attack_bonus = models.SmallIntegerField(default=0)
    damage = models.SmallIntegerField(default=0)
    shield = models.SmallIntegerField(default=0)
    mana_cost = models.SmallIntegerField(default=0)

    class Meta:
        db_table = "Carta"
        constraints = [models.CheckConstraint(condition=Q(card_id__gte=1), name="carta_card_id_gte_1")]
        ordering = ["card_id"]

    def __str__(self):
        return f"{self.card_id} {self.name}"


class CartaElemento(models.Model):
    carta = models.ForeignKey(Carta, on_delete=models.CASCADE, related_name="elementos")
    slot = models.PositiveSmallIntegerField()   # 1..4 (Element1..Element4)
    element = models.CharField(max_length=1)

    class Meta:
        db_table = "Carta_Elemento"
        unique_together = [("carta", "slot")]


class CartaManaGain(models.Model):
    carta = models.ForeignKey(Carta, on_delete=models.CASCADE, related_name="managains")
    slot = models.PositiveSmallIntegerField()   # 1..4
    element = models.CharField(max_length=1)
    value = models.SmallIntegerField()

    class Meta:
        db_table = "Carta_ManaGain"
        unique_together = [("carta", "slot")]


class CartaSkill(models.Model):
    carta = models.ForeignKey(Carta, on_delete=models.CASCADE, related_name="skills")
    slot = models.PositiveSmallIntegerField()   # 1..3
    name = models.CharField(max_length=32)
    number = models.CharField(max_length=16, blank=True)
    manacost = models.SmallIntegerField(default=0)
    txt_key = models.CharField(max_length=64)   # chave i18n; texto por IDIOMA nos dicionários

    class Meta:
        db_table = "Carta_Skill"
        unique_together = [("carta", "slot")]


class Combinacao(models.Model):
    """Regra de fusão/combinação (O§3.3). A tabela é entregue vazia (P§15.14)."""
    EFFECTS = [("create_card", "create_card"), ("power_delta", "power_delta"), ("shield_delta", "shield_delta")]
    nome = models.CharField(max_length=64)
    ativo = models.BooleanField(default=True)
    block_card_id = models.PositiveIntegerField(null=True, blank=True)
    block_element = models.CharField(max_length=1, blank=True)
    incoming_card_id = models.PositiveIntegerField(null=True, blank=True)
    incoming_element = models.CharField(max_length=1, blank=True)
    effect_type = models.CharField(max_length=16, choices=EFFECTS)
    effect_value = models.IntegerField()

    class Meta:
        db_table = "Combinacao"
