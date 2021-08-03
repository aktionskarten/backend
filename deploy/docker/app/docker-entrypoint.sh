#!/bin/sh

DB_HOST=db
REDIS_HOST=redis

while ! pg_isready -h ${DB_HOST} > /dev/null 2> /dev/null; do
    echo "Connecting to ${DB_HOST} Failed"
    sleep 1
done

rq worker --url "redis://${REDIS_HOST}" &

flask run --with-threads --no-reload --host=0.0.0.0
