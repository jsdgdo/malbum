from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import FotoForm, EtiquetaForm, ColeccionForm
from .models import Foto, Etiqueta, Coleccion
from django.shortcuts import get_object_or_404

def splash(request):
  return render(request, 'inicio.html')

def inicio(request):
  if request.user.is_authenticated:
    return redirect('tablon')
  else:
    return render(request, 'inicio.html')

@login_required
def subir_foto(request):
  if request.method == 'POST':
    form = FotoForm(request.POST, request.FILES)
    if form.is_valid():
      foto = form.save(commit=False)
      foto.usuario = request.user
      foto.save()

      form.save_m2m()
      return redirect('inicio')
  else:
    form = FotoForm()
  return render(request, 'subir_foto.html', {'form': form})

@require_POST
@login_required 
def agregar_etiqueta(request):
  form = EtiquetaForm(request.POST)
  if form.is_valid():
    etiqueta = form.save()
    return JsonResponse({'id': etiqueta.id, 'nombre': etiqueta.nombre})
  return JsonResponse({'error': form.errors}, status=400)

@require_POST
@login_required
def agregar_coleccion(request):
  form = ColeccionForm(request.POST)
  if form.is_valid():
    coleccion = form.save(commit=False)
    coleccion.usuario = request.user
    coleccion.save()
    return JsonResponse({'id': coleccion.id, 'titulo': coleccion.titulo})
  return JsonResponse({'error': form.errors}, status=400)

@login_required
def tablon(request):
  fotos = Foto.objects.filter(usuario=request.user)
  etiqueta = request.GET.get('tag')
  coleccion = request.GET.get('coleccion')

  if etiqueta:
    fotos = fotos.filter(etiquetas__nombre=etiqueta)
  if coleccion:
    fotos = fotos.filter(colecciones__titulo=coleccion)
  
  context = { 
    'fotos' : fotos,
    'eitquetas' : Etiqueta.objects.all(),
    'colecciones' : Coleccion.objects.all(),
    'etiqueta_seleccionada' : etiqueta,
    'coleccion_seleccionada' : coleccion
  }
  return render(request, 'tablon.html', context)

def detalle_foto(request, id):
    foto = get_object_or_404(Foto, id=id)
    context = {
        'foto': foto,
        'etiquetas': foto.etiquetas.all() if foto.etiquetas.exists() else None,
        'colecciones': foto.colecciones.all() if foto.colecciones.exists() else None,
        'licencia': foto.licencia
    }
    return render(request, 'detalle_foto.html', {'foto': foto})