"""Roteamento HTTP principal."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("django-admin/", admin.site.urls),   # Django Admin complementar (somente ADMIN/DEV)
    path("painel/", include("apps.painel.urls")),
    path("", include("apps.accounts.urls")),
    path("", include("apps.decks.urls")),
    path("", include("apps.cards.urls")),
    path("", include("apps.game.urls")),
    path("", include("apps.core.urls")),
]
