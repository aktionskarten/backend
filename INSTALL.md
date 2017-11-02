# Install

### Ubuntu

You need to use 17.04 (if you don't want to compile some stuff on your own)
because 16.04 is missing cairo support and 17.10 contains non-working
python-mapnik.

Add user and set locale to utf-8 (needed for postgres template)
```
  update-locale LANG=en_US.UTF-8
  adduser gis
```

You can either run the backend with python or python3:

Install packages (python2)
```
  apt install python-virtualenv python-wheel python-cairocffi python-mapnik pyhton-shapely python-numpy git wget bzip2 osm2pgsql postgresql postgresql-9.6-postgis-scripts imagemagick
```

Install packages (python3)
```
  apt install python3-wheel python3-cairocffi python3-mapnik python3-venv python3-shapely python3-numpy git wget bzip2 osm2pgsql postgresql postgresql-9.6-postgis-scripts imagemagick
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

Import osm data
```
  wget http://download.geofabrik.de/europe/germany/berlin-latest.osm.bz2
  bzip2 -d berlin-latest.osm.bz2
  osm2pgsql -U gis -W -d gis berlin-latest.osm
```

Clone source
```
  git clone https://github.com/KartographischeAktion/aktionskarten-backend.git
  cd aktionskarten-backend
  git checkout rewrite-flask_mapnik
```

Setup virtualenv

python3
```
  python3 -m venv --system-site-packages env
  . env/bin/activate
```

python2
```
  virtual--system-site-packages env2
  echo 'export FLASK_APP=src/app.py' >> env/bin/activate
  echo 'export FLASK_DEBUG=1' >> env/bin/activate
  . env2/bin/activate
```

Install dependencies and start app
```
  pip install -r requirements.txt
  markers/generate_markers.sh
  flask run
```


If you're not able to use Ubuntu 17.04, you need to build python-mapnik by
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

(go for python2 because py3cairo.h is missing otherwise)

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

Install carto to generate mapnik osm xml style:
```
  pacman -S npm
  npm install -g carto
  git clone https://github.com/gravitystorm/openstreetmap-carto.git
  cd openstreetmap-carto
  osm2pgsql -G --hstore --style openstreetmap-carto.style --tag-transform-script openstreetmap-carto.lua -d gis /tmp/berlin-latest.osm  
  psql -d gis -f indexes.sql
  scripts/get-shapefiles.py -s
  carto project.mml > osm.xml
```

Create virtualenv for python2
```
  virtualenv2 --system-site-packages env
  echo 'export FLASK_APP=src/app.py' >> env/bin/activate
  echo 'export FLASK_DEBUG=1' >> env/bin/activate
  . env/bin/activate
```

Compile python-mapnik
```
  pacman -S python2-cairocffi python2-cairo
  git clone https://github.com/mapnik/python-mapnik.git
  cd python-mapnik
  git checkout v3.0.x
  ln -s /usr/include/pycairo ../aktionskarten-backend/env/include/pycairo
  PYCAIRO=true python setup.py develop
  python setup.py install
```

Install backend
```
  git clone https://github.com/KartographischeAktion/aktionskarten-backend.git
  cd aktionskarten-backend
  pip install -r requirements.txt
  markers/generate_markers.sh
  flask run
```
