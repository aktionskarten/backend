#!/bin/sh

# TODO replace with .env? remove?
cat <<EOT >> .flaskenv
FLASK_APP=app
FLASK_ENV=production
EOT

while ! pg_isready -h ${POSTGRES_HOST} > /dev/null 2> /dev/null; do
    echo "Connecting to ${POSTGRES_HOST} Failed"
    sleep 1
done

rq worker --url "redis://${REDIS_HOST}" &

#flask run --with-threads --no-reload --host=0.0.0.0
gunicorn --worker-class eventlet -w 1 "app:create_app()"
