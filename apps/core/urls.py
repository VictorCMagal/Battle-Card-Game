from django.urls import path

from . import views

urlpatterns = [
    path("", views.page("index.html"), name="index"),
    path("criar_conta/", views.page("criar_conta.html"), name="criar_conta"),
    path("login/", views.page("login.html"), name="login"),
    path("servidores/", views.page("servidores.html", True), name="servidores"),
    path("lobby/", views.page("lobby.html", True), name="lobby"),
    path("sala/", views.page("sala.html", True), name="sala"),
    path("decks/", views.page("decks.html", True), name="decks"),
    path("api/status/", views.status, name="api_status"),
    path("api/servidores/", views.servidores, name="api_servidores"),
    path("api/i18n/", views.i18n, name="api_i18n"),
]
