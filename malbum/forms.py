from django import forms
from .models import Foto, Etiqueta, Coleccion

class FotoForm(forms.ModelForm):
  class Meta:
    model = Foto
    fields = ['titulo', 'imagen', 'descripcion', 'alt_descripcion', 'licencia', 'advertencia_contenido', 'etiquetas', 'colecciones']
    labels = {
      'titulo': 'Título',
      'imagen': 'Imagen',
      'descripcion': 'Descripción',
      'alt_descripcion': 'Descripción alternativa',
      'licencia': 'Licencia',
      'advertencia_contenido': 'Advertencia de contenido',
      'etiquetas': 'Etiquetas',
      'colecciones': 'Colecciones'
    }

class EtiquetaForm(forms.ModelForm):
  class Meta:
    model = Etiqueta
    fields = ['nombre']
    labels = {'nombre': 'Nombre de la etiqueta'}

class ColeccionForm(forms.ModelForm):
  class Meta:
    model = Coleccion
    fields = ['titulo', 'descripcion']
    labels = {
      'titulo': 'Título de la colección',
      'descripcion': 'Descripción'
    }