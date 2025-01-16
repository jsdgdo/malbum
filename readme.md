# Malbum

Malbum es un proyecto de tesis de la Universidad Católica "Nuestra Señora de la Asunción" de Paraguay. 

El objetivo de este proyecto es crear una plataforma de gestión de fotos que permita a los usuarios gestionar sus fotos de manera segura y privada.

## Los requerimientos del proyecto son los siguientes:
- Tener un servidor físico o virtual conectado a internet. Preferentemente con sistema operativo Linux.
- Tener un dominio apuntando a la IP del servidor.
- Tener un certificado SSL para ese dominio.

## Los pasos de instalación son los siguientes:
1. Instalar git
2. Instalar docker
3. Instalar docker compose
4. Clonar el proyecto en el lugar de preferencia
5. Navegar a la carpeta del proyecto y crear un directorio `media`
6. Crear un directorio `certs`
    - En ese directorio, copiar los certificados para el dominio
        - `dominio.cer` renombrar a `certificate.cer`
        - `dominio.key` renombrar a `private.key`
        - copiar `fullchain.cer`
7. Crear un directorio `keys` 
    - Crear un par de clave pública y privada dentro de ese directorio. Se utilizarán para firmar los requests de activitypub.
    - Ambos pasos se realizan con este comando: `mkdir -p keys && openssl genpkey -algorithm RSA -out keys/private.pem -pkeyopt rsa_keygen_bits:2048 && openssl rsa -in keys/private.pem -pubout -out keys/public.pem && chmod 600 keys/private.pem && chmod 644 keys/public.pem && echo "Se han creado las claves satisfactoriamente. Clave pública:" && cat keys/public.pem`
8. Dar permiso de ejecucion a [`entrypoint.sh`](http://entrypoint.sh) con el comando `chmod +x entrypoint.sh`
9. Correr `docker-compose -f docker-compose-prod.yml up --build` o `docker compose -f docker-compose-prod.yml up --build` dependiendo de la versión de docker compose que se tenga.
10. Ir al panel de control, configurar el dominio. Por ahora funcionará solamente una instalación por dominio.
    1. Pegar la clave pública que se generó en el paso 4.

## Para el desarrollo local
1. Clonar el proyecto
2. Levantar el servidor de desarrollo con `python3 manage.py runserver 0.0.0.0:8080` o `python manage.py runserver 0.0.0.0:8080` dependiendo del sistema operativo.
3. Ir a `http://localhost:8000`

Se recomienda usar [venv](https://docs.python.org/3/library/venv.html) para el entorno de desarrollo.