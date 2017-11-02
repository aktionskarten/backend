aktionskarten-backend
=====================

This repo contains the actual backend for aktionskarten-frontend. It's purpose
is to provide a datastore for GeoJSON data (for maps and geo features). Moreover
you can render map as PDF, SVG or PNG documents. It's written in python with
Flask and uses PostgreSQL+Postgis as database (through SQLAlchemy + GeoAlchemy),
mapnik for rendering and open street map data.

## Install

For installation see [INSTALL](INSTALL.md).
