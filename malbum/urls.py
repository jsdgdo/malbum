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

urlpatterns = [
    path('', views.inicio, name="inicio"),
    path('admin/', admin.site.urls),
    path('usuario/', include('usuario.urls')),
    path('ap/', include('usuario.urls')),
    path('subir-foto/', subir_foto, name='subir_foto'),
    path('agregar-etiqueta', views.agregar_etiqueta, name='agregar_etiqueta'),
    path('agregar-coleccion', views.agregar_coleccion, name='agregar_coleccion'),
    path('tablon/', views.tablon, name='tablon'),
    path('splash/', views.splash, name='splash'),
    path('foto/<int:id>/', views.detalle_foto, name='detalle_foto'),
    path('foto/<int:id>/editar/', views.editar_foto, name='editar_foto'),
    path("rss/", FotoFeed(), name="rss_feed"),
    path('control/', control, name='control'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)