#!/bin/sh

while ! pg_isready -h ${POSTGRES_HOST} > /dev/null 2> /dev/null; do
    echo "Connecting to ${POSTGRES_HOST} Failed"
    sleep 1
done

flask db upgrade

python -m pytest -s tests/
