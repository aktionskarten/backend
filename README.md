aktionskarten renderer
=====================

This web rest service takes aktionskarten maps and renders them into different
file formats like PDF, PNG or SVG. It's written in python with help of flask,
mapnik and openstreetmap-carto. Rendereing is time and ressource intensive and
therefor it's not done in the webapp itself but through a task queue.

The renderer itself is not supposed to run publicly because it's missing
authentication functionality.

Install
-------

## Dependencies
At least postgres, postgis, mapnik, osm2pgsql and redis need to be installed. Do this
through your os package manager:

### Ubuntu

```
$ apt install XXX
```

### ArchLinux

You need to install osm2pgsql through AUR.

```
$ pacman -S postgresql postgis redis mapnik
```

## Renderer

```
$ git clone --recursive aktionskarten
$ python -m venv env
$ . env/bin/activate
$ pip instal -r requirements.txt
$ python cli.py init
$ flask run
```


Tests
-----

Tests are written with pytest. To run them do the following:

```
$ python -m pytest -s tests/
```


API
---

The following endpoints are implemented

* '/render/<string:file_type>' - POST
* '/status/<string:job_id>' - GET
* '/status/<string:map_id>/<string:version>/<string:file_type>' - GET
* '/download/<string:map_id>_<string:version>.<string:file_type>' - GET
* '/download/<string:map_id>.<string:file_type>' - GET
