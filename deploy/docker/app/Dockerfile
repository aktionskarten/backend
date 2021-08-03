# vim:set ft=dockerfile:
FROM python:3.9-buster

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN set -ex; \
        apt-get update; \
        apt-get install -y \
                build-essential \
                git \
                libmapnik3.0 \
                libmapnik-dev \
                libboost-python-dev \
                libcairo2 \
                libcairo2-dev \
                postgresql-client \
                imagemagick \
                wget

WORKDIR /source

# python deps
COPY requirements.txt ./
RUN pip install -r /source/requirements.txt

# run pymapnik before source to create cache
COPY libs ./libs
COPY app/cli/pymapnik.py ./
RUN python pymapnik.py install

# copy source
COPY . ./

RUN flask gen-markers

COPY deploy/docker/app/docker-entrypoint.sh /usr/local/bin
CMD ["docker-entrypoint.sh"]
