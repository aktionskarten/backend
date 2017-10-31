FROM ubuntu:17.04

RUN apt update && apt install -y \
    git \
    libffi-dev \
    python3 \
    python3-setuptools \
    python3-pip \
    python3-mapnik \
    postgresql-client \
    osm2pgsql \
    wget \
    unifont \
    python-mapnik \
    python \
    unzip

RUN mkdir -p /opt/
WORKDIR /opt/
RUN git clone https://github.com/openstreetmap/mapnik-stylesheets mapnik-stylesheets

WORKDIR /opt/mapnik-stylesheets

RUN wget -q http://tile.openstreetmap.org/world_boundaries-spherical.tgz && \
    wget -q http://tile.openstreetmap.org/processed_p.tar.bz2 && \
    wget -q http://tile.openstreetmap.org/shoreline_300.tar.bz2 &&\
    wget -q http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_populated_places.zip &&\
    wget -q http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/ne_110m_admin_0_boundary_lines_land.zip

RUN tar xzf world_boundaries-spherical.tgz &&\
    tar xjf processed_p.tar.bz2 -C world_boundaries &&\
    tar xjf shoreline_300.tar.bz2 -C world_boundaries &&\
    unzip -q ne_10m_populated_places.zip -d world_boundaries &&\
    unzip -q ne_110m_admin_0_boundary_lines_land.zip -d world_boundaries

VOLUME /opt/mapnik-stylesheets

RUN mkdir /source

WORKDIR /source

ADD requirements.txt /source

RUN pip3 install -r /source/requirements.txt

ADD . /source

CMD /source/docker/docker-entrypoint.sh