from django import forms
from .models import Foto

class FotoForm(forms.ModelForm):
  class Meta:
    model = Foto
    fields = {'titulo', 'imagen', 'descripcion'}
    labels = {
      'titulo': 'Título',
      'imagen': 'Imagen',
      'descripcion': 'Descripción',
      'alt_descripcion': 'Descripción alternativa',
      'licencia': 'Licencia',
      'advertencia_contenido': 'Advertencia de contenido'
    }
