#!/usr/bin/env sh
cd /tmp/mapnik

# OSM data
wget -q $PBF_URL -O import.osm.pbf
psql -U postgres -h $DB_HOST -d $DB_NAME -c 'CREATE EXTENSION hstore;'
osm2pgsql -s --create -U postgres -H $DB_HOST -d $DB_NAME import.osm.pbf

# load shapefiles for osm theme
/usr/share/openstreetmap-carto-common/get-shapefiles.sh

# App db
sudo -u postgres createdb -h $DB_HOST --encoding='utf-8' maps
sudo -u postgres psql -h $DB_HOST -d maps -c 'CREATE EXTENSION postgis'
