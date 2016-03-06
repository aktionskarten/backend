# aktionskarten-backend

[![Build Status](https://travis-ci.org/KartographischeAktion/aktionskarten-backend.svg?branch=master)](https://travis-ci.org/KartographischeAktion/aktionskarten-backend)

REST API for [aktionskarten-frontend](https://github.com/KartographischeAktion/aktionskarten-frontend).

It stores the points of interest, the bounding box, lines, multilines and areas for maps created with [aktionskarten-frontend](https://github.com/KartographischeAktion/aktionskarten-frontend).

### HowTo get started

#####Install dependencies
```
$ pacman -S libspatialite gdal
$ virtualenv env
$ . env/bin/activate
$ pip install -r requirements.txt
```

#####Init database & after every update
```
$ python manage.py makemigrations maps
$ python manage.py migrate
```

#####Import sample data
Import json files from maps/management/sample_data/maps and maps/management/sample_data/features.
```
$ python manage.py init_sample_data
```

#####Start tests
```
$ nosetests
$ pylint actionmaps_backend maps manage.py --load-plugins pylint_django
```

#####Start Server
```
$ python manage.py runserver
```
[aktionskarten-frontend](https://github.com/KartographischeAktion/aktionskarten-frontend) tries to reach the backend on port 8080. To run aktionskarten-backend on this port run:
```
$ python manage.py runserver 0.0.0.0:8080
```

#####API Usage
[aktionskarten-backend](https://github.com/KartographischeAktion/aktionskarten-backend) provides a RESTful API for storing the data related to the maps created with [aktionskarten-frontend](https://github.com/KartographischeAktion/aktionskarten-frontend).<br>


* <host>/api/v1/maps/ - list of the public maps
* <host>/api/v1/maps/ \<map_name\>/ - bounding box and properties of the map
* <host>/api/v1/maps/\<map_name\>/features/ - features (circles, lines, markers, ...) of the map

```
$ curl -i http://localhost:8080/api/v1/maps/Rigaer/
HTTP/1.0 200 OK
Date: Sun, 06 Mar 2016 20:24:51 GMT
Server: WSGIServer/0.2 CPython/3.5.1
Allow: GET, PUT, PATCH, DELETE, HEAD, OPTIONS
Vary: Accept, Cookie
Content-Type: application/json
X-Frame-Options: SAMEORIGIN

{"id":"Rigaer","type":"Feature","geometry":{"type":"Polygon","coordinates":[[[13.44439,52.504833],[13.44439,52.521156],[13.476233,52.521156],[13.476233,52.504833],[13.44439,52.504833]]]},"bbox":[13.44439,52.504833,13.476233,52.521156],"properties":{"public":true,"editable":true}}

$ curl -X POST -H "Content-Type: application/json" -d @maps/management/sample_data/maps/rigaer.json localhost:8080/api/v1/maps/
{"id":"Rigaer","type":"Feature","geometry":{"type":"Polygon","coordinates":[[[13.44439,52.504833],[13.44439,52.521156],[13.476233,52.521156],[13.476233,52.504833],[13.44439,52.504833]]]},"bbox":[13.44439,52.504833,13.476233,52.521156],"properties":{"public":true,"editable":true}}
```

### Production

#####Create settings_local
Creates a new SECRET_KEY and disables debugging.<br>
ALLOWED_HOSTS can be set with *--hosts* (IPs, domains the backend runs on).<br>
CORS_WHITELIST can be set with *--cors* (IPs, domains the frontend runs on).
```
$ python manage.py create_settings_local --cors localhost 127.0.0.1 --hosts localhost example.com 127.0.0.1
```

