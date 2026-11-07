"""Modelos de infraestrutura: servidores de jogo e configurações editáveis pelo painel."""
from django.db import models


class Servidor(models.Model):
    """Servidor exibido na tela de seleção. O MVP entrega um único servidor ativo (D-24)."""
    name = models.CharField(max_length=32, unique=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "Servidor"

    def __str__(self):
        return self.name


class ConfigServidor(models.Model):
    """Pares chave/valor de configuração (ex.: mensagem do dia). Editável no painel."""
    key = models.CharField(max_length=64, unique=True)
    value = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "Config_Servidor"

    def __str__(self):
        return self.key
