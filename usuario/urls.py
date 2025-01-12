from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('registrarse/', views.registrarUsuario, name='registrarUsuario'),
    path('iniciar-sesion/', auth_views.LoginView.as_view(template_name='usuario/login.html'), name='iniciarSesion'),
    path('cerrar-sesion/', auth_views.LogoutView.as_view(next_page='inicio'), name='cerrarSesion'),
    path('recuperar-contrasena/', auth_views.PasswordResetView.as_view(template_name='usuario/recuperar-contrasena.html'), name='password_reset'),
    path('recuperar-contrasena/enviado/', auth_views.PasswordResetDoneView.as_view(template_name='usuario/recuperar-contrasena-enviado.html'), name='password_reset_done'),
    path('recuperar-contrasena/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='usuario/recuperar-contrasena-form.html'), name='password_reset_confirm'),
    path('recuperar-contrasena-completo/', auth_views.PasswordResetCompleteView.as_view(template_name='usuario/recuperar-contrasena-completo.html'), name='password_reset_complete'),
    path('seguir/', views.follow, name='follow'),
    path('dejar-de-seguir/', views.unfollow, name='unfollow'),
    path('buscar/', views.buscar_usuarios, name='buscar_usuarios'),
    path('<str:username>/', views.perfil_usuario, name='perfil_usuario'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)