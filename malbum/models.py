from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from PIL import Image, ExifTags

class Foto(models.Model):
  titulo = models.CharField(max_length=255, verbose_name="Título")
  imagen = models.ImageField(upload_to='fotos/', verbose_name="Imagen")
  descripcion = models.TextField(blank=True, verbose_name="Descripción")
  fecha_subida = models.DateTimeField(default=timezone.now, verbose_name="Fecha de subida")

  camara = models.CharField(max_length=100, blank=True, verbose_name="Cámara")
  lente = models.CharField(max_length=100, blank=True, verbose_name="Lente")
  configuracion = models.CharField(max_length=255, blank=True, verbose_name="Configuración")

  usuario = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="fotos", verbose_name="Usuario")

  def save(self, *args, **kwargs):
    super(Foto, self).save(*args, **kwargs)
    self.extract_exif_data()
    super(Foto, self).save(*args, **kwargs)
  
  def extract_exif_data(self):
    try:
      image = Image.open(self.imagen.path)
      exif_data = image._getexif()
      print(f"EXIF Data Retrieved: {exif_data}")

      if exif_data:
        exif={ExifTags.TAGS.get(tag, tag): value for tag, value in exif_data.items()}
        print(f"Formatted EXIF: {exif}")

        self.camara = exif.get("Model", "Desconocida")
        self.lente = exif.get("LensModel", "Desconocida")
        self.configuracion = f"ISO {exif.get('ISOSpeedRatings', 'Desconocido')}, {exif.get('ExposureTime', 'N/A')}s, f/{exif.get('FNumber', 'N/A')}"
    except Exception as e:
      print(f"Error extracting EXIF data: {e}")

  def __str__(self):
    return self.titulo