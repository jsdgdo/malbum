import json
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from usuario.models import Usuario
from .models import Foto
from django.urls import reverse
from .config import get_config

def get_actor(request, username):
    """Return ActivityPub actor object for a user"""
    user = get_object_or_404(Usuario, username=username)
    config = get_config()
    
    actor = {
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            "https://w3id.org/security/v1"
        ],
        "type": "Person",
        "id": f"https://{request.get_host()}/ap/users/{user.username}",
        "following": f"https://{request.get_host()}/ap/users/{user.username}/following",
        "followers": f"https://{request.get_host()}/ap/users/{user.username}/followers",
        "inbox": f"https://{request.get_host()}/ap/users/{user.username}/inbox",
        "outbox": f"https://{request.get_host()}/ap/users/{user.username}/outbox",
        "preferredUsername": user.username,
        "name": user.nombreCompleto,
        "summary": user.bio or "",
        "icon": {
            "type": "Image",
            "mediaType": "image/jpeg",
            "url": request.build_absolute_uri(user.get_profile_pic_url())
        } if user.fotoDePerfil else None,
        "publicKey": {
            "id": f"https://{request.get_host()}/ap/users/{user.username}#main-key",
            "owner": f"https://{request.get_host()}/ap/users/{user.username}",
            "publicKeyPem": config.get('PUBLIC_KEY', '')
        }
    }
    
    return JsonResponse(actor)

def get_outbox(request, username):
    """Return user's outbox containing their photos as Create activities"""
    user = get_object_or_404(Usuario, username=username)
    
    # Get user's photos
    photos = Foto.objects.filter(usuario=user).order_by('-fecha_subida')
    
    # Convert each photo to an ActivityPub Create activity
    items = []
    for photo in photos:
        activity = {
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Create",
            "actor": f"https://{request.get_host()}/ap/users/{user.username}",
            "object": {
                "type": "Image",
                "id": f"https://{request.get_host()}/ap/photos/{photo.id}",
                "name": photo.titulo,
                "content": photo.descripcion,
                "url": request.build_absolute_uri(photo.imagen.url),
                "attributedTo": f"https://{request.get_host()}/ap/users/{user.username}",
                "published": photo.fecha_subida.isoformat(),
                "license": photo.licencia
            }
        }
        items.append(activity)
    
    outbox = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "OrderedCollection",
        "totalItems": len(items),
        "orderedItems": items
    }
    
    return JsonResponse(outbox)

def get_photo(request, photo_id):
    """Return ActivityPub representation of a photo"""
    photo = get_object_or_404(Foto, id=photo_id)
    
    photo_obj = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "Image",
        "id": f"https://{request.get_host()}/ap/photos/{photo.id}",
        "name": photo.titulo,
        "content": photo.descripcion,
        "url": request.build_absolute_uri(photo.imagen.url),
        "attributedTo": f"https://{request.get_host()}/ap/users/{photo.usuario.username}",
        "published": photo.fecha_subida.isoformat(),
        "license": photo.licencia,
        "sensitive": photo.advertencia_contenido,
        "alt": photo.alt_descripcion,
        "tags": [tag.nombre for tag in photo.etiquetas.all()],
        "collections": [col.nombre for col in photo.colecciones.all()]
    }
    
    return JsonResponse(photo_obj)

def webfinger(request):
    """Handle Webfinger requests to find users"""
    resource = request.GET.get('resource', '')
    if not resource.startswith('acct:'):
        return HttpResponse(status=400)
    
    # Extract username from acct:username@domain
    username = resource.split(':')[1].split('@')[0]
    user = get_object_or_404(Usuario, username=username)
    
    response = {
        "subject": f"acct:{user.username}@{request.get_host()}",
        "links": [
            {
                "rel": "self",
                "type": "application/activity+json",
                "href": f"https://{request.get_host()}/ap/users/{user.username}"
            }
        ]
    }
    
    return JsonResponse(response)