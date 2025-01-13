from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import RegistroUsuarioForm, EditarUsuarioForm
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Usuario, Follow, RemotePost
from malbum.models import Foto
from malbum.config import get_default_config, save_config, get_valor
from django.contrib.auth.decorators import login_required
from django.db import models
from .activitypub import search_users_remote, fetch_remote_posts
import json
from django.conf import settings
from django.db.models import Q
import requests
from django.contrib import messages


def registrarUsuario(request):
  if Usuario.objects.exists():
    return redirect('inicio')
  if request.method == "POST":
    form = RegistroUsuarioForm(request.POST, request.FILES)
    if form.is_valid():
      usuario = form.save(commit=False)
      usuario.is_staff = True
      usuario.save()
      
      # Create initial config.json
      initial_config = get_default_config()
      initial_config['dominio'] = request.get_host()  # Set default domain from request
      save_config(initial_config)
      
      login(request, usuario)
      return redirect("inicio")
    else: 
      print (form.errors)
  else:
    form = RegistroUsuarioForm()
  return render(request, "usuario/registrar.html", {"form": form})

def perfil_usuario(request, username):
    usuario = get_object_or_404(Usuario, username=username)
    fotos = Foto.objects.filter(usuario=usuario).order_by('-fecha_subida')
    is_following = False
    
    if request.user.is_authenticated and request.user != usuario:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=usuario
        ).exists()
    
    context = {
        'usuario': usuario,
        'fotos': fotos,
        'is_following': is_following
    }
    return render(request, 'usuario/perfil.html', context)

@login_required
@require_POST
def follow_user(request, username):
    print(f"\nFollowing user: {username}")
    
    # Parse username and domain
    if '@' in username:
        username, domain = username.split('@')
        
        # Don't allow following yourself
        local_domain = get_valor('domain')
        if domain == local_domain and username == request.user.username:
            return JsonResponse({'success': False, 'error': 'No puedes seguirte a ti mismo'})
            
        actor_url = f"https://{domain}/ap/{username}"
        print(f"Following remote user at: {actor_url}")
        
        # Check if already following
        follow = Follow.objects.filter(
            follower=request.user,
            actor_url=actor_url
        ).first()
        
        if follow:
            # Unfollow
            follow.delete()
            print("Unfollowed user")
            return JsonResponse({'success': True})
        
        # Create new follow
        follow = Follow.objects.create(
            follower=request.user,
            actor_url=actor_url
        )
        print("New follow created")
        
        # Fetch their posts immediately
        posts = fetch_remote_posts(actor_url)
        print(f"Found {len(posts)} posts")
        for post_data in posts:
            try:
                print(f"Creating/updating post: {post_data['remote_id']}")
                RemotePost.objects.get_or_create(
                    remote_id=post_data['remote_id'],
                    defaults={
                        'actor_url': post_data['actor_url'],
                        'content': post_data['content'],
                        'image_url': post_data['image_url'],
                        'published': post_data['published']
                    }
                )
            except Exception as e:
                print(f"Error saving post: {e}")
                import traceback
                traceback.print_exc()
                
    return JsonResponse({'success': True})

@login_required
@require_POST
def unfollow_user(request, username):
    if '@' in username:
        # Handle remote user
        username, domain = username.split('@', 1)
        actor_url = f"https://{domain}/ap/{username}"
        Follow.objects.filter(
            follower=request.user,
            following__isnull=True,
            actor_url=actor_url
        ).delete()
    else:
        # Handle local user
        user_to_unfollow = get_object_or_404(Usuario, username=username)
        Follow.objects.filter(
            follower=request.user,
            following=user_to_unfollow,
            actor_url__isnull=True
        ).delete()
    
    return JsonResponse({'success': True})

def search_users_remote(query):
    """Search for remote users using WebFinger"""
    if '@' in query:
        username, domain = query.rsplit('@', 1)
        
        # Try WebFinger lookup
        try:
            webfinger_url = f"https://{domain}/.well-known/webfinger"
            params = {
                'resource': f'acct:{username}@{domain}'
            }
            headers = {
                'Accept': 'application/jrd+json'
            }
            
            print(f"Checking WebFinger at {webfinger_url}")
            response = requests.get(webfinger_url, params=params, headers=headers)
            
            if response.status_code != 200:
                print(f"WebFinger lookup failed: {response.status_code}")
                return []
                
            data = response.json()
            
            # Look for ActivityPub profile link
            ap_url = None
            for link in data.get('links', []):
                if link.get('rel') == 'self' and link.get('type') == 'application/activity+json':
                    ap_url = link.get('href')
                    break
            
            if not ap_url:
                print("No ActivityPub profile URL found")
                return []
                
            # Get ActivityPub profile
            headers = {
                'Accept': 'application/activity+json'
            }
            response = requests.get(ap_url, headers=headers)
            
            if response.status_code != 200:
                print(f"ActivityPub profile lookup failed: {response.status_code}")
                return []
                
            profile = response.json()
            
            # Return user info
            return [{
                'username': username,
                'name': profile.get('name', username),
                'domain': domain,
                'is_local': False,
                'bio': profile.get('summary', ''),
                'avatar_url': profile.get('icon', {}).get('url', None),
                'actor_url': ap_url
            }]
            
        except Exception as e:
            print(f"Error looking up remote user: {e}")
            import traceback
            traceback.print_exc()
            return []
            
    return []

@login_required
def buscar_usuarios(request):
    query = request.GET.get('q', '')
    print(f"\nDirect search for {query}")
    
    results = []
    
    if '@' in query:
        # Remote user search
        if query.count('@') > 1:
            query = query.replace('@', '', 1)
        results = search_users_remote(query)
    else:
        # Local user search
        local_users = Usuario.objects.filter(username__icontains=query)
        for user in local_users:
            results.append({
                'username': user.username,
                'name': user.nombreCompleto or user.username,
                'domain': get_valor('domain'),
                'is_local': True,
                'bio': '',  # Add if you have this field
                'avatar_url': user.avatar.url if user.avatar else None,
                'actor_url': f"https://{get_valor('domain')}/ap/{user.username}"
            })
    
    # Add follow status
    for user in results:
        if user['is_local']:
            user['is_followed'] = Follow.objects.filter(
                follower=request.user,
                following__username=user['username']
            ).exists()
        else:
            user['is_followed'] = Follow.objects.filter(
                follower=request.user,
                actor_url=user['actor_url']
            ).exists()
    
    return render(request, 'usuario/resultados_busqueda.html', {
        'query': query,
        'users': results
    })

def fetch_remote_posts(actor_url):
    """Fetch posts from a remote user's outbox"""
    print(f"\nFetching posts from {actor_url}")
    
    # First get the actor info to find their outbox
    print("Getting actor info...")
    headers = {
        'Accept': 'application/activity+json',
        'User-Agent': 'MAlbum/1.0 (+https://malbum.org)'
    }
    print(f"Using headers: {headers}")
    
    try:
        # Get actor info
        response = requests.get(actor_url, headers=headers)
        print(f"Actor response status: {response.status_code}")
        print(f"Actor response headers: {response.headers}")
        print(f"Actor response content: {response.text[:500]}...")
        
        if response.status_code != 200:
            print(f"Error getting actor info: {response.status_code}")
            return []
            
        actor_data = response.json()
        outbox_url = actor_data.get('outbox')
        print(f"Found outbox URL: {outbox_url}")
        
        if not outbox_url:
            print("No outbox URL found")
            return []
            
        # Get the outbox
        print(f"Getting outbox from {outbox_url}")
        response = requests.get(outbox_url, headers=headers)
        print(f"Outbox response status: {response.status_code}")
        print(f"Outbox response headers: {response.headers}")
        print(f"Outbox response content: {response.text[:500]}...")
        
        if response.status_code != 200:
            print(f"Error getting outbox: {response.status_code}")
            return []
            
        outbox_data = response.json()
        
        # Get the first page if this is a collection
        if outbox_data.get('type') == 'OrderedCollection':
            first_page_url = outbox_data.get('first')
            if first_page_url:
                print("Getting first page of outbox")
                response = requests.get(first_page_url, headers=headers)
                print(f"First page response status: {response.status_code}")
                if response.status_code == 200:
                    outbox_data = response.json()
        
        # Process the items
        items = outbox_data.get('orderedItems', [])
        print(f"Found {len(items)} items")
        
        posts = []
        for item in items:
            try:
                # Only process Create activities with Note objects
                if item.get('type') == 'Create' and item.get('object', {}).get('type') == 'Note':
                    obj = item['object']
                    
                    # Look for image attachments
                    attachments = obj.get('attachment', [])
                    image_urls = [
                        att['url'] for att in attachments 
                        if att.get('mediaType', '').startswith('image/')
                    ]
                    
                    if image_urls:  # Only process posts with images
                        post = {
                            'remote_id': obj['id'],
                            'actor_url': item['actor'],
                            'content': obj.get('content', ''),
                            'image_url': image_urls[0],  # Use first image
                            'published': obj.get('published')
                        }
                        print(f"Found post: {post}")
                        posts.append(post)
                    else:
                        print(f"No images found in post {obj['id']}")
                else:
                    print(f"Skipping non-Note activity: {item.get('type')} - {item.get('object', {}).get('type')}")
            except Exception as e:
                print(f"Error processing item: {e}")
                print(f"Item content: {item}")
                
        print(f"Returning {len(posts)} posts")
        return posts
        
    except Exception as e:
        print(f"Error fetching posts: {e}")
        import traceback
        traceback.print_exc()
        return []

@login_required
def editar_usuario(request):
    if request.method == "POST":
        form = EditarUsuarioForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            usuario = form.save()
            messages.success(request, 'Perfil actualizado correctamente')
            return redirect("control")
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario')
    else:
        form = EditarUsuarioForm(instance=request.user)

    return render(request, "usuario/registrar.html", {
        "form": form,
        "is_edit": True
    })