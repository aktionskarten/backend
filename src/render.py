from flask import Blueprint, send_file, current_app

from models import db, Map
import os
import mapnik
import json
import cairo
import io
from geojson import FeatureCollection, Feature, Point


render = Blueprint('Render', __name__)
SRC_PATH = os.path.dirname(__file__)

def get_xml(path):
    with open(path, 'r') as f:
        return f.read()


def add_legend(mapnik_map, data):
    features = []
    box = mapnik_map.envelope()
    offset = ((box.maxy - box.miny) / 12) / len(data)
    x = box.minx + 1.5*offset
    y = box.miny + offset
    for i, k in enumerate(data.keys()):
        point = Point((x, y+offset*(1+i)))
        properties = {'key': k, 'value': data[k]}
        features.append(Feature(geometry=point, properties=properties))

    collection = FeatureCollection(features)
    path = os.path.join(SRC_PATH, "maps-xml/legend.xml")
    xml_str = get_xml(path).format(json.dumps(collection)).encode()
    mapnik.load_map_from_string(mapnik_map, xml_str)


def render_map(_map, mimetype='application/pdf'):
    merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')
    longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
    transform = mapnik.ProjTransform(longlat, merc)

    bbox = mapnik.Box2d(*_map.bbox)
    merc_bbox = transform.forward(bbox)

    mapnik_map = mapnik.Map(int(merc_bbox.width()), int(merc_bbox.height()))
    mapnik_map.zoom_to_box(merc_bbox)
    mapnik_map.buffer_size = 5

    # add osm data
    mapnik.load_map(mapnik_map, current_app.config['MAPNIK_OSM_XML'])

    # add grid
    data = _map.grid
    path = os.path.join(SRC_PATH, "maps-xml/grid.xml")
    xml_str = get_xml(path).format(json.dumps(data)).encode()
    mapnik.load_map_from_string(mapnik_map, xml_str)

    # add all features
    features = FeatureCollection([f.to_dict() for f in _map.features])
    path = os.path.join(SRC_PATH, "maps-xml/features.xml")
    xml_str = get_xml(path).format(json.dumps(features)).encode()
    mapnik.load_map_from_string(mapnik_map, xml_str)

    # add legend
    add_legend(mapnik_map, _map.legend)

    # export as in-memory file
    f = io.BytesIO()

    if mimetype == 'image/svg+xml':
        surface = cairo.SVGSurface(f, mapnik_map.width, mapnik_map.height)
    elif mimetype == 'image/png':
        ratio = float(mapnik_map.height) / mapnik_map.width
        mapnik.height = 800
        mapnik.width = int(600*ratio)
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, mapnik_map.width,
                                     mapnik_map.height)
    else:
        surface = cairo.PDFSurface(f, mapnik_map.width, mapnik_map.height)

    mapnik.render(mapnik_map, surface)

    if mimetype == 'image/png':
        surface.write_to_png(f)

    surface.finish()
    f.seek(0)

    return f


@render.route('/api/maps/<int:map_id>/export/svg')
def map_export_svg(map_id):
    m = db.session.query(Map).get(map_id)
    mimetype = 'image/svg+xml'
    return send_file(render_map(m, mimetype),
                     attachment_filename='map.svg',
                     mimetype=mimetype)


@render.route('/api/maps/<int:map_id>/export/pdf')
def map_export_pdf(map_id):
    m = db.session.query(Map).get(map_id)
    mimetype = 'application/pdf'
    return send_file(render_map(m, mimetype),
                     attachment_filename='map.pdf',
                     mimetype=mimetype)


@render.route('/api/maps/<int:map_id>/export/png')
def map_export_png(map_id):
    m = db.session.query(Map).get(map_id)
    mimetype = 'image/png'
    return send_file(render_map(m, mimetype),
                     attachment_filename='map.png',
                     mimetype=mimetype)
