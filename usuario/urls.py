from django.urls import path
from django.contrib.auth import views as auth_views
from .views import registrarUsuario
from django.conf import settings
from django.conf.urls.static import static
from . import views
from . import activitypub

urlpatterns = [
    path('registrar/', registrarUsuario, name="registrarUsuario"),
    path('iniciar-sesion/', auth_views.LoginView.as_view(template_name='usuario/iniciar-sesion.html'), name='iniciarSesion'),
    path('cerrar-sesion/', auth_views.LogoutView.as_view(next_page='inicio'), name='cerrarSesion'),
    path('recuperar-contrasena/', auth_views.PasswordResetView.as_view(template_name='usuario/recuperar-contrasena.html'), name='password_reset'),
    path('recuperar-contrasena/hecho/', auth_views.PasswordResetDoneView.as_view(template_name='usuario/recuperar-contrasena-hecho.html'), name='password_reset_done'),
    path('recuperar-contrasena-confirmar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='usuario/recuperar-contrasena-confirmar.html'), name='password_reset_confirm'),
    path('recuperar-contrasena-completo/', auth_views.PasswordResetCompleteView.as_view(template_name='usuario/recuperar-contrasena-completo.html'), name='password_reset_complete'),
    path('editar/', views.editar_usuario, name='editar_usuario'),
    path('buscar/', views.buscar_usuarios, name='buscar_usuarios'),
    path('<str:username>/follow/', views.follow_user, name='follow_user'),
    path('<str:username>/unfollow/', views.unfollow_user, name='unfollow_user'),
    path('<str:username>/', views.perfil_usuario, name='perfil_usuario'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)