# aktionskarten-backend

REST API for aktionskarten-frontend.

Install dependencies

  $ pacman -S libspatialite
  $ virtualenv env
  $ . env/bin/activate
  $ pip install -r requirements.txt


Start Server

  $ python app.py runserver


API Usage

  $ curl -i http://localhost:5000/maps/foosajdlkasd
  HTTP/1.0 200 OK
  Content-Type: application/json
  Content-Length: 31
  Server: Werkzeug/0.10.4 Python/2.7.10
  Date: Sat, 31 Oct 2015 15:26:13 GMT

  {
      "name": "foosajdlkasd"
  }
