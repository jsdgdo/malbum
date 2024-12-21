from django.core.management.base import BaseCommand
from malbum.models import Foto
from malbum.utils import ensure_image_sizes

class Command(BaseCommand):
    help = 'Generar tamaños de imagen faltantes para fotos existentes'

    def handle(self, *args, **options):
        fotos = Foto.objects.all()
        total = fotos.count()
        
        self.stdout.write(f"Procesando {total} fotos...")
        
        for i, foto in enumerate(fotos, 1):
            if foto.imagen:
                self.stdout.write(f"Procesando {i}/{total}: {foto.titulo}")
                ensure_image_sizes(foto.imagen.path)
            
        self.stdout.write(self.style.SUCCESS('Tamaños de imagen generados exitosamente')) 