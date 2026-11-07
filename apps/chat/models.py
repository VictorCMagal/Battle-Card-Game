"""Mensagens de chat persistidas (lobby, sala e privado). Retenção configurável."""
from django.conf import settings
from django.db import models


class ChatMensagem(models.Model):
    canal = models.CharField(max_length=40, db_index=True)   # lobby:1, sala:12, priv:3-7
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    sender_name = models.CharField(max_length=16)
    texto = models.CharField(max_length=126)
    criado_em = models.DateTimeField(auto_now_add=True)
    moderado = models.BooleanField(default=False)   # gancho para moderação futura (P§20)

    class Meta:
        db_table = "Chat_Mensagem"
        ordering = ["id"]
