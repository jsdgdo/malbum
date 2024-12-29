#!/bin/bash

# Create media directories if they don't exist
mkdir -p /code/media/fotos
mkdir -p /code/media/profile_pics
mkdir -p /code/staticfiles

# Ensure database directory is writable
touch /code/db.sqlite3
chmod 664 /code/db.sqlite3
chmod 775 /code

# Collect static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate

# Start Apache (as www-data)
exec apache2ctl -D FOREGROUND