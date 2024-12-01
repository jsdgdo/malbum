from django.urls import path
from django.contrib.auth import views as auth_views
from .views import registrarUsuario
from . import views

urlpatterns = [
    path('registrar/', registrarUsuario, name="registrarUsuario"),
    path('iniciar-sesion/', auth_views.LoginView.as_view(template_name='usuario/iniciar-sesion.html'), name='iniciarSesion'),
    path('cerrar-sesion/', auth_views.LogoutView.as_view(next_page='inicio'), name='cerrarSesion'),
    path("actor/<str:username>/", views.activitypub_actor, name="activitypub_actor"),
    path("inbox/<str:username>/", views.activitypub_inbox, name="activitypub_inbox"),
    path("outbox/<str:username>/", views.activitypub_outbox, name="activitypub_outbox"),
]