from django.urls import path
from django.contrib.auth import views as auth_views
from .views import registrarUsuario
from . import views

urlpatterns = [
    path('registrar/', registrarUsuario, name="registrarUsuario"),
    path('iniciar-sesion/', auth_views.LoginView.as_view(template_name='usuario/iniciar-sesion.html'), name='iniciarSesion'),
    path('cerrar-sesion/', auth_views.LogoutView.as_view(next_page='inicio'), name='cerrarSesion'),
    path('<str:username>/', views.perfil_usuario, name='perfil_usuario'),
    path('recuperar-contrasena/', auth_views.PasswordResetView.as_view(template_name='usuario/recuperar-contrasena.html'), name='password_reset'),
    path('recuperar-contrasena/hecho/', auth_views.PasswordResetDoneView.as_view(template_name='usuario/recuperar-contrasena-hecho.html'), name='password_reset_done'),
    path('recuperar-contrasena-confirmar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='usuario/recuperar-contrasena-confirmar.html'), name='password_reset_confirm'),
    path('recuperar-contrasena-completo/', auth_views.PasswordResetCompleteView.as_view(template_name='usuario/recuperar-contrasena-completo.html'), name='password_reset_complete'),
    path("actor/<str:username>/", views.activitypub_actor, name="activitypub_actor"),
    path("inbox/<str:username>/", views.activitypub_inbox, name="activitypub_inbox"),
    path("outbox/<str:username>/", views.activitypub_outbox, name="activitypub_outbox"),
]