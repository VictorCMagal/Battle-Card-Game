from django.urls import path

from . import views

urlpatterns = [path("api/cartas/", views.catalog, name="api_cartas")]
