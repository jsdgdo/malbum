from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import FotoForm, EtiquetaForm, ColeccionForm
from .models import Etiqueta, Coleccion

def inicio(request):
  return render(request, 'inicio.html')

@login_required
def subir_foto(request):
  if request.method == 'POST':
    form = FotoForm(request.POST, request.FILES)
    if form.is_valid():
      foto = form.save(commit=False)
      foto.usuario = request.user
      foto.save()
      foto.save_m2m()
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