from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegistroUsuarioForm
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Usuario
from malbum.models import Foto


def registrarUsuario(request):
  if request.method == "POST":
    form = RegistroUsuarioForm(request.POST, request.FILES)
    if form.is_valid():
      usuario = form.save()
      login(request, usuario)
      return redirect("inicio")
    else: 
      print (form.errors)
  else:
    form = RegistroUsuarioForm()
  return render(request, "usuario/registrar.html", {"form": form})

def perfil_usuario(request, username):
  # Get the user or return a 404 if not found
  usuario = get_object_or_404(Usuario, username=username)
  
  # Fetch the photos uploaded by the user
  fotos = Foto.objects.filter(usuario=usuario).order_by('-fecha_subida')

  return render(request, 'usuario/perfil.html', {
    'usuario': usuario,
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