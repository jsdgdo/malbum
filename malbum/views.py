from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .forms import FotoForm, EtiquetaForm, ColeccionForm
from .models import Foto, Etiqueta, Coleccion
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from malbum.models import Foto, Etiqueta, Coleccion
from usuario.models import Usuario
from django.db import connection
import logging

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

def handle_import_data(request):
  if request.method == 'POST' and request.FILES.get('data_file'):
    try:
      data_file = request.FILES['data_file']
      data = json.load(data_file)

      # Import Usuarios
      for user_data in data.get('usuarios', []):
        Usuario.objects.create(
          username=user_data['username'],
          password=user_data['password'],
          email=user_data['email'],
          is_staff=user_data['is_staff'],
          is_active=user_data['is_active'],
          is_superuser=user_data['is_superuser'],
          date_joined=user_data['date_joined']
        )

      # Import Etiquetas
      for etiqueta_data in data.get('etiquetas', []):
        Etiqueta.objects.create(
          nombre=etiqueta_data['nombre']
        )

      # Import Colecciones
      for coleccion_data in data.get('colecciones', []):
        Coleccion.objects.create(
          titulo=coleccion_data['titulo'],
          descripcion=coleccion_data['descripcion'],
          usuario_id=coleccion_data['usuario_id']
        )
        
      # Import Fotos
      for foto_data in data.get('fotos', []):
        Foto.objects.create(
          titulo=foto_data['titulo'],
          usuario_id=foto_data['usuario_id'],
          descripcion= foto_data['descripcion'],
          alt_descripcion= foto_data['alt_descripcion'],
          licencia= foto_data['licencia'],
          advertencia_contenido= foto_data['advertencia_contenido'],
          camara= foto_data['camara'],
          lente= foto_data['lente'],
          configuracion= foto_data['configuracion'],
          imagen= foto_data['imagen'],
        )
        
      return True, 'Datos importados exitosamente.'
    except Exception as e:
      return False, f'Error al importar datos: {str(e)}'
  return False, 'Solicitud inválida.'

@staff_member_required
def control(request):
  if request.method == 'POST':
    if 'export_data' in request.POST:
      data = {
        'usuarios': list(Usuario.objects.values(
          'username','password', 'email', 'is_staff', 'is_active', 'is_superuser', 'date_joined')),
        'fotos': list(Foto.objects.values(
          'titulo', 'descripcion', 'alt_descripcion', 'licencia', 'advertencia_contenido',
          'camara', 'lente', 'configuracion', 'usuario_id', 'imagen')),
        'etiquetas': list(Etiqueta.objects.values('nombre')),
        'colecciones': list(Coleccion.objects.values(
          'titulo', 'descripcion', 'usuario_id')),
      }
      response = HttpResponse(
        json.dumps(data, ensure_ascii=False, indent=4, cls=DjangoJSONEncoder),
        content_type='application/json'
      )
      response['Content-Disposition'] = 'attachment; filename="exported_data.json"'
      return response

    elif 'import_data' in request.POST:
      success, message = handle_import_data(request)
      return JsonResponse({'success': success, 'message': message}, status=200 if success else 400)

  return render(request, 'control.html')

def importar_datos(request):
  if request.method == 'POST':
    success, message = handle_import_data(request)
    if success:
      return redirect('inicio')
    else:
      return JsonResponse({'success': False, 'message': message}, status=400)
  return render(request, 'importar_datos.html')