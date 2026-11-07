from django.urls import path

from . import views

urlpatterns = [
    path("api/contas/", views.register, name="api_register"),
    path("api/contas/disponibilidade/", views.availability, name="api_availability"),
    path("api/login/", views.login_view, name="api_login"),
    path("api/logout/", views.logout_view, name="api_logout"),
    path("api/me/", views.me, name="api_me"),
]
