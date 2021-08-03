# vim:set ft=dockerfile:
#FROM ubuntu:18.04
FROM debian:stretch-slim

ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN set -ex; \
        # see https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=866729
        mkdir -p /usr/share/man/man1; \
        mkdir -p /usr/share/man/man7; \
        apt-get update; \
        apt-get install -y \
                build-essential \
                git \
                libmapnik3.0 \
                libmapnik-dev \
                python3 \
                python3-dev \
                python3-virtualenv \
                libboost-python-dev \
                libcairo2 \
                libcairo2-dev \
                postgresql-client \
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

# run pymapnik before source to create cache
COPY libs ./libs
COPY app/cli/pymapnik.py ./
RUN python pymapnik.py install

# copy source
COPY . ./

# should be moved somehow before source copy to prevent run for each time
COPY .flaskenv ./
RUN flask gen-markers

COPY deploy/docker/app/docker-entrypoint.sh /usr/local/bin
CMD ["docker-entrypoint.sh"]
