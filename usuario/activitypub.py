from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from .models import Usuario
from malbum.models import Foto
from malbum.config import get_valor
import json
from datetime import datetime
from django.core.paginator import Paginator

def get_actor_url(username):
    domain = get_valor('dominio')
    return f"https://{domain}/ap/{username}"

def get_foto_url(foto_id):
    domain = get_valor('dominio')
    return f"https://{domain}/ap/foto/{foto_id}"

def actor_info(request, username):
    usuario = get_object_or_404(Usuario, username=username)
    actor_url = get_actor_url(username)
    
    return JsonResponse({
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "Person",
        "id": actor_url,
        "following": f"{actor_url}/following",
        "followers": f"{actor_url}/followers",
        "inbox": f"{actor_url}/inbox",
        "outbox": f"{actor_url}/outbox",
        "preferredUsername": usuario.username,
        "name": usuario.nombreCompleto or usuario.username,
        "summary": usuario.bio or "",
        "publicKey": {
            "id": f"{actor_url}#main-key",
            "owner": actor_url,
            "publicKeyPem": get_valor('clave_activitypub', '')
        }
    })

def foto_info(request, foto_id):
    foto = get_object_or_404(Foto, id=foto_id)
    foto_url = get_foto_url(foto_id)
    
    return JsonResponse({
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "Image",
        "id": foto_url,
        "attributedTo": get_actor_url(foto.usuario.username),
        "name": foto.titulo,
        "content": foto.descripcion,
        "url": [
            {
                "type": "Link",
                "href": request.build_absolute_uri(foto.get_original_url()),
                "mediaType": "image/jpeg"
            }
        ],
        "published": foto.fecha_subida.isoformat(),
        "to": ["https://www.w3.org/ns/activitystreams#Public"]
    })

def webfinger(request):
    resource = request.GET.get('resource', '')
    if not resource.startswith('acct:'):
        return HttpResponse(status=400)
    
    username = resource.split('@')[0][5:]
    domain = get_valor('dominio')
    
    usuario = get_object_or_404(Usuario, username=username)
    actor_url = get_actor_url(username)
    
    return JsonResponse({
        "subject": f"acct:{username}@{domain}",
        "links": [
            {
                "rel": "self",
                "type": "application/activity+json",
                "href": actor_url
            },
            {
                "rel": "http://webfinger.net/rel/profile-page",
                "type": "text/html",
                "href": f"https://{domain}/@{username}"
            },
            {
                "rel": "self",
                "type": "application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\"",
                "href": actor_url
            }
        ]
    })

def inbox(request, username):
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    usuario = get_object_or_404(Usuario, username=username)
    activity = json.loads(request.body)
    
    # Handle Follow activity
    if activity['type'] == 'Follow':
        # Here you would verify the signature and handle the follow request
        # For testing, we'll just accept all follows
        accept_activity = {
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Accept",
            "to": [activity['actor']],
            "actor": get_actor_url(username),
            "object": activity
        }
        # Here you would send the Accept activity to the follower's inbox
        
    return HttpResponse(status=202)

def outbox(request, username):
    if request.method != 'GET':
        return HttpResponse(status=405)
    
    usuario = get_object_or_404(Usuario, username=username)
    actor_url = get_actor_url(username)
    
    # Get all photos by this user
    fotos = Foto.objects.filter(usuario=usuario).order_by('-fecha_subida')
    
    # Paginate results
    page_size = 20
    paginator = Paginator(fotos, page_size)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    
    # Convert photos to Create activities
    items = []
    for foto in page:
        foto_url = get_foto_url(foto.id)
        items.append({
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Create",
            "actor": actor_url,
            "published": foto.fecha_subida.isoformat(),
            "to": ["https://www.w3.org/ns/activitystreams#Public"],
            "object": {
                "type": "Image",
                "id": foto_url,
                "attributedTo": actor_url,
                "name": foto.titulo,
                "content": foto.descripcion,
                "url": [
                    {
                        "type": "Link",
                        "href": request.build_absolute_uri(foto.get_original_url()),
                        "mediaType": "image/jpeg"
                    }
                ],
                "published": foto.fecha_subida.isoformat(),
                "to": ["https://www.w3.org/ns/activitystreams#Public"]
            }
        })
    
    return JsonResponse({
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "OrderedCollection",
        "totalItems": fotos.count(),
        "first": f"{actor_url}/outbox?page=1",
        "last": f"{actor_url}/outbox?page={paginator.num_pages}",
        "current": f"{actor_url}/outbox?page={page_number}",
        "orderedItems": items
    })

def followers(request, username):
    if request.method != 'GET':
        return HttpResponse(status=405)
    
    usuario = get_object_or_404(Usuario, username=username)
    actor_url = get_actor_url(username)
    
    # Get all followers
    # Note: You'll need to implement a Follower model and relationship
    followers = usuario.followers.all().order_by('-created_at')
    
    # Paginate results
    page_size = 20
    paginator = Paginator(followers, page_size)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    
    items = [follower.actor_url for follower in page]
    
    return JsonResponse({
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "OrderedCollection",
        "totalItems": followers.count(),
        "first": f"{actor_url}/followers?page=1",
        "last": f"{actor_url}/followers?page={paginator.num_pages}",
        "current": f"{actor_url}/followers?page={page_number}",
        "orderedItems": items
    })

def following(request, username):
    if request.method != 'GET':
        return HttpResponse(status=405)
    
    usuario = get_object_or_404(Usuario, username=username)
    actor_url = get_actor_url(username)
    
    # Get all accounts this user follows
    following = usuario.following.all().order_by('-created_at')
    
    # Paginate results
    page_size = 20
    paginator = Paginator(following, page_size)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    
    items = [follow.actor_url for follow in page]
    
    return JsonResponse({
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "OrderedCollection",
        "totalItems": following.count(),
        "first": f"{actor_url}/following?page=1",
        "last": f"{actor_url}/following?page={paginator.num_pages}",
        "current": f"{actor_url}/following?page={page_number}",
        "orderedItems": items
    }) 