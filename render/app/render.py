import json
import cairo

from io import BytesIO
from mapnik import Map, Projection, ProjTransform, Box2d, load_map, \
                   load_map_from_string, render, register_fonts
from flask import current_app
from geojson import FeatureCollection, Feature, Point
from timeit import default_timer as timer
from app.utils import get_xml, strip


register_fonts('/usr/share/fonts')


class MapRenderer:
    """ Class for rendering maps through mapnik """
    def __init__(self, content):
        """ With MapRenderer you can render an aktionskarten map in different
            file formats like pdf, svg or png.

            Internally it uses mapnik and cairo to archieve this. A valid style
            has to be defined through `MAPNIK_OSM_XML`. Normally this a carto
            derived `style.xml`. In this file your datasource is specified. This
            can be for instance a postgres+postgis database with imported osm
            data.

            :param content: dict of map content
        """
        # Mapnik uses mercator as internal projection. Our data is encoded in
        # latlon. Therefor we need a transformer for coordindates from longlat
        # to mercator
        proj_merc = Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0\
                                +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m  \
                                +nadgrids=@null +no_defs +over')
        proj_longlat = Projection('+proj=longlat +ellps=WGS84 +datum=WGS84  \
                                   +no_defs')
        transformer = ProjTransform(proj_longlat, proj_merc)

        # our maps should be printable on a DIN A4 page with 150dpi
        self._map = Map(1754, 1240)
        bbox = transformer.forward(Box2d(*content['bbox']))
        self._map.zoom_to_box(bbox)
        self._map.buffer_size = 5

        start = timer()

        # add osm data (background)
        load_map(self._map, current_app.config['MAPNIK_OSM_XML'])

        mid = timer()

        self._add_grid(content['grid'])
        self._add_features(content['features'])
        self._add_legend(content['name'], content['place'], content['datetime'],
                        content['attributes'])

        end = timer()
        print("Map.init - OSM: ", mid - start)
        print("Map.init - Map: ", end - mid)
        print("Map.init - Total: ", end - start)

    def _add_legend(self, name, place, datetime, attributes):
        features = []
        box = self._map.envelope()

        # add name, place and date
        point = Point((box.minx, box.maxy))
        features.append(Feature(geometry=point, properties={
            'name': name,
            'place': place,
            'date': datetime#strftime('%d.%m.%Y %H:%M')
            }))

        # add properties
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
        load_map_from_string(self._map, xml_str)

    def _add_features(self, features):
        # add all features (as features are rendered on top of each other in the
        # order we provide it to mapnik, make sure markers are on top)
        types = ['Polygon', 'LineString', 'Point']
        getter = lambda x: types.index(x['geometry']['type'])
        entries = sorted([strip(f) for f in features], key=getter)
        collection = json.dumps(FeatureCollection(entries))
        xml_str = get_xml("styles/features.xml").format(collection).encode()
        load_map_from_string(self._map, xml_str)

    def _add_grid(self, grid):
        xml_str = get_xml("styles/grid.xml").format(json.dumps(grid)).encode()
        load_map_from_string(self._map, xml_str)

    def render(self, mimetype='application/pdf', scale=1):
        """
            Renders a map through mapnik and in cases uses cairo to export in
            different file types. By default as a single paged `pdf` but you can
            pick as well other mimetypes.

            Maps are rendered and returned as in-memory file :class:`io.ByteIO`.

            Depending on the bounding box of your map, this is a ressouce and
            time consuming process. For web applications you should outsource it
            for instance in a task queue.

            Through scale you can alter the size of the rendered output.
            Currently only `image/png` supports this parameter. Normally this is
            a value between 0 and 1. For instance for aktionskarten the
            following sizings are used:

            small
                0.5
            medium
                0.75
            large
                1

            :param mimetype: `image/svg+xml`, `image/png` or `image/pdf`
            :param scale: scale factor  for sizing
        """
        start = timer()

        # export is done as in-memory file
        f = BytesIO()

        # create corresponding surface for mimetype
        if mimetype == 'image/svg+xml':
            surface = cairo.SVGSurface(f, self._map.width, self._map.height)
            # limit svg version to at least 1.2 otherwise we end up with an
            # embedded image instead of vector data. See as well:
            # * github.com/mapnik/mapnik/pull/4029
            # * github.com/mapnik/mapnik/issues/3749
            surface.restrict_to_version(cairo.SVGVersion.VERSION_1_2)
        elif mimetype == 'image/png':
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self._map.width,
                                         self._map.height)
        else:
            surface = cairo.PDFSurface(f, self._map.width, self._map.height)

        # let mapnik render the actual map
        render(self._map, surface)

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
                width = int(self._map.width * scale)
                height = int(self._map.height * scale)
                surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
                ctx = cairo.Context(surface)
                ctx.set_source(pattern)
                ctx.paint()

            surface.write_to_png(f)
        else:
            surface.finish()

        f.seek(0)

        end = timer()
        print("Map.render: ", end - start)

        return f
