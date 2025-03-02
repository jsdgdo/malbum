from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from PIL import Image, ExifTags
from .utils import get_sized_image_url

class Foto(models.Model):
  titulo = models.CharField(max_length=255, verbose_name="Título")
  imagen = models.ImageField(upload_to='fotos/', verbose_name="Imagen")
  descripcion = models.TextField(blank=True, verbose_name="Descripción", help_text="Descripción de la imagen")
  fecha_subida = models.DateTimeField(default=timezone.now, verbose_name="Fecha de subida")
  alt_descripcion = models.CharField(max_length=255, blank=True, verbose_name="Descripción alternativa", help_text="Descripción alternativa para lectores de pantalla")
  licencia = models.CharField(max_length=255, blank=True, verbose_name="Licencia", help_text="Detalles sobre la licencia de imagen (ej. Creative Commons, Copyright, etc.)")
  advertencia_contenido = models.BooleanField(default=False, verbose_name="Advertencia de contenido", help_text="Indica si esta imagen debe mostrarse con una advertencia de contenido.")

  camara = models.CharField(max_length=100, blank=True, verbose_name="Cámara")
  lente = models.CharField(max_length=100, blank=True, verbose_name="Lente")
  configuracion = models.CharField(max_length=255, blank=True, verbose_name="Configuración")

  usuario = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="fotos", verbose_name="Usuario")
  etiquetas = models.ManyToManyField('Etiqueta', blank=True, related_name="fotos", verbose_name="Etiquetas")
  colecciones = models.ManyToManyField('Coleccion', blank=True, related_name="fotos", verbose_name="Colecciones")

  def get_thumbnail_url(self):
    return get_sized_image_url(self.imagen, 'thumbnail')
    
  def get_medium_url(self):
    return get_sized_image_url(self.imagen, 'medium')
    
  def get_original_url(self):
    return get_sized_image_url(self.imagen, 'original')

  def save(self, *args, **kwargs):
    super(Foto, self).save(*args, **kwargs)
    self.extract_exif_data()
    if self._state.adding is False:
      super(Foto, self).save(update_fields=['camara', 'lente', 'configuracion'])
    # Generate resized versions after saving
    if self.imagen:
      from .utils import ensure_image_sizes
      ensure_image_sizes(self.imagen.path)
  
  def extract_exif_data(self):
    try:
      image = Image.open(self.imagen.path)
      exif_data = image._getexif()

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

class Etiqueta(models.Model):
  nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")

  def __str__(self):
    return self.nombre

class Coleccion(models.Model):
  titulo=models.CharField(max_length=255, verbose_name="Titulo")
  descripcion=models.TextField(blank=True, verbose_name="Descripcion")
  usuario=models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="colecciones", verbose_name="Usuario")
  fecha_creacion=models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")

  def __str__(self):
    return self.titulo

class SolicitudImagen(models.Model):
    foto = models.ForeignKey(Foto, on_delete=models.CASCADE, related_name='solicitudes')
    email_solicitante = models.EmailField(verbose_name="Email del solicitante")
    mensaje = models.TextField(verbose_name="Mensaje")
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('aprobada', 'Aprobada'),
            ('rechazada', 'Rechazada')
        ],
        default='pendiente'
    )
    url_descarga = models.CharField(max_length=255, blank=True, null=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Solicitud de imagen"
        verbose_name_plural = "Solicitudes de imágenes"
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"Solicitud de {self.email_solicitante} para {self.foto.titulo}"

class Configuracion(models.Model):
    clave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración"
        verbose_name_plural = "Configuraciones"

    def __str__(self):
        return self.clave

    @classmethod
    def get_valor(cls, clave, default=None):
        try:
            return cls.objects.get(clave=clave).valor
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_valor(cls, clave, valor):
        obj, created = cls.objects.update_or_create(
            clave=clave,
            defaults={'valor': valor}
        )
        return obj