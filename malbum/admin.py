from django.contrib import admin
from .models import Foto, Etiqueta, Coleccion

@admin.register(Foto)
class FotoAdmin(admin.ModelAdmin):
  list_display = ('titulo', 'usuario', 'fecha_subida', 'licencia', 'advertencia_contenido')
  search_fields = ('titulo', 'usuario__username', 'descripcion', 'alt_descripcion', 'licencia')
  list_filter = ['fecha_subida', 'usuario', 'advertencia_contenido']
  filter_horizontal = ['etiquetas', 'colecciones']

  fieldsets = (
    (None, {
      'fields': ('titulo', 'imagen', 'descripcion', 'alt_descripcion', 'usuario')
    }),
    ('Metadata', {
      'fields':('camara', 'lente', 'configuracion', 'fecha_subida')
    }),
    ('Licencia y Advertencia', {
      'fields':('licencia', 'advertencia_contenido')
    }),
    ('Etiquetas y colecciones', {
      'fields':('etiquetas', 'colecciones')
    })
  )

@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    search_fields=['nombre']

@admin.register(Coleccion)
class ColeccionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'usuario', 'fecha_creacion')
    search_fields = ['titulo', 'descripcion', 'usuario__username']
    list_filter = ['fecha_creacion']