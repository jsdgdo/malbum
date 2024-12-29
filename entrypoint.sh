#!/bin/bash

# Create media directories if they don't exist
mkdir -p /code/media/fotos
mkdir -p /code/media/profile_pics
mkdir -p /code/staticfiles

# Create database directory if it doesn't exist and set permissions
mkdir -p /code/data
touch /code/data/db.sqlite3
touch /code/config/config.json
chmod 664 /code/data/db.sqlite3
chmod 664 /code/config/config.json
chmod 775 /code/data
chmod 775 /code/config

# Collect static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate

# Start Apache (as www-data)
exec apache2ctl -D FOREGROUND