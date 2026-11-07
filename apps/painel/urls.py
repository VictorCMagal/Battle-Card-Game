from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="painel"),
    path("contas/", views.contas, name="painel_contas"),
    path("contas/<int:conta_id>/", views.conta_edit, name="painel_conta_edit"),
    path("cartas/", views.cartas, name="painel_cartas"),
    path("cartas/nova/", views.carta_edit, name="painel_carta_new"),
    path("cartas/importar/", views.cartas_import, name="painel_cartas_import"),
    path("cartas/exportar/", views.cartas_export, name="painel_cartas_export"),
    path("cartas/<int:card_id>/", views.carta_edit, name="painel_carta_edit"),
    path("cartas/<int:card_id>/remover/", views.carta_delete, name="painel_carta_delete"),
    path("decks/", views.decks, name="painel_decks"),
    path("decks/<int:deck_id>/", views.deck_detail, name="painel_deck"),
    path("grimorium/<int:grim_id>/", views.grimorium_detail, name="painel_grimorium"),
    path("historico/", views.historico, name="painel_historico"),
    path("historico/<int:partida_id>/", views.historico_detail, name="painel_historico_detail"),
    path("config/", views.config, name="painel_config"),
]
