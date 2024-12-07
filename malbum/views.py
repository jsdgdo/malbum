from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .forms import FotoForm, EtiquetaForm, ColeccionForm
from .models import Foto, Etiqueta, Coleccion
from django.conf import settings
from django.core.files.storage import default_storage
import json
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from malbum.models import Foto, Etiqueta, Coleccion
from usuario.models import Usuario


def inicio(request):
  if request.user.is_authenticated:
    return redirect('tablon')
  else:
    return redirect('splash')

def splash(request):
  hay_usuario = Usuario.objects.exists()
  return render(request, 'inicio.html', {'hay_usuario': hay_usuario})

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
  return render(request, 'subir_foto.html', {'form': form, 'foto': None})

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
  etiqueta = request.GET.get('etiqueta')
  coleccion = request.GET.get('coleccion')

  if etiqueta:
    fotos = fotos.filter(etiquetas__nombre=etiqueta)
  if coleccion:
    fotos = fotos.filter(colecciones__titulo=coleccion)
  
  context = { 
    'fotos' : fotos,
    'etiquetas' : Etiqueta.objects.all(),
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

@login_required
def editar_foto(request, id):
  foto = get_object_or_404(Foto, id=id, usuario=request.user)
  if request.method == 'POST':
    form = FotoForm(request.POST, request.FILES, instance=foto)
    if form.is_valid():
      form.save()
      return redirect('detalle_foto', id=foto.id)
  else:
    form = FotoForm(instance=foto)
  return render(request, 'subir_foto.html', {'form': form, 'foto': foto})

@staff_member_required
def control(request):
  if request.method == 'POST':
    if 'export_data' in request.POST:
      data = {
          'usuarios': list(Usuario.objects.values('username', 'email', 'is_staff', 'is_active', 'is_superuser', 'date_joined')),
          'fotos': list(Foto.objects.values('titulo', 'descripcion', 'alt_descripcion', 'licencia', 'advertencia_contenido', 'camara', 'lente', 'configuracion', 'usuario_id', 'imagen')),
          'etiquetas': list(Etiqueta.objects.values('nombre')),
          'colecciones': list(Coleccion.objects.values('titulo', 'descripcion', 'usuario_id')),
      }
      response = HttpResponse(
          json.dumps(data, ensure_ascii=False, indent=4),
          content_type='application/json'
      )
      response['Content-Disposition'] = 'attachment; filename="exported_data.json"'
      return response

    elif 'import_data' in request.POST and request.FILES.get('data_file'):
      
      try:
        data_file = request.FILES['data_file']
        data = json.load(data_file)

        for user_data in data.get('usuarios', []):
          Usuario.objects.create(**user_data)

        for etiqueta_data in data.get('etiquetas', []):
          Etiqueta.objects.create(**etiqueta_data)

        for coleccion_data in data.get('colecciones', []):
          Coleccion.objects.create(**coleccion_data)

        for foto_data in data.get('fotos', []):
          Foto.objects.create(**foto_data)

        return JsonResponse({'success': True, 'message': 'Datos importados exitosamente.'})
      except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=400)

    elif 'update_settings' in request.POST:
      
      domain = request.POST.get('domain')
      activity_pub_key = request.POST.get('activity_pub_key')

      # to do, ver como hacer esta parte
      settings.CUSTOM_DOMAIN = domain  
      settings.ACTIVITY_PUB_KEY = activity_pub_key

      return JsonResponse({'success': True, 'message': 'Configuraciones actualizadas exitosamente.'})

  return render(request, 'control_center.html')