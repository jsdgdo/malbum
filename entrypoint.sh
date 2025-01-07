#!/bin/bash

# Create media directories if they don't exist
mkdir -p /code/media/fotos
mkdir -p /code/media/profile_pics
mkdir -p /code/staticfiles

# Create database directory if it doesn't exist and set permissions
mkdir -p /code/data
mkdir -p /code/config
touch /code/data/db.sqlite3
touch /code/config/config.json
chmod 664 /code/data/db.sqlite3
chmod 664 /code/config/config.json
chmod 775 /code/data
chmod 775 /code/config

# Set proper ownership for files that need to be written by www-data
chown www-data:www-data /code/data/db.sqlite3
chown www-data:www-data /code/config/config.json
chown www-data:www-data /code/data
chown www-data:www-data /code/config

# Ensure Apache directories exist and have correct permissions
mkdir -p /var/run/apache2
mkdir -p /var/lock/apache2
mkdir -p /var/log/apache2
chown -R www-data:www-data /var/run/apache2
chown -R www-data:www-data /var/lock/apache2
chown -R www-data:www-data /var/log/apache2

# Collect static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate

# Debug: Show Apache version and modules
apache2 -v
apache2ctl -M

# Debug: Check Apache configuration
apache2ctl -t

# Debug: Show permissions of key directories
ls -la /var/run/apache2
ls -la /var/log/apache2

# Start Apache (as www-data)
exec apache2 -D FOREGROUND
