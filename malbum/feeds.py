from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.conf import settings
import os
from .models import Foto

class FotoFeed(Feed):
    title = "Malbum - Fotos"
    link = "/tablon/"
    description = "Últimas fotos subidas a Malbum"

    def items(self):
        return Foto.objects.order_by('-fecha_subida')[:10]  # Customize the number of items

    def item_title(self, item):
        return item.titulo

    def item_description(self, item):
      description = f'<img src="{settings.SITE_URL}{item.imagen.url}" alt="{item.alt_descripcion or "Imagen"}" style="max-width:100%;">'
      description += f"""
      <p><strong>Descripción:</strong> {item.descripcion or 'Sin descripción'}</p>
      <p><strong>Licencia:</strong> {item.licencia or 'Sin licencia especificada'}</p>
      """
      if item.advertencia_contenido:
          description += '<p><strong>Advertencia de contenido:</strong> Esta imagen puede contener contenido sensible.</p>'

      description += '<p><strong>Datos de captura</strong></p>'
      if item.camara:
          description += f'<li><strong>Cámara:</strong> {item.camara}</li>'
      else:
          description += '<li><strong>Cámara:</strong> No especificada</li>'
      
      if item.lente:
          description += f'<li><strong>Lente:</strong> {item.lente}</li>'
      else:
          description += '<li><strong>Lente:</strong> No especificada</li>'
      
      if item.configuracion:
          description += f'<li><strong>Configuración:</strong> {item.configuracion}</li>'
      else:
          description += '<li><strong>Configuración:</strong> No especificada</li>'
      
      description += '</ul>'

      return description

    def item_link(self, item):
        return reverse('detalle_foto', args=[item.id])  # Assuming you have a detail view for "Foto"

    def item_extra_kwargs(self, item):
        # Add additional elements like <image> for RSS
        return {
            'image': f"{item.imagen.url}"
        }

    def item_enclosure_url(self, item):
      return "http://localhost:8080"+item.imagen.url
    
    def item_enclosure_mime_type(self, item):
      return "image/jpeg"

    def item_enclosure_length(self, item):
      try:
        return os.path.getsize(item.imagen.path)
      except FileNotFoundError:
        return 0  # Fallback if the file doesn't exist