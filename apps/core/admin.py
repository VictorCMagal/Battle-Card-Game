from django.contrib import admin

from .models import ConfigServidor, Servidor

admin.site.register(Servidor)
admin.site.register(ConfigServidor)
