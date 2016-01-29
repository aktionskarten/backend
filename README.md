# aktionskarten-backend

[![Build Status](https://travis-ci.org/KartographischeAktion/aktionskarten-backend.svg?branch=master)](https://travis-ci.org/KartographischeAktion/aktionskarten-backend)

REST API for aktionskarten-frontend.

### HowTo get started

Install dependencies
```
$ pacman -S libspatialite
$ virtualenv env
$ . env/bin/activate
$ pip install -r requirements.txt
```

Init database & after every update
```
  $ python manage.py makemigrations maps
  $ python manage.py migrate
```

Start tests
```
  $ nosetests
  $ pylint actionmaps_backend maps manage.py --load-plugins pylint_django
```

Start Server
```
  $ python manage.py runserver
```

API Usage
```
  $ curl -i http://localhost:5000/maps/foosajdlkasd
  HTTP/1.0 200 OK
  Content-Type: application/json
  Content-Length: 31
  Server: Werkzeug/0.10.4 Python/2.7.10
  Date: Sat, 31 Oct 2015 15:26:13 GMT

  {
      "name": "foosajdlkasd"
  }
```
