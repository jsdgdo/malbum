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
import os
import zipfile
from io import BytesIO
import logging
from django.contrib.auth import logout

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
  hay_usuario = Usuario.objects.exists()
  foto = get_object_or_404(Foto, id=id)
  context = {
      'foto': foto,
      'etiquetas': foto.etiquetas.all() if foto.etiquetas.exists() else None,
      'colecciones': foto.colecciones.all() if foto.colecciones.exists() else None,
      'licencia': foto.licencia
  }
  return render(request, 'detalle_foto.html', {'foto': foto, 'hay_usuario': hay_usuario})

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
      logging.warning(f"Uploaded file: {data_file.name}, Size: {data_file.size} bytes")

      if zipfile.is_zipfile(data_file):
        print("Detected a ZIP file")
        with zipfile.ZipFile(data_file) as z:
          
          json_filename = next((name for name in z.namelist() if name.endswith('.json')), None)
          if not json_filename:
            raise ValueError("El archivo ZIP no contiene un archivo JSON válido.")

          print(f"Found JSON file in ZIP: {json_filename}")
          with z.open(json_filename) as json_file:
            json_content = json_file.read().decode('utf-8')
            data = json.loads(json_content)

          for file_name in z.namelist():
            if file_name.endswith(('.jpg', '.jpeg', '.png', '.gif')):
              print(f"Extracting image: {file_name}")
              with z.open(file_name) as img_file:
                img_path = os.path.join('fotos', os.path.basename(file_name))
                default_storage.save(img_path, img_file)
      else:
        logging.warning("Processing plain JSON file")
        data_file.seek(0)
        json_content = data_file.read().decode('utf-8').strip()
        logging.warning(f"First 200 characters of JSON content: {json_content[:200]}")

        if not json_content:
          raise ValueError("El archivo JSON está vacío.")

        data = json.loads(json_content)

      Usuario.objects.all().delete()
      Etiqueta.objects.all().delete()
      Coleccion.objects.all().delete()
      Foto.objects.all().delete()

      for user_data in data.get('usuarios', []):
        print(f"Importing user: {user_data['username']}")
        Usuario.objects.create(
          username=user_data['username'],
          password=user_data['password'],
          email=user_data['email'],
          is_staff=user_data['is_staff'],
          is_active=user_data['is_active'],
          is_superuser=user_data['is_superuser'],
          date_joined=user_data['date_joined']
        )

      for etiqueta_data in data.get('etiquetas', []):
        print(f"Importing etiqueta: {etiqueta_data['nombre']}")
        Etiqueta.objects.create(nombre=etiqueta_data['nombre'])

      for coleccion_data in data.get('colecciones', []):
        print(f"Importing coleccion: {coleccion_data['titulo']}")
        Coleccion.objects.create(
          titulo=coleccion_data['titulo'],
          descripcion=coleccion_data['descripcion'],
          usuario_id=coleccion_data['usuario_id']
        )

      for foto_data in data.get('fotos', []):
        print(f"Importing foto: {foto_data['titulo']}")
        Foto.objects.create(
          titulo=foto_data['titulo'],
          descripcion=foto_data['descripcion'],
          alt_descripcion=foto_data['alt_descripcion'],
          licencia=foto_data['licencia'],
          advertencia_contenido=foto_data['advertencia_contenido'],
          camara=foto_data['camara'],
          lente=foto_data['lente'],
          configuracion=foto_data['configuracion'],
          usuario_id=foto_data['usuario_id'],
          imagen=f"fotos/{os.path.basename(foto_data.get('imagen', ''))}"
        )

      return True, 'Datos importados exitosamente.'
    except json.JSONDecodeError as e:
      print(f"JSON Decode Error: {e}")
      return False, 'Error: El archivo JSON está malformado.'
    except Exception as e:
      print(f"General Exception: {e}")
      return False, f'Error al importar datos: {str(e)}'
  return False, 'Solicitud inválida.'

@login_required
def control(request):
  if request.method == 'POST':
    if 'reset_installation' in request.POST:
      # Delete all data - for SQLite we don't need to disable foreign key checks
      Foto.objects.all().delete()
      Etiqueta.objects.all().delete()
      Coleccion.objects.all().delete()
      Usuario.objects.all().delete()
      
      # Clear media files
      import shutil
      media_root = settings.MEDIA_ROOT
      for dir_name in ['fotos', 'profile_pics']:
        dir_path = os.path.join(media_root, dir_name)
        if os.path.exists(dir_path):
          shutil.rmtree(dir_path)
          os.makedirs(dir_path)
      
      # Logout the current user
      logout(request)
      return redirect('splash')
    
    elif 'export_data' in request.POST:
      include_images = request.POST.get('include_images', 'false') == 'true'

      # Prepare data for export
      data = {
        'usuarios': list(Usuario.objects.values(
          'username', 'password', 'email', 'is_staff', 'is_active', 'is_superuser', 'date_joined')),
        'fotos': list(Foto.objects.values(
          'titulo', 'descripcion', 'alt_descripcion', 'licencia', 'advertencia_contenido',
          'camara', 'lente', 'configuracion', 'usuario_id', 'imagen')),
        'etiquetas': list(Etiqueta.objects.values('nombre')),
        'colecciones': list(Coleccion.objects.values(
          'titulo', 'descripcion', 'usuario_id')),
      }

      json_data = json.dumps(data, ensure_ascii=False, indent=4, cls=DjangoJSONEncoder)

      if include_images:
        # Prepare a ZIP file for data and images
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zip_file:
          # Add JSON data to the ZIP
          zip_file.writestr('db.json', json_data)

          # Add images to the ZIP
          for foto in Foto.objects.all():
            if foto.imagen:
              image_path = os.path.join(settings.MEDIA_ROOT, str(foto.imagen))
              if os.path.exists(image_path):
                zip_file.write(image_path, arcname=os.path.join('media', str(foto.imagen)))

        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="exported_data_with_images.zip"'
        return response
      else:
        # Return JSON data as response
        response = HttpResponse(
          json_data,
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