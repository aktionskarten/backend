# Install

### Ubuntu

Clone source
```
  git clone https://github.com/aktionskarten/backend.git
  cd backend
```

You need to use 18.04 (if you don't want to compile some stuff on your own)
because 16.04 is missing cairo support and 17.10 contains non-working
python-mapnik.

Set locale to utf-8 (needed for postgres template)
```
  update-locale LANG=en_US.UTF-8
```

Install packages (python3)
```
  apt install python3-wheel python3-cairocffi python3-mapnik python3-venv python3-shapely python3-numpy git wget bzip2 osm2pgsql postgresql postgresql-10-postgis-scripts imagemagick
```

Start postgres
```
  sudo systemctl enable postgresql
  sudo systemctl start postgresql
```

Create postgres user and database (enable postgis and hstore extensions)
```
  sudo -u postgres createuser -P gis
  sudo -u postgres createdb -O gis --encoding='utf-8' gis
  sudo -u postgres createdb -O gis --encoding='utf-8' maps
  sudo -u postgres psql -d gis -c 'CREATE EXTENSION postgis; CREATE EXTENSION hstore;'
  sudo -u postgres psql -d maps -c 'CREATE EXTENSION postgis'
```

Install osm style (style can be found in `/usr/share/openstreetmap-carto/style.xml`). Use `gis` as database.
```
  apt install openstreetmap-carto
```

To allow password auth for user `gis` from localhost, in
`/etc/postgresql/10/main/pg_hba.conf` add method `trust` to IPv4 local
connections (you need to be root in order to edit this file):
```
# IPv4 local connections:
host    all             all             127.0.0.1/32            trust
```

Since we created our own gis DB with new credentials, we need to locally update
the osm configs. First, create a local copy of the config and symlink the data:
```
mkdir openstreetmap-carto
cd openstreetmap-carto
cp /usr/share/openstreetmap-carto/style.xml .
ln -s /usr/share/openstreetmap-carto/symbols
ln -s /usr/share/openstreetmap-carto/data
```

Add gis user credentials to `style.xml`
```
sed -i  '/<Parameter name="dbname"><!\[CDATA\[gis\]\]><\/Parameter>/a <Parameter name="host"><!\[CDATA\[127.0.0.1\]\]><\/Parameter>\n<Parameter name="user"><!\[CDATA\[gis\]\]><\/Parameter>\n<Parameter name="password"><!\[CDATA\[gis\]\]><\/Parameter>' style.xml
```

Create a local `src/settings.py` and add following line to it:
```
MAPNIK_OSM_XML = "../openstreetmap-carto/style.xml"
```

Finally, export the local settings in your shell:
```
export SETTINGS=settings.py
```

Import osm data
```
  wget http://download.geofabrik.de/europe/germany/berlin-latest.osm.bz2
  bzip2 -d berlin-latest.osm.bz2
  osm2pgsql -U gis -W -d gis berlin-latest.osm
```

Setup virtualenv
```
  python3 -m venv --system-site-packages env
  . env/bin/activate
```

Install dependencies and start app
```
  pip install -r requirements.txt
  markers/generate_markers.sh
  cd src
  flask run
```


If you're not able to use Ubuntu 18.04, you need to build python-mapnik by
yourself:

```
  apt install python-dev python-cairocffi python-cairo libmapnik-dev python-cairo-dev libboost-python-dev
  git clone https://github.com/mapnik/python-mapnik.git
  cd python-mapnik
  git checkout v3.0.x
  ln -s /usr/include/pycairo ../aktionskarten-backend/env/include/pycairo
  PYCAIRO=true python setup.py develop
  python setup.py install
```

### ArchLinux

Add user and initialize postgres database.
```
  useradd -m -G wheel -s /bin/bash gis
  vim /etc/locale.gen
  echo 'LANG=en_US.UTF-8' > /etc/locale.conf
  locale-gen 
  pacman -S python-wheel python-cairocffi python-shapely python-numpy git wget bzip2 postgresql postgis sudo imagemagick
  su - postgres -c "initdb --locale en_US.UTF-8 -D '/var/lib/postgres/data'"
```

Install osm2pgsql from AUR
```
  wget -O PKGBUILD https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h=osm2pgsql-git
  makepkg -s
  pacman -U osm2pgsql-git-*.pkg.tar.xz
```

Start postgres
```
  sudo systemctl enable postgresql
  sudo systemctl start postgresql
```

Create postgres user and database (enable postgis and hstore extensions)
```
  sudo -u postgres createuser -P gis
  sudo -u postgres createdb -O gis --encoding='utf-8' gis
  sudo -u postgres createdb -O gis --encoding='utf-8' maps
  sudo -u postgres psql -d gis -c 'CREATE EXTENSION postgis; CREATE EXTENSION hstore;'
  sudo -u postgres psql -d maps -c 'CREATE EXTENSION postgis'
```

To allow password auth for user `gis` from localhost in
`/etc/postgresql/10/main/pg_hba.conf` add method `trust` to IPv4 local
connections:
```
# IPv4 local connections:
host    all             all             127.0.0.1/32            trust
```

Install carto to generate mapnik osm xml style:

Set the postgres user and password of the user in `project.mml`.
Default for both user and password is "gis".

```
  pacman -S npm
  npm install -g carto
  git clone https://github.com/gravitystorm/openstreetmap-carto.git
  cd openstreetmap-carto
  wget http://download.geofabrik.de/europe/germany/berlin-latest.osm.bz2
  bzip2 -d berlin-latest.osm.bz2
  osm2pgsql -U gis -W -G --hstore --style openstreetmap-carto.style --tag-transform-script openstreetmap-carto.lua -d gis berlin-latest.osm  
  sudo -u postgres psql -d gis -f indexes.sql
  scripts/get-shapefiles.py -s
  carto project.mml > osm.xml
```

Create virtualenv for python
```
  virtualenv --system-site-packages env
  echo 'export FLASK_APP=src/app.py' >> env/bin/activate
  echo 'export FLASK_DEBUG=1' >> env/bin/activate
  . env/bin/activate
```

Compile python-mapnik
```
  pacman -S python-cairocffi python-cairo
  git clone https://github.com/mapnik/python-mapnik.git
  cd python-mapnik
  git checkout v3.0.x
  ln -s /usr/include/pycairo ../backend/env/include/pycairo
  PYCAIRO=true python setup.py develop
  python setup.py install
```

Install backend
```
  git clone https://github.com/aktionskarten/backend.git
  cd backend
  pip install -r requirements.txt
  markers/generate_markers.sh
  flask run
```

