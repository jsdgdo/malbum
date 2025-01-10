from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import RegistroUsuarioForm
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
    if '@' in username:
        # Handle remote user
        try:
            data = json.loads(request.body)
            actor_url = data.get('actor_url')
            remote_username = data.get('remote_username')
            remote_domain = data.get('remote_domain')
            
            if not all([actor_url, remote_username, remote_domain]):
                return JsonResponse({'success': False, 'error': 'Datos incompletos'})
            
            # For remote users, following_id is None
            follow, created = Follow.objects.get_or_create(
                follower=request.user,
                remote_username=remote_username,
                remote_domain=remote_domain,
                defaults={
                    'following': None,
                    'actor_url': actor_url
                }
            )
            
            if created:
                # Fetch their posts immediately
                print(f"Fetching posts for new follow: {actor_url}")
                posts = fetch_remote_posts(actor_url)
                print(f"Found {len(posts)} posts")
                for post_data in posts:
                    try:
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
                
            return JsonResponse({'success': True})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Datos inválidos'})
    else:
        # Handle local user
        user_to_follow = get_object_or_404(Usuario, username=username)
        if request.user == user_to_follow:
            return JsonResponse({'success': False, 'error': 'No puedes seguirte a ti mismo'})
        
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        
        return JsonResponse({'success': True})

@login_required
@require_POST
def unfollow_user(request, username):
    if '@' in username:
        # Handle remote user
        username, domain = username.split('@', 1)
        Follow.objects.filter(
            follower=request.user,
            remote_username=username,
            remote_domain=domain
        ).delete()
    else:
        # Handle local user
        user_to_unfollow = get_object_or_404(Usuario, username=username)
        Follow.objects.filter(
            follower=request.user,
            following=user_to_unfollow
        ).delete()
    
    return JsonResponse({'success': True})

def buscar_usuarios(request):
    query = request.GET.get('q', '').strip()
    results = []
    
    if query and len(query) >= 3:  # Only search for queries >= 3 chars
        if '@' in query:
            # Direct search for a specific user@domain
            username, domain = query.split('@', 1)
            results = search_users_remote(f"{username}@{domain}")
        else:
            # General search across known instances
            results = search_users_remote(query)
            
        # Add follow status for each user if the requester is authenticated
        if request.user.is_authenticated:
            for user in results:
                user['is_followed'] = Follow.objects.filter(
                    follower=request.user,
                    remote_username=user['username'],
                    remote_domain=user['domain']
                ).exists()

    return render(request, 'usuario/resultados_busqueda.html', {
        'query': query,
        'users': results
    })