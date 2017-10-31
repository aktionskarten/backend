#!/usr/bin/env sh
cd /opt/mapnik-stylesheets

# TODO: some hackyness
sed -i -e 's/unifont Medium/Unifont Medium/g' ./inc/fontset-settings.xml.inc.template

python2 generate_xml.py --dbname $DB_NAME --host $DB_HOST --user postgres --port 5432 --password '' osm.xml