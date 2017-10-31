#!/usr/bin/env sh
cd /tmp/mapnik
wget -q $PBF_URL -O import.osm.pbf
psql -U postgres -h $DB_HOST -d $DB_NAME -c 'CREATE EXTENSION hstore;'
osm2pgsql -s --create -U postgres -H $DB_HOST -d $DB_NAME import.osm.pbf