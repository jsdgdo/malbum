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
  hay_usuario = Usuario.objects.exists()
  # Get the user or return a 404 if not found
  usuario = get_object_or_404(Usuario, username=username)
  
  # Fetch the photos uploaded by the user
  fotos = Foto.objects.filter(usuario=usuario).order_by('-fecha_subida')

  return render(request, 'usuario/perfil.html', {
    'usuario': usuario,
    'hay_usuario': hay_usuario,
    'fotos': fotos,
  })

def activitypub_actor(request, username):
  user = get_object_or_404(Usuario, username=username)
  return JsonResponse(user.get_actor())

@csrf_exempt
@require_POST
def activitypub_inbox(request, username):
  return JsonResponse({"status": "received"}, status=202)

def activitypub_outbox(request, username):
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