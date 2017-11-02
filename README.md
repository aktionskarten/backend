aktionskarten-backend
=====================

This repo contains the actual backend for aktionskarten-frontend. It's purpose
is to provide a datastore for GeoJSON data (for maps and geo features). Moreover
you can render map as PDF, SVG or PNG documents. It's written in python with
Flask and uses PostgreSQL+Postgis as database (through SQLAlchemy + GeoAlchemy),
mapnik for rendering and open street map data.

## Install

For installation see [INSTALL](INSTALL.md).

## API

aktionskarten-backend provides a RESTful API for storing the data related to the
maps created with aktionskarten-frontend. The following endpoints are
implemented:

* `/api/maps` - list of the public maps
* `/api/maps/<map_id>` - bounding box and properties
* `/api/maps/<map_id>/features` - features (circles, lines, markers, ...) of a map
* `/api/maps/<map_id>/grid` - grid in size of bbox of map

The backend furthermore supports rendering of maps with grid and features. You
can export a map the following ways:

* `/api/maps/<map_id>/export/pdf` - PDF Document
* `/api/maps/<map_id>/export/svg` - SVG Image
* `/api/maps/<map_id>/export/png` - PNG Image

### Example

#### Create a new map
```
$ curl -i -d '{
    "name":"ouchiii",
    "bbox": [13.419885635375975, 52.4833029277260650, 13.436880111694336, 52.48994074915979]
}' -H "Content-Type: application/json" -H "Accept: application/json" -X POST http://localhost:5000/api/maps
HTTP/1.0 200 OK
Content-Type: application/json
Access-Control-Allow-Origin: *
Content-Length: 170
Server: Werkzeug/0.12.2 Python/2.7.14
Date: Thu, 02 Nov 2017 11:06:26 GMT

{
  "bbox": [
    13.419885635375975, 
    52.483302927726065, 
    13.436880111694336, 
    52.48994074915979
  ], 
  "id": 3, 
  "name": "ouchiii", 
  "public": true
}
```

#### Create a new feature
```
$ curl -i -d '{
>     "type": "Polygon",
>     "properties": {"color":"red", "fillOpacity":0.8},
>     "coordinates": [
>       [
>         [
>           13.424252271652222,
>           52.487647678039096
>         ],
>         [
>           13.423839211463928,
>           52.48712502401718
>         ],
>         [
>           13.424976468086243,
>           52.48639656461409
>         ],
>         [
>           13.42603325843811,
>           52.48696495998076
>         ],
>         [
>           13.426585793495176,
>           52.48729162066096
>         ],
>         [
>           13.425502181053162,
>           52.48778487369072
>         ],
>         [
>           13.424252271652222,
>           52.487647678039096
>         ]
>       ]
>     ]
>   }' -H "Content-Type: application/json" -H "Accept: application/json" -X POST http://localhost:5000/api/maps/1/features
HTTP/1.0 200 OK
Content-Type: application/json
Access-Control-Allow-Origin: *
Content-Length: 762
Server: Werkzeug/0.12.2 Python/2.7.14
Date: Thu, 02 Nov 2017 11:08:01 GMT

{
  "geometry": {
    "coordinates": [
      [
        [
          13.424252271652222, 
          52.487647678039096
        ], 
        [
          13.423839211463928, 
          52.48712502401718
        ], 
        [
          13.424976468086243, 
          52.48639656461409
        ], 
        [
          13.42603325843811, 
          52.48696495998076
        ], 
        [
          13.426585793495176, 
          52.48729162066096
        ], 
        [
          13.425502181053162, 
          52.48778487369072
        ], 
        [
          13.424252271652222, 
          52.487647678039096
        ]
      ]
    ], 
    "type": "Polygon"
  }, 
  "properties": {
    "color": "red", 
    "fillOpacity": 0.8, 
    "id": 13
  }, 
  "type": "Feature"
}
```
