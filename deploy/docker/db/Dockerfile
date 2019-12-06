# based on debian:stretch-slim
FROM mdillon/postgis:10

RUN set -ex; \
        # see https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=866729
        mkdir -p /usr/share/man/man1; \
        mkdir -p /usr/share/man/man7; \
        apt-get update; \
        apt-get install -y \
                build-essential \
                python3 \
                python3-dev \
                python3-virtualenv \
                libboost-python-dev \
                libcairo2 \
                libcairo2-dev \
                osm2pgsql \
                imagemagick \
                wget

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

# osm data
RUN install -o postgres -d /source/data
COPY data/kotti-latest.osm.pbf /source/data/kotti-latest.osm.pbf

# db init script (run on startup)
COPY deploy/docker/db/aktionskarten.sh /docker-entrypoint-initdb.d/z-aktionskarten.sh
