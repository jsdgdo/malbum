from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

class Foto(models.Model):
  titulo = models.CharField(max_length=255, verbose_name="Título")
  imagen = models.ImageField(upload_to='fotos/', verbose_name="Imagen")
  descripcion = models.TextField(blank=True, verbose_name="Descripción")
  fecha_subida = models.DateTimeField(default=timezone.now, verbose_name="Fecha de subida")

  camara = models.CharField(max_length=100, blank=True, verbose_name="Cámara")
  lente = models.CharField(max_length=100, blank=True, verbose_name="Lente")
  configuracion = models.CharField(max_length=255, blank=True, verbose_name="Configuración")

  usuario = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="fotos", verbose_name="Usuario")

  def __str__(self):
    return self.titulo