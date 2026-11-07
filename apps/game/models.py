"""Histórico de partidas (O§2.4): cabeçalho + eventos em ordem cronológica (seq único)."""
from django.conf import settings
from django.db import models


class HistoricoPartida(models.Model):
    servidor = models.ForeignKey("core.Servidor", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    modo = models.CharField(max_length=8)                  # versus | debug
    jogador_a = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    jogador_b = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    iniciada_em = models.DateTimeField()
    finalizada_em = models.DateTimeField(null=True, blank=True)
    resultado = models.CharField(max_length=8, blank=True)  # win | draw | aborted
    vencedor = models.CharField(max_length=1, blank=True)   # A | B
    motivo = models.CharField(max_length=16, blank=True)    # life | afk | abandon | disconnect
    turnos = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "Historico_Partida"
        ordering = ["-id"]


class HistoricoEvento(models.Model):
    partida = models.ForeignKey(HistoricoPartida, on_delete=models.CASCADE, related_name="eventos")
    seq = models.PositiveIntegerField()
    turno = models.PositiveIntegerField(default=0)
    jogador = models.CharField(max_length=1, blank=True)
    tipo = models.CharField(max_length=32)
    payload = models.JSONField(default=dict)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Historico_Evento"
        ordering = ["partida_id", "seq"]
        unique_together = [("partida", "seq")]
