from django.urls import path
from .views import registrarUsuario

urlpatterns = [
    path('registrar/', registrarUsuario, name="registrarUsuario"),
]