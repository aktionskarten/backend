import mapnik
import json
import cairo
import io

from flask import current_app
from geojson import FeatureCollection, Feature, Point
from utils import get_xml, strip


def add_legend(mapnik_map, _map):
    features = []
    box = mapnik_map.envelope()

    # add name, place and date
    point = Point((box.minx, box.maxy))
    features.append(Feature(geometry=point, properties={
        'name': _map['name'],
        'place': _map['place'],
        'date': _map['datetime']#strftime('%d.%m.%Y %H:%M')
        }))

    # add properties
    attributes = _map['attributes']
    if (attributes and len(attributes) > 0):
        cell_size = ((box.maxy - box.miny) / 11.)
        offset = cell_size / 3
        x = box.minx + offset
        y = box.miny + offset
        for i, (k, v) in enumerate(attributes):
            point = Point((x, y+offset*i))
            properties = {'key': k, 'value': v}
            features.append(Feature(geometry=point, properties=properties))

    # add osm copyright
    properties = {
        'type': 'copyright',
        'text': 'Tiles © OpenStreetMap contributers, CC-BY-SA'
    }
    point = Point((box.maxx, box.miny))
    features.append(Feature(geometry=point, properties=properties))

    # render them
    collection = json.dumps(FeatureCollection(features))
    xml_str = get_xml("styles/legend.xml").format(collection).encode()
    mapnik.load_map_from_string(mapnik_map, xml_str)


def render_map(_map, mimetype='application/pdf', scale=1):
    merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 \
                              +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m \
                              +nadgrids=@null +no_defs +over')
    longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 \
                                 +no_defs')
    transform = mapnik.ProjTransform(longlat, merc)

    bbox = mapnik.Box2d(*_map['bbox'])
    merc_bbox = transform.forward(bbox)

    # size is DINA4 @ 150dpi
    mapnik_map = mapnik.Map(1754, 1240)
    mapnik_map.zoom_to_box(merc_bbox)
    mapnik_map.buffer_size = 5

    # add osm data
    mapnik.load_map(mapnik_map, current_app.config['MAPNIK_OSM_XML'])

    # add grid
    data = _map['grid']
    xml_str = get_xml("styles/grid.xml").format(json.dumps(data)).encode()
    mapnik.load_map_from_string(mapnik_map, xml_str)

    # add all features (as features are rendered on top of each other in the
    # order we provide it to mapnik, make sure markers are on top)
    types = ['Polygon', 'LineString', 'Point']
    getter = lambda x: types.index(x['geometry']['type'])
    features = sorted([strip(f) for f in _map['features']], key=getter)
    collection = json.dumps(FeatureCollection(features))
    xml_str = get_xml("styles/features.xml").format(collection).encode()
    mapnik.load_map_from_string(mapnik_map, xml_str)

    # add legend
    add_legend(mapnik_map, _map)

    # export as in-memory file
    f = io.BytesIO()

    # create corresponding surface for mimetype
    if mimetype == 'image/svg+xml':
        surface = cairo.SVGSurface(f, mapnik_map.width, mapnik_map.height)
    elif mimetype == 'image/png':
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, mapnik_map.width,
                                     mapnik_map.height)
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
