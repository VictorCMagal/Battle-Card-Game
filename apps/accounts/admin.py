from django.contrib import admin

from .models import Conta


@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    """Visualização administrativa. Nunca exibe hash/PIN; senhas mudam pelo painel."""
    list_display = ("name", "email", "acc_code", "cur_battlepoints", "victory_counts", "last_login")
    list_filter = ("acc_code", "premium_check")
    search_fields = ("name", "email")
    exclude = ("password", "acc_pin", "last_session_key")
    readonly_fields = ("codigo_id", "last_login")
