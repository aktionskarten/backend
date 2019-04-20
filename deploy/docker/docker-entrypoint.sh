#!/bin/sh
cd /source
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
/source/markers/generate_markers.sh
FLASK_DEBUG=1 FLASK_APP=src/app.py flask run --host=0.0.0.0
