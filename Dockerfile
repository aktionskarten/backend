FROM ubuntu:17.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    git \
    libffi-dev \
    python3 \
    python3-setuptools \
    python3-pip \
    python3-mapnik \
    python3-shapely \
    python3-numpy \
    python3-wheel \
    python3-cairocffi \
    python3-mapnik \
    python3-shapely \
    python3-numpy \
    postgresql-client \
    osm2pgsql \
    openstreetmap-carto \
    wget \
    unifont \
    python-mapnik \
    python \
    sudo \
    unzip \
    imagemagick

RUN mkdir /source

WORKDIR /source

ADD requirements.txt /source

RUN pip3 install -r /source/requirements.txt

# load shapefiles for osm theme
WORKDIR /usr/share/openstreetmap-carto-common
RUN ./get-shapefiles.sh

ADD . /source

CMD /source/docker/docker-entrypoint.sh
