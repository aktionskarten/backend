#!/bin/sh
cd /source

flask postgres init
flask osm init

flask run --with-threads --no-reload --host=0.0.0.0
