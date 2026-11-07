from django.urls import path

from . import views

urlpatterns = [path("api/salas/", views.rooms, name="api_salas")]
