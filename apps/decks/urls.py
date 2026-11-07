from django.urls import path

from . import views

urlpatterns = [
    path("api/decks/", views.decks, name="api_decks"),
    path("api/decks/mover/", views.move, name="api_decks_move"),
    path("api/decks/selecionar/", views.select, name="api_decks_select"),
    path("api/decks/<int:deck_id>/", views.deck_detail, name="api_deck_detail"),
]
