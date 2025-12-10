#! /bin/sh
echo $IS_DEVELOPMENT
if [ -z "$API_PORT" ]; then
  API_PORT=8000
fi
printenv
if [ "$IS_DEVELOPMENT" = "1" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.5
    done

    echo "PostgreSQL started"
    python /app/manage.py migrate
    python /app/manage.py createsuperuser --noinput
    python /app/manage.py collectstatic --no-input --clear
    django-admin compilemessages
    python /app/manage.py runserver 0.0.0.0:$API_PORT
else
    python /app/manage.py migrate
    python /app/manage.py createsuperuser --noinput
    django-admin compilemessages
    gunicorn --bind 0.0.0.0:$API_PORT --workers 2 --threads 8 --timeout 0 --max-requests 1000 --max-requests-jitter 50 wsgi:application
fi
exec "$@"
