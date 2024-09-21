from django.urls import path
from django.contrib.auth import views as auth_views
from .views import registrarUsuario

urlpatterns = [
    path('registrar/', registrarUsuario, name="registrarUsuario"),
    path('iniciar-sesion/', auth_views.LoginView.as_view(template_name='usuario/iniciar-sesion.html'), name='iniciarSesion'),

]