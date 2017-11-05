#!/bin/sh
cd /source
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
export PYTHONPATH=${PYTHONPATH}:.
/source/markers/generate_markers.sh
FLASK_DEBUG=1 flask run --host=0.0.0.0
