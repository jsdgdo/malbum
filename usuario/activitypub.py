from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from .models import Usuario, Follow, get_default_user
from malbum.models import Foto
from malbum.config import get_valor
import json
from datetime import datetime
from django.core.paginator import Paginator
import requests
from django.views.decorators.csrf import csrf_exempt
import base64
import hashlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from urllib.parse import urlparse
import time

def load_private_key():
    try:
        with open('/code/keys/private.pem', 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )
            return private_key
    except Exception as e:
        print(f"Error loading private key: {e}")
        return None

def sign_request(private_key, method, path, host, date, digest=None):
    signed_string = f"(request-target): {method.lower()} {path}\n"
    signed_string += f"host: {host}\n"
    signed_string += f"date: {date}"
    if digest:
        signed_string += f"\ndigest: {digest}"

    signature = private_key.sign(
        signed_string.encode('utf-8'),
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    
    key_id = f"https://{get_valor('dominio')}/ap/jose#main-key"
    
    header = f'keyId="{key_id}",algorithm="rsa-sha256",headers="(request-target) host date{" digest" if digest else ""}",signature="{signature_b64}"'
    
    return header

def send_signed_request(url, data, method='POST'):
    try:
        private_key = load_private_key()
        if not private_key:
            raise Exception("Could not load private key")

        parsed_url = urlparse(url)
        path = parsed_url.path
        if parsed_url.query:
            path = f"{path}?{parsed_url.query}"
        
        date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # Calculate digest if there's a body
        if data:
            body = json.dumps(data).encode('utf-8')
            digest = f"SHA-256={base64.b64encode(hashlib.sha256(body).digest()).decode('utf-8')}"
        else:
            body = None
            digest = None

        # Generate signature
        signature = sign_request(
            private_key,
            method,
            path,
            parsed_url.netloc,
            date,
            digest
        )

        # Prepare headers
        headers = {
            'Host': parsed_url.netloc,
            'Date': date,
            'Signature': signature,
            'Accept': 'application/activity+json',
            'Content-Type': 'application/activity+json',
        }
        if digest:
            headers['Digest'] = digest

        # Send request
        response = requests.request(
            method=method,
            url=url,
            json=data if data else None,
            headers=headers
        )
        
        return response

    except Exception as e:
        print(f"Error sending signed request: {e}")
        import traceback
        traceback.print_exc()
        return None

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
    try:
        activity = json.loads(request.body)
        print(f"Received activity: {activity}")
        
        if activity['type'] == 'Undo':
            # Handle Undo Follow
            if activity['object']['type'] == 'Follow':
                follower_url = activity['actor']
                Follow.objects.filter(
                    following=usuario,
                    actor_url=follower_url
                ).delete()
                return HttpResponse(status=200)
        
        # Handle Follow activity
        elif activity['type'] == 'Follow':
            follower_url = activity['actor']
            
            try:
                parsed_url = urlparse(follower_url)
                domain = parsed_url.netloc
                remote_username = parsed_url.path.split('/')[-1]
            except:
                domain = ''
                remote_username = ''
            
            # Create or get the system user for remote followers
            system_user = get_default_user()
            
            follow, created = Follow.objects.get_or_create(
                following=usuario,
                actor_url=follower_url,
                defaults={
                    'follower_id': system_user,  # Set the follower to system user
                    'remote_username': remote_username,
                    'remote_domain': domain
                }
            )
            
            # Create Accept activity
            accept_activity = {
                "@context": "https://www.w3.org/ns/activitystreams",
                "id": f"https://{get_valor('dominio')}/ap/{usuario.username}#accepts/follows/{follow.id}",
                "type": "Accept",
                "actor": f"https://{get_valor('dominio')}/ap/{usuario.username}",
                "object": activity
            }
            
            # Get follower's inbox
            headers = {'Accept': 'application/activity+json'}
            r = requests.get(follower_url, headers=headers)
            if r.status_code == 200:
                follower_info = r.json()
                follower_inbox = follower_info.get('inbox')
                
                if follower_inbox:
                    # Send signed Accept activity
                    r = send_signed_request(follower_inbox, accept_activity)
                    if r:
                        print(f"Accept response: {r.status_code}")
                        print(f"Accept response content: {r.content}")
                    
    except Exception as e:
        print(f"Error processing follow: {e}")
        import traceback
        traceback.print_exc()
        return HttpResponse(status=500)
    
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
    followers = Follow.objects.filter(following=usuario).order_by('-created_at')
    
    # Paginate results
    page_size = 20
    paginator = Paginator(followers, page_size)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    
    # Get follower URLs
    items = [follow.actor_url for follow in page]
    
    response = JsonResponse({
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "OrderedCollectionPage",
        "id": f"{actor_url}/followers?page={page_number}",
        "totalItems": followers.count(),
        "first": f"{actor_url}/followers?page=1",
        "last": f"{actor_url}/followers?page={paginator.num_pages}",
        "prev": f"{actor_url}/followers?page={page.previous_page_number()}" if page.has_previous() else None,
        "next": f"{actor_url}/followers?page={page.next_page_number()}" if page.has_next() else None,
        "partOf": f"{actor_url}/followers",
        "orderedItems": items
    })
    
    response["Content-Type"] = "application/activity+json"
    response["Access-Control-Allow-Origin"] = "*"
    
    return response

def following(request, username):
    if request.method != 'GET':
        return HttpResponse(status=405)
    
    usuario = get_object_or_404(Usuario, username=username)
    actor_url = get_actor_url(username)
    
    # Get all accounts this user follows through the Follow model
    following = Follow.objects.filter(follower=usuario).order_by('-created_at')
    
    # Paginate results
    page_size = 20
    paginator = Paginator(following, page_size)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    
    # Get the actor URLs from the Follow objects
    items = [follow.actor_url for follow in page]
    
    response = JsonResponse({
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "OrderedCollection",
        "totalItems": following.count(),
        "first": f"{actor_url}/following?page=1",
        "last": f"{actor_url}/following?page={paginator.num_pages}",
        "current": f"{actor_url}/following?page={page_number}",
        "orderedItems": items
    })
    
    response["Content-Type"] = "application/activity+json"
    response["Access-Control-Allow-Origin"] = "*"
    
    return response 