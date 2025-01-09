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

# Debug: Show mod_wsgi location
echo "Looking for mod_wsgi.so:"
find / -name 'mod_wsgi.so' 2>/dev/null

# Debug: Show loaded modules
apache2ctl -M

# Debug: Show Apache error log if it exists
echo "Apache error log contents:"
cat /var/log/apache2/error.log

# Debug: Test Apache configuration
echo "Testing Apache configuration:"
apache2ctl -t

# Set environment variables for Apache
export APACHE_RUN_USER=www-data
export APACHE_RUN_GROUP=www-data
export APACHE_RUN_DIR=/var/run/apache2
export APACHE_LOG_DIR=/var/log/apache2
export APACHE_LOCK_DIR=/var/lock/apache2
export APACHE_PID_FILE=/var/run/apache2/apache2.pid

echo "Starting Apache with debug info..."
exec apache2 -X -e debug -D FOREGROUND