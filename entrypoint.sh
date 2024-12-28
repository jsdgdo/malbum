#!/bin/sh

# Create media directories if they don't exist
mkdir -p /code/media/fotos /code/media/profile_pics
chown -R www-data:www-data /code/media
chmod -R 775 /code/media

exec "$@"

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

exec "$@"