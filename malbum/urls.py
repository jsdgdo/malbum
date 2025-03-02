"""
URL configuration for malbum project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from . import views
from django.urls import path, include
from .views import subir_foto
from django.conf import settings
from django.conf.urls.static import static
from .feeds import FotoFeed
from .views import control
from .views import importar_datos
from usuario import activitypub

urlpatterns = [
    path('', views.inicio, name="inicio"),
    path('admin/', admin.site.urls),
    path('usuario/', include('usuario.urls')),
    path('subir-foto/', subir_foto, name='subir_foto'),
    path('agregar-etiqueta', views.agregar_etiqueta, name='agregar_etiqueta'),
    path('agregar-coleccion', views.agregar_coleccion, name='agregar_coleccion'),
    path('tablon/', views.tablon, name='tablon'),
    path('splash/', views.splash, name='splash'),
    path('foto/<int:id>/', views.detalle_foto, name='detalle_foto'),
    path('foto/<int:id>/editar/', views.editar_foto, name='editar_foto'),
    path('foto/<int:id>/borrar/', views.borrar_foto, name='borrar_foto'),
    path("rss/", FotoFeed(), name="rss_feed"),
    path('control/', control, name='control'),
    path('importar-datos/', importar_datos, name='importar_datos'),
    path('foto/<int:foto_id>/solicitar/', views.solicitar_imagen, name='solicitar_imagen'),
    path('solicitudes/', views.gestionar_solicitudes, name='gestionar_solicitudes'),
    path('solicitud/<int:solicitud_id>/responder/', views.responder_solicitud, name='responder_solicitud'),
    path('descargar/<str:token>/', views.descargar_imagen, name='descargar_imagen'),
    path('colecciones/', views.gestionar_colecciones, name='gestionar_colecciones'),
    path('colecciones/buscar-fotos/', views.buscar_fotos, name='buscar_fotos'),
    path('colecciones/agregar-foto/', views.agregar_foto_coleccion, name='agregar_foto_coleccion'),
    path('colecciones/quitar-foto/', views.quitar_foto_coleccion, name='quitar_foto_coleccion'),
    path("ap/<str:username>/", activitypub.actor_info, name="activitypub_actor"),
    path("ap/foto/<int:foto_id>/", activitypub.foto_info, name="activitypub_foto"),
    path("ap/<str:username>/inbox", activitypub.inbox, name="activitypub_inbox"),
    path("ap/<str:username>/outbox", activitypub.outbox, name="activitypub_outbox"),
    path("ap/<str:username>/followers", activitypub.followers, name="activitypub_followers"),
    path("ap/<str:username>/following", activitypub.following, name="activitypub_following"),
    path('.well-known/webfinger', activitypub.webfinger, name='webfinger'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)