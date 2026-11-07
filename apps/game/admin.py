from django.contrib import admin

from .models import HistoricoEvento, HistoricoPartida

admin.site.register(HistoricoPartida)
admin.site.register(HistoricoEvento)
