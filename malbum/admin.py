from django.contrib import admin
from .models import Foto

@admin.register(Foto)
class FotoAdmin(admin.ModelAdmin):
  list_display = ('titulo', 'usuario', 'fecha_subida')
  search_fields = ('titulo', 'usuario__username')
  list_filter = ('fecha_subida', 'usuario')

  fieldsets = (
    (None, {
      'fields': ('titulo', 'imagen', 'descripcion', 'usuario')
    }),
    ('Metadata', {
      'fields':('camara', 'lente', 'configuracion', 'fecha_subida')
    }),
  )