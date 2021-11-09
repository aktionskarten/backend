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

flask db upgrade

rq worker --url "redis://${REDIS_HOST}" &

gunicorn --worker-class eventlet -w 1 "app:create_app()" --bind 0.0.0.0:5000
