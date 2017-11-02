#!/bin/sh
cd /source
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
export PYTHONPATH=${PYTHONPATH}:.
FLASK_APP=src/app.py FLASK_DEBUG=1 flask run --host=0.0.0.0
