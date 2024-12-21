from PIL import Image
import os
from django.conf import settings
from pathlib import Path

def get_image_paths(image_path):
    """Generate paths for different image sizes"""
    base_path = Path(image_path)
    directory = base_path.parent
    filename = base_path.stem
    extension = base_path.suffix

    thumbnail_path = directory / f"{filename}_thumb{extension}"
    medium_path = directory / f"{filename}_medium{extension}"
    
    return {
        'original': image_path,
        'thumbnail': str(thumbnail_path),  # For tablon/profile (300x300)
        'medium': str(medium_path),        # For detalle (800x800)
    }

def ensure_image_sizes(image_path):
    """Create resized versions if they don't exist"""
    if not os.path.exists(image_path):
        return None
        
    paths = get_image_paths(image_path)
    sizes = {
        'thumbnail': (375, 375),  # 300 * 1.25 = 375
        'medium': (1000, 1000)    # 800 * 1.25 = 1000
    }
    
    try:
        with Image.open(image_path) as img:
            for size_name, size in sizes.items():
                output_path = paths[size_name]
                
                if not os.path.exists(output_path):
                    # Create a copy for resizing
                    resized_img = img.copy()
                    resized_img.thumbnail(size, Image.Resampling.LANCZOS)
                    resized_img.save(output_path, quality=85, optimize=True)
                    
        return paths
    except Exception as e:
        print(f"Error procesando imagen {image_path}: {e}")
        return None

def get_sized_image_url(image_field, size='original'):
    """Get the URL for a specific image size"""
    if not image_field:
        return None
        
    original_path = image_field.path
    paths = get_image_paths(original_path)
    
    # Ensure resized versions exist
    ensure_image_sizes(original_path)
    
    # Convert file system path to URL
    relative_path = Path(paths[size]).relative_to(settings.MEDIA_ROOT)
    return f"{settings.MEDIA_URL}{relative_path}" 