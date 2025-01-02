from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegistroUsuarioForm
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Usuario
from malbum.models import Foto
from malbum.config import get_default_config, save_config
from django.contrib.auth.models import Follow
from malbum.models import Etiqueta, Coleccion
from django.contrib.auth.decorators import login_required


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
    hay_usuario = Usuario.objects.exists()
    
    # Get the photos uploaded by the user
    fotos = Foto.objects.filter(usuario=usuario)
    
    # Apply filters if present
    etiqueta = request.GET.get('etiqueta')
    coleccion = request.GET.get('coleccion')

    if etiqueta:
        fotos = fotos.filter(etiquetas__nombre=etiqueta)
    if coleccion:
        fotos = fotos.filter(colecciones__titulo=coleccion)
    
    fotos = fotos.order_by('-fecha_subida')

    # Check if the logged-in user is following this profile
    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=usuario
        ).exists()

    return render(request, 'usuario/perfil.html', {
        'usuario': usuario,
        'hay_usuario': hay_usuario,
        'fotos': fotos,
        'is_following': is_following,
        'etiquetas': Etiqueta.objects.filter(foto__usuario=usuario).distinct(),
        'colecciones': Coleccion.objects.filter(usuario=usuario),
        'etiqueta_seleccionada': etiqueta,
        'coleccion_seleccionada': coleccion,
    })

  user = get_object_or_404(Usuario, username=username)
  activities = {
      "@context": "https://www.w3.org/ns/activitystreams",
      "type": "OrderedCollection",
      "id": f"https://{user.username}.example.com/ap/outbox",
      "orderedItems": [
          # Example activities here
      ],
  }
  return JsonResponse(activities)

@login_required
@require_POST
def follow_user(request, username):
    user_to_follow = get_object_or_404(Usuario, username=username)
    if request.user != user_to_follow:
        Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow,
            defaults={
                'actor_url': f"https://{get_valor('dominio')}/ap/{request.user.username}",
                'remote_username': request.user.username,
                'remote_domain': get_valor('dominio')
            }
        )
    return redirect('perfil_usuario', username=username)

@login_required
@require_POST
def unfollow_user(request, username):
    user_to_unfollow = get_object_or_404(Usuario, username=username)
    Follow.objects.filter(
        follower=request.user,
        following=user_to_unfollow
    ).delete()
    return redirect('perfil_usuario', username=username)