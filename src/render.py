import os
import mapnik
import json

# somesystems have a different cairo
try:
    import cairo
except:
    import cairocffi as cairo

import io
import mimetypes

from flask import Blueprint, send_file, current_app, jsonify
from models import db, Map
from geojson import FeatureCollection, Feature, Point
from hashlib import sha256

# somesystems have a different cairo
try:
    import cairo
except:
    import cairocffi as cairo



render = Blueprint('Render', __name__)


def get_xml(path):
    path_abs = os.path.join(os.path.dirname(__file__), path)
    with open(path_abs, 'r') as f:
        return f.read()


def add_legend(mapnik_map, _map):
    features = []
    box = mapnik_map.envelope()

    # add name, place and date
    point = Point((box.minx, box.maxy))
    features.append(Feature(geometry=point, properties={
        'name': _map.name,
        'place': _map.place,
        'date': _map.datetime.strftime('%d.%m.%Y %H:%M')
        }))

    # add properties
    if (_map.attributes and len(_map.attributes) > 0):
        cell_size = ((box.maxy - box.miny) / 11.)
        offset = cell_size / 3
        x = box.minx + offset
        y = box.miny + offset
        if (_map.attributes):
            for i, (k, v) in enumerate(_map.attributes):
                point = Point((x, y+offset*i))
                properties = {'key': k, 'value': v}
                features.append(Feature(geometry=point, properties=properties))

    collection = json.dumps(FeatureCollection(features))
    xml_str = get_xml("maps-xml/legend.xml").format(collection).encode()
    mapnik.load_map_from_string(mapnik_map, xml_str)


def strip(feature):
    props = feature['properties']
    # dashArray="1" results in Leaflet as a straight line but in mapnik as
    # strokes. In mapnik to render a straight line, you don't provide any
    # dashArray. To have the same render result, delete it here.
    if 'dashArray' in props and props['dashArray'] == "1":
        del props['dashArray']
    return feature


def render_map(_map, mimetype='application/pdf', scale=1):
    merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')
    longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
    transform = mapnik.ProjTransform(longlat, merc)

    bbox = mapnik.Box2d(*_map.bbox)
    merc_bbox = transform.forward(bbox)

    # size is DINA4 @ 150dpi
    mapnik_map = mapnik.Map(1754, 1240)
    mapnik_map.zoom_to_box(merc_bbox)
    mapnik_map.buffer_size = 5

    # add osm data
    mapnik.load_map(mapnik_map, current_app.config['MAPNIK_OSM_XML'])

    # add all features
    features = FeatureCollection([strip(f.to_dict()) for f in _map.features])
    xml_str = get_xml("maps-xml/features.xml").format(json.dumps(features)).encode()
    mapnik.load_map_from_string(mapnik_map, xml_str)

    # add grid
    data = _map.grid
    xml_str = get_xml("maps-xml/grid.xml").format(json.dumps(data)).encode()
    mapnik.load_map_from_string(mapnik_map, xml_str)


    # add legend
    add_legend(mapnik_map, _map)

    # export as in-memory file
    f = io.BytesIO()

    # create corresponding surface for mimetype
    if mimetype == 'image/svg+xml':
        surface = cairo.SVGSurface(f, mapnik_map.width, mapnik_map.height)
    elif mimetype == 'image/png':
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, mapnik_map.width, mapnik_map.height)
    else:
        surface = cairo.PDFSurface(f, mapnik_map.width, mapnik_map.height)

    # let mapnik render the actual map
    mapnik.render(mapnik_map, surface)

    # pngs can be in different sizes through a scaling factor
    if mimetype == 'image/png':
        if (scale != 1):
            # render first and then scale resulting image otherwise fonts
            # occurr in wrong sizes
            pattern = cairo.SurfacePattern(surface)
            scaler = cairo.Matrix()
            scaler.scale(1./scale, 1./scale)
            pattern.set_matrix(scaler)
            pattern.set_filter(cairo.FILTER_FAST)

            # apply scale and save as new image surface
            width = int(mapnik_map.width * scale)
            height = int(mapnik_map.height * scale)
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
            ctx = cairo.Context(surface)
            ctx.set_source(pattern)
            ctx.paint()

        surface.write_to_png(f)
    else:
        surface.finish()

    f.seek(0)
    return f


def send_map(map_id, extension, scale=1, suffix=None):
    m = Map.get(map_id)
    dirname = sha256(map_id.encode()).hexdigest()
    mimetype = mimetypes.types_map['.' + extension]

    if (suffix):
        filename = '{}_{}.{}'.format(map_id, suffix, extension)
    else:
        filename = '{}.{}'.format(map_id, extension)

    # for development you can disable caching of maps
    config = current_app.config
    if 'NO_MAP_CACHE' in config and config['NO_MAP_CACHE']:
        return send_file(render_map(m, mimetype, scale),
                         attachment_filename=filename,
                         mimetype=mimetype)

    static_path = current_app.static_folder
    path = os.path.join(static_path, 'maps', dirname, m.hash, filename)
    if not os.path.exists(path):
        basename = os.path.dirname(path)
        if not os.path.exists(basename):
            os.makedirs(basename)
        with open(path, 'wb') as f:
            f.write(render_map(m, mimetype, scale).read())

    return send_file(path,
                     attachment_filename=filename,
                     mimetype=mimetype)


@render.route('/api/maps/<string:map_id>/export/svg')
def map_export_svg(map_id):
    return send_map(map_id, 'svg')


@render.route('/api/maps/<string:map_id>/export/pdf')
def map_export_pdf(map_id):
    return send_map(map_id, 'pdf')


@render.route('/api/maps/<string:map_id>/export/png')
@render.route('/api/maps/<string:map_id>/export/png:<string:size>')
def map_export_png(map_id, size='large'):
    if size == 'large':
        scale = 1
    elif size == 'small':
        scale = 0.5
    else:
        size = 'medium'
        scale = 0.75

    return send_map(map_id, 'png', scale, size)


@render.route('/api/maps/<string:map_id>/export/geojson')
def map_export_geojson(map_id):
    m = Map.get(map_id)
    features = [f.to_dict() for f in m.features]
    return jsonify(FeatureCollection(features, properties=m.to_dict(False)))
