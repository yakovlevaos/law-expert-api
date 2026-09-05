#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec uwsgi --ini /deploy/uwsgi.ini
