#!/usr/bin/env bash

echo "Init postgres for aktionskarten"
python postgres.py createuser --user maps --password maps
python postgres.py initdb --owner maps maps

echo "Init osm for aktionskarten"
python osm.py initdb --user maps --password maps --name osm
python osm.py import-dump --name osm /source/data/kotti-latest.osm.pbf
