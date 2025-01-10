from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .forms import FotoForm, EtiquetaForm, ColeccionForm
from .models import Foto, Etiqueta, Coleccion, SolicitudImagen, Configuracion
from usuario.models import Usuario, Follow, RemotePost
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connection
from django.db.models import Q
import json
import os
import zipfile
from io import BytesIO
import logging
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.utils import timezone
import uuid
from django.contrib import messages
from django.urls import reverse
from .config import get_valor, set_valor, get_default_config, save_config, load_config
from usuario.activitypub import notify_followers_of_new_post
from itertools import chain

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
          
          # Notify followers of the new post
          notify_followers_of_new_post(foto)
          
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
    # Get local photos
    fotos_locales = Foto.objects.filter(
        Q(usuario=request.user) | 
        Q(usuario__in=request.user.following.all())
    ).order_by('-fecha_creacion')
    
    # Get remote posts from users we follow
    follows = Follow.objects.filter(follower=request.user, following__isnull=True)
    remote_posts = RemotePost.objects.filter(actor_url__in=follows.values_list('actor_url', flat=True))
    
    # Combine and sort
    fotos = sorted(
        chain(fotos_locales, remote_posts),
        key=lambda x: x.fecha_creacion if hasattr(x, 'fecha_creacion') else x.published,
        reverse=True
    )
    
    context = {
        'fotos': fotos,
        'usuario': request.user,
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
                    # Look for config.json in the ZIP
                    config_filename = next((name for name in z.namelist() if name.endswith('config.json')), None)
                    if config_filename:
                        with z.open(config_filename) as config_file:
                            config_content = config_file.read().decode('utf-8')
                            save_config(json.loads(config_content))
                    
                    # Look for the data JSON file
                    json_filename = next((name for name in z.namelist() if name.endswith('.json') and name != 'config.json'), None)
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

            # Process the imported data
            Foto.objects.all().delete()
            Etiqueta.objects.all().delete()
            Coleccion.objects.all().delete()
            Usuario.objects.all().delete()

            user_id_map = {}

            for user_data in data.get('usuarios', []):
                print(f"Importing user: {user_data['username']}")
                old_id = user_data.get('id')
                user = Usuario(
                    username=user_data['username'],
                    email=user_data['email'],
                    is_staff=user_data['is_staff'],
                    is_active=user_data['is_active'],
                    is_superuser=user_data['is_superuser'],
                    date_joined=user_data['date_joined'],
                    nombreCompleto=user_data.get('nombreCompleto', ''),
                    bio=user_data.get('bio', '')
                )
                user.password = user_data['password']
                user.save()
                if old_id:
                    user_id_map[old_id] = user.id

            for etiqueta_data in data.get('etiquetas', []):
                print(f"Importing etiqueta: {etiqueta_data['nombre']}")
                Etiqueta.objects.create(nombre=etiqueta_data['nombre'])

            for coleccion_data in data.get('colecciones', []):
                print(f"Importing coleccion: {coleccion_data['titulo']}")
                old_user_id = coleccion_data['usuario_id']
                new_user_id = user_id_map.get(old_user_id)
                if new_user_id:
                    usuario = Usuario.objects.get(id=new_user_id)
                    Coleccion.objects.create(
                        titulo=coleccion_data['titulo'],
                        descripcion=coleccion_data['descripcion'],
                        usuario=usuario
                    )

            for foto_data in data.get('fotos', []):
                print(f"Importing foto: {foto_data['titulo']}")
                old_user_id = foto_data['usuario_id']
                new_user_id = user_id_map.get(old_user_id)
                if new_user_id:
                    usuario = Usuario.objects.get(id=new_user_id)
                    Foto.objects.create(
                        titulo=foto_data['titulo'],
                        descripcion=foto_data['descripcion'],
                        alt_descripcion=foto_data['alt_descripcion'],
                        licencia=foto_data['licencia'],
                        advertencia_contenido=foto_data['advertencia_contenido'],
                        camara=foto_data['camara'],
                        lente=foto_data['lente'],
                        configuracion=foto_data['configuracion'],
                        usuario=usuario,
                        imagen=f"fotos/{os.path.basename(foto_data.get('imagen', ''))}"
                    )

            # If no config.json was found or imported, ensure we have defaults
            if not get_valor('dominio'):
                initial_config = get_default_config()
                initial_config['dominio'] = request.get_host()
                save_config(initial_config)

            return True, 'Datos importados exitosamente.'
            
        except Exception as e:
            print(f"Error during import: {e}")
            return False, str(e)

    return False, 'Solicitud inválida.'

@login_required
def control(request):
    if request.method == 'POST':
        if 'update_settings' in request.POST:
            dominio = request.POST.get('domain', '').strip()
            clave_activitypub = request.POST.get('activity_pub_key', '').strip()
            
            if dominio:
                set_valor('dominio', dominio)
            if clave_activitypub:
                set_valor('clave_activitypub', clave_activitypub)
            
            messages.success(request, 'Configuración actualizada correctamente.')
            return redirect('control')
            
        if 'reset_installation' in request.POST:
            # Delete all data
            SolicitudImagen.objects.all().delete()
            Foto.objects.all().delete()
            Etiqueta.objects.all().delete()
            Coleccion.objects.all().delete()
            Usuario.objects.all().delete()
            
            # Reset config.json to defaults
            initial_config = get_default_config()
            save_config(initial_config)
            
            import shutil
            media_root = settings.MEDIA_ROOT
            for dir_name in ['fotos', 'profile_pics']:
                dir_path = os.path.join(media_root, dir_name)
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
                    os.makedirs(dir_path)
            
            logout(request)
            return redirect('splash')
        
        elif 'export_data' in request.POST:
            include_images = request.POST.get('include_images') == 'true'

            data = {
                'usuarios': [{
                    'id': user.id,
                    'username': user.username,
                    'password': user.password,
                    'email': user.email,
                    'is_staff': user.is_staff,
                    'is_active': user.is_active,
                    'is_superuser': user.is_superuser,
                    'date_joined': user.date_joined,
                    'nombreCompleto': user.nombreCompleto if hasattr(user, 'nombreCompleto') else '',
                    'bio': user.bio if hasattr(user, 'bio') else '',
                } for user in Usuario.objects.all()],
                'fotos': list(Foto.objects.values(
                    'titulo', 'descripcion', 'alt_descripcion', 'licencia', 'advertencia_contenido',
                    'camara', 'lente', 'configuracion', 'usuario_id', 'imagen')),
                'etiquetas': list(Etiqueta.objects.values('nombre')),
                'colecciones': list(Coleccion.objects.values(
                    'titulo', 'descripcion', 'usuario_id')),
            }

            json_data = json.dumps(data, ensure_ascii=False, indent=4, cls=DjangoJSONEncoder)

            if include_images:
                buffer = BytesIO()
                with zipfile.ZipFile(buffer, 'w') as zip_file:
                    # Add config.json to the export
                    config = load_config()  # Import this from config.py
                    zip_file.writestr('config.json', json.dumps(config, indent=2))
                    
                    zip_file.writestr('db.json', json_data)

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
                response = HttpResponse(
                    json_data,
                    content_type='application/json'
                )
                response['Content-Disposition'] = 'attachment; filename="exported_data.json"'
                return response

        elif 'import_data' in request.POST:
            success, message = handle_import_data(request)
            return JsonResponse({'success': success, 'message': message}, status=200 if success else 400)

    # Get current settings
    context = {
        'dominio': get_valor('dominio', request.get_host()),
        'clave_activitypub': get_valor('clave_activitypub', ''),
    }
    return render(request, 'control.html', context)

def importar_datos(request):
  if request.method == 'POST':
    success, message = handle_import_data(request)
    if success:
      return redirect('inicio')
    else:
      return JsonResponse({'success': False, 'message': message}, status=400)
  return render(request, 'importar_datos.html')

@require_POST
def solicitar_imagen(request, foto_id):
    foto = get_object_or_404(Foto, id=foto_id)
    email = request.POST.get('email')
    mensaje = request.POST.get('mensaje')
    
    solicitud = SolicitudImagen.objects.create(
        foto=foto,
        email_solicitante=email,
        mensaje=mensaje
    )
    
    # Notificar al dueño de la foto
    send_mail(
        f'Nueva solicitud de imagen para "{foto.titulo}"',
        f'Has recibido una nueva solicitud para la imagen "{foto.titulo}".\n\n'
        f'Email del solicitante: {email}\n'
        f'Mensaje: {mensaje}\n\n'
        f'Puedes gestionar esta solicitud desde tu panel de control.',
        settings.DEFAULT_FROM_EMAIL,
        [foto.usuario.email],
        fail_silently=False,
    )
    
    messages.success(request, 'Solicitud enviada correctamente. El fotógrafo revisará tu petición.')
    return redirect('detalle_foto', id=foto_id)

@login_required
def gestionar_solicitudes(request):
    solicitudes = SolicitudImagen.objects.filter(
        foto__usuario=request.user
    ).select_related('foto')
    
    return render(request, 'gestionar_solicitudes.html', {
        'solicitudes': solicitudes
    })

@login_required
@require_POST
def responder_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(SolicitudImagen, id=solicitud_id, foto__usuario=request.user)
    respuesta = request.POST.get('respuesta')
    
    if respuesta == 'aprobar':
        # Generar URL única para la descarga
        url_token = str(uuid.uuid4())
        solicitud.url_descarga = url_token
        solicitud.estado = 'aprobada'
        
        # Enviar email de aprobación
        send_mail(
            'Tu solicitud de imagen ha sido aprobada',
            f'Tu solicitud para la imagen "{solicitud.foto.titulo}" ha sido aprobada.\n\n'
            f'Puedes descargar la imagen en alta resolución desde el siguiente enlace:\n'
            f'{request.build_absolute_uri(reverse("descargar_imagen", args=[url_token]))}\n\n'
            f'Este enlace expirará en 24 horas.',
            settings.DEFAULT_FROM_EMAIL,
            [solicitud.email_solicitante],
            fail_silently=False,
        )
    else:
        solicitud.estado = 'rechazada'
        # Enviar email de rechazo
        send_mail(
            'Respuesta a tu solicitud de imagen',
            f'Lo sentimos, tu solicitud para la imagen "{solicitud.foto.titulo}" '
            f'no ha podido ser aprobada en esta ocasión.\n\n'
            f'Gracias por tu interés.',
            settings.DEFAULT_FROM_EMAIL,
            [solicitud.email_solicitante],
            fail_silently=False,
        )
    
    solicitud.fecha_respuesta = timezone.now()
    solicitud.save()
    
    messages.success(request, 'Respuesta enviada correctamente.')
    return redirect('gestionar_solicitudes')

def descargar_imagen(request, token):
    solicitud = get_object_or_404(SolicitudImagen, 
                                 url_descarga=token, 
                                 estado='aprobada',
                                 fecha_respuesta__gte=timezone.now() - timezone.timedelta(days=1))
    
    response = HttpResponse(content_type='image/jpeg')
    response['Content-Disposition'] = f'attachment; filename="{solicitud.foto.imagen.name}"'
    
    with open(solicitud.foto.imagen.path, 'rb') as img:
        response.write(img.read())
    
    return response

@login_required
def gestionar_colecciones(request):
    colecciones = Coleccion.objects.filter(usuario=request.user)
    coleccion_actual = None
    
    if request.method == 'POST':
        # Crear nueva colección
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        if titulo:
            coleccion = Coleccion.objects.create(
                titulo=titulo,
                descripcion=descripcion,
                usuario=request.user
            )
            return redirect('gestionar_colecciones')
    
    # Obtener colección seleccionada
    coleccion_id = request.GET.get('coleccion_id')
    if coleccion_id:
        coleccion_actual = get_object_or_404(Coleccion, id=coleccion_id, usuario=request.user)
    
    return render(request, 'colecciones.html', {
        'colecciones': colecciones,
        'coleccion_actual': coleccion_actual
    })

@login_required
def buscar_fotos(request):
    query = request.GET.get('q', '')
    if len(query) >= 2:
        fotos = Foto.objects.filter(
            usuario=request.user
        ).filter(
            Q(titulo__icontains=query) | 
            Q(descripcion__icontains=query)
        )[:10]  # Limitar a 10 resultados
        
        resultados = [{
            'id': foto.id,
            'titulo': foto.titulo,
            'thumbnail_url': foto.get_thumbnail_url()
        } for foto in fotos]
        
        return JsonResponse({'fotos': resultados})
    return JsonResponse({'fotos': []})

@login_required
@require_POST
def agregar_foto_coleccion(request):
    data = json.loads(request.body)
    foto_id = data.get('foto_id')
    coleccion_id = data.get('coleccion_id')
    
    coleccion = get_object_or_404(Coleccion, id=coleccion_id, usuario=request.user)
    foto = get_object_or_404(Foto, id=foto_id, usuario=request.user)
    
    coleccion.fotos.add(foto)
    return JsonResponse({'success': True})

@login_required
@require_POST
def quitar_foto_coleccion(request):
    data = json.loads(request.body)
    foto_id = data.get('foto_id')
    coleccion_id = data.get('coleccion_id')
    
    coleccion = get_object_or_404(Coleccion, id=coleccion_id, usuario=request.user)
    foto = get_object_or_404(Foto, id=foto_id, usuario=request.user)
    
    coleccion.fotos.remove(foto)
    return JsonResponse({'success': True})