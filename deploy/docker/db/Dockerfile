# based on debian:stretch-slim
FROM postgis/postgis:13-3.1-alpine

RUN apk add py-virtualenv

WORKDIR /source

# python virtual environment
ENV VIRTUAL_ENV=/source/venv
RUN python3 -m virtualenv --python=/usr/bin/python3 $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# python deps
COPY requirements.txt ./
RUN pip install -r /source/requirements.txt

# cli scripts
COPY libs /source/libs
RUN chown -R postgres:postgres /source/libs
COPY app/cli/* ./

# db init script (run on startup)
COPY deploy/docker/db/aktionskarten.sh /docker-entrypoint-initdb.d/z-aktionskarten.sh
