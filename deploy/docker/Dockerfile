FROM ubuntu:18.04

ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN apt-get update && apt-get install -y \
    git \
    libmapnik3.0 \
    libmapnik-dev \
    python3-virtualenv \
    python3 \
    python3-dev \
    libboost-python-dev \
    libcairo2 \
    libcairo2-dev \
    postgresql-client \
    osm2pgsql \
    wget

RUN mkdir /source

WORKDIR /source

ENV VIRTUAL_ENV=/source/venv
RUN python3 -m virtualenv --python=/usr/bin/python3 $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt /source
RUN pip install -r /source/requirements.txt

COPY . /source
RUN python app/cli/pymapnik.py install

COPY .flaskenv /source/
RUN cd /source && flask gen-markers

CMD /source/deploy/docker/docker-entrypoint.sh
