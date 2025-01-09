from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import RegistroUsuarioForm
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Usuario, Follow
from malbum.models import Foto
from malbum.config import get_default_config, save_config, get_valor
from django.contrib.auth.decorators import login_required
from django.db import models
from .activitypub import search_users_remote, send_follow_activity
import json


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
    try:
        data = json.loads(request.body)
        actor_url = data.get('actor_url')
        remote_username = data.get('remote_username')
        remote_domain = data.get('remote_domain')

        # Create or get the Follow object
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            remote_username=remote_username,
            remote_domain=remote_domain,
            actor_url=actor_url
        )

        if created:
            # Send ActivityPub follow request
            send_follow_activity(request.user, actor_url)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Ya sigues a este usuario'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def unfollow_user(request, username):
    user_to_unfollow = get_object_or_404(Usuario, username=username)
    Follow.objects.filter(
        follower=request.user,
        following=user_to_unfollow
    ).delete()
    
    return JsonResponse({'success': True})

def search_users(request):
    query = request.GET.get('q', '').strip()
    results = []
    
    if query and len(query) >= 3:  # Only search for queries >= 3 chars
        # Search remote users
        results = search_users_remote(query)
    
    return render(request, 'usuario/resultados_busqueda.html', {
        'users': results[:20],  # Limit total results to 20
        'query': query
    })