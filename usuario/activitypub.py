from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from .models import Usuario, Follow
from malbum.models import Foto
from malbum.config import get_valor
import json
from datetime import datetime
from django.core.paginator import Paginator
import requests
from django.views.decorators.csrf import csrf_exempt

def get_actor_url(username):
    domain = get_valor('dominio')
    return f"https://{domain}/ap/{username}"

def get_foto_url(foto_id):
    domain = get_valor('dominio')
    return f"https://{domain}/ap/foto/{foto_id}"

def actor_info(request, username):
    usuario = get_object_or_404(Usuario, username=username)
    actor_url = get_actor_url(username)
    
    response = JsonResponse({
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
    
    # Set required headers
    response["Content-Type"] = "application/activity+json"
    response["Access-Control-Allow-Origin"] = "*"
    
    return response

def foto_info(request, foto_id):
    foto = get_object_or_404(Foto, id=foto_id)
    foto_url = get_foto_url(foto_id)
    
    response = JsonResponse({
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
    
    # Set required headers
    response["Content-Type"] = "application/activity+json"
    response["Access-Control-Allow-Origin"] = "*"
    
    return response

def webfinger(request):
    resource = request.GET.get('resource', '')
    if not resource.startswith('acct:'):
        return HttpResponse(status=400)
    
    username = resource.split('@')[0][5:]
    domain = get_valor('dominio')
    
    usuario = get_object_or_404(Usuario, username=username)
    actor_url = get_actor_url(username)
    
    response = JsonResponse({
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
    
    # Set required headers
    response["Content-Type"] = "application/jrd+json"
    response["Access-Control-Allow-Origin"] = "*"
    
    return response

@csrf_exempt
def inbox(request, username):
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    usuario = get_object_or_404(Usuario, username=username)
    activity = json.loads(request.body)
    
    # Handle Follow activity
    if activity['type'] == 'Follow':
        # Create the follow relationship
        follower_url = activity['actor']
        Follow.objects.get_or_create(
            follower=usuario,
            following=usuario,
            actor_url=follower_url
        )
        
        # Create Accept activity
        accept_activity = {
            "@context": "https://www.w3.org/ns/activitystreams",
            "id": f"{get_actor_url(username)}#accept-{activity['id'].split('/')[-1]}",
            "type": "Accept",
            "actor": get_actor_url(username),
            "object": activity,
            "to": [follower_url]
        }
        
        # Send Accept activity to follower's inbox
        follower_inbox = None
        try:
            # Fetch follower's actor info to get their inbox
            headers = {'Accept': 'application/activity+json'}
            r = requests.get(follower_url, headers=headers)
            if r.status_code == 200:
                follower_info = r.json()
                follower_inbox = follower_info.get('inbox')
                
                if follower_inbox:
                    # Send Accept activity
                    headers = {
                        'Content-Type': 'application/activity+json',
                        'Accept': 'application/activity+json'
                    }
                    r = requests.post(follower_inbox, 
                                    json=accept_activity,
                                    headers=headers)
                    if r.status_code not in [200, 202]:
                        print(f"Error sending Accept: {r.status_code}")
                
        except Exception as e:
            print(f"Error processing follow: {e}")
    
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
        attachment = {
            "type": "Document",
            "mediaType": "image/jpeg",
            "url": request.build_absolute_uri(foto.get_original_url()),
            "name": foto.titulo
        }
        
        items.append({
            "id": f"{foto_url}#create",
            "type": "Create",
            "actor": actor_url,
            "published": foto.fecha_subida.isoformat(),
            "to": ["https://www.w3.org/ns/activitystreams#Public"],
            "cc": [f"{actor_url}/followers"],
            "object": {
                "id": foto_url,
                "type": "Note",
                "published": foto.fecha_subida.isoformat(),
                "attributedTo": actor_url,
                "content": foto.descripcion,
                "attachment": [attachment],
                "to": ["https://www.w3.org/ns/activitystreams#Public"],
                "cc": [f"{actor_url}/followers"]
            }
        })
    
    response = JsonResponse({
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            "https://w3id.org/security/v1"
        ],
        "type": "OrderedCollection",
        "totalItems": fotos.count(),
        "first": f"{actor_url}/outbox?page=1",
        "last": f"{actor_url}/outbox?page={paginator.num_pages}",
        "current": f"{actor_url}/outbox?page={page_number}",
        "orderedItems": items
    })
    
    # Set required headers
    response["Content-Type"] = "application/activity+json"
    response["Access-Control-Allow-Origin"] = "*"
    
    return response

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