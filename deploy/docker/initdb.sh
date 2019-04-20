#!/usr/bin/env sh
cd /tmp/mapnik

# OSM data
wget -q $PBF_URL -O import.osm.pbf
psql -U postgres -h $PGHOST -d $PGDATABASE -c 'CREATE EXTENSION hstore;CREATE EXTENSION postgis;'
osm2pgsql -s --create -U postgres -H $PGHOST -d $PGDATABASE import.osm.pbf