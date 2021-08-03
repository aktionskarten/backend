import cairo
import mapnik
import contextlib
import json
import math
import geojson
import shutil
import requests
import math
import shapely
import pathlib
import numpy

from io import BytesIO
from flask import current_app
from pyproj import Transformer
from app.models import Map
from app.utils import strip, nearest_n, get_size


class SurfaceRenderer:
    def __init__(self, obj):
        # bbox in mercator
        proj = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')

        # use pyproj as mapnik is built without proj4 support
        wgs_to_merc = Transformer.from_crs(4326, 3857, always_xy=True)

        bbox_wgs84 = mapnik.Box2d(*obj['bbox'])

        south_west_merc = wgs_to_merc.transform(bbox_wgs84.minx, bbox_wgs84.miny)
        north_east_merc = wgs_to_merc.transform(bbox_wgs84.maxx, bbox_wgs84.maxy)
        bbox_merc = mapnik.Box2d(*south_west_merc, *north_east_merc)

        # instantiate mapnik (used as renderer) with web mercator projection
        width, height = get_size(bbox_merc.width(), bbox_merc.height())
        _map = mapnik.Map(width, height, '+init=epsg:3857')
        _map.zoom_to_box(bbox_merc)

        # render as well features outside of bbox as they may overlap (labels of
        # the grid itself)
        _map.buffer_size = 10

        self._map = _map
        self.obj = obj

        # add features and overlay layers+styles
        self._add_layer("styles/grid.xml", self.obj['grid'])
        self._add_layer("styles/features.xml", self._get_features())
        self._add_layer("styles/overlay.xml", self._get_overlay())

    @property
    def width(self):
        return self._map.width

    @property
    def height(self):
        return self._map.height

    def _add_layer(self, filename, datasources):
        if not isinstance(datasources, list):
            datasources = [datasources]

        idx = len(self._map.layers)
        current_dir = pathlib.Path(__file__).parent
        mapnik.load_map(self._map, str(current_dir / '..' / filename))

        for ds in datasources:
            data = mapnik.Datasource(type='geojson', inline=json.dumps(ds))
            self._map.layers[idx].datasource = data
            idx += 1


    def _get_features(self):
        # add all features (as features are rendered on top of each other in the
        # order we provide it to mapnik, make sure markers are on top)
        features = []
        if len(self.obj['features']) > 0:
            types = ['GeometryCollection', 'Polygon', 'LineString', 'Point']
            getter = lambda x: types.index(x['geometry']['type'])
            features = sorted([strip(f) for f in self.obj['features']], key=getter)
        return geojson.FeatureCollection(features)

    def _get_overlay(self):
        from app.grid import scalebar_for_bbox

        scalebar = scalebar_for_bbox(*self.obj['bbox'])
        collection_scalebar = geojson.FeatureCollection(scalebar)

        # copyright (in mercator projection)
        bbox = self._map.envelope()
        geometry = geojson.Point((bbox.maxx, bbox.miny))
        properties = {'text': 'Tiles © OpenMapTiles © OSM contributors, CC-BY-SA'}
        feature = geojson.Feature(geometry=geometry, properties=properties)
        collection_copyright = geojson.FeatureCollection([feature])

        return [collection_scalebar, collection_copyright]

    def _get_background(self):
        bbox = ','.join(str(x) for x in self.obj['bbox'])
        renderer_url = current_app.config['MAP_RENDERER'][self.obj['theme']]
        url = renderer_url.format(bbox, self.width, self.height)
        response = requests.get(url, stream=True)
        if (response.status_code != 200):
            return None
        return cairo.ImageSurface.create_from_png(response.raw)

    def render(self, mimetype='image/png', scale=1):
        # render our map
        surface_features = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)
        mapnik.render(self._map, surface_features)

        # merge map background and the map itself
        width, height = [int(n*scale) for n in [self.width, self.height]]
        surface_merged = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        merger = SurfaceMerger(surface_merged)
        merger.add_surface(self._get_background())
        merger.add_surface(surface_features)

        return merger.write(mimetype)


class SurfaceMerger:
    def __init__(self, surface):
        self.ctx = cairo.Context(surface)

    @contextlib.contextmanager
    def scoped(self):
        self.ctx.save()
        yield
        self.ctx.restore()

    @property
    def width(self):
        return self.ctx.get_target().get_width()

    @property
    def height(self):
        return self.ctx.get_target().get_height()

    def add_surfaces(self, surfaces):
        for surface in surfaces:
            self.add_surface(surface)

    def add_surface(self, surface, alpha=None):
        with self.scoped():
            scale_x = self.width/surface.get_width()
            scale_y = self.height/surface.get_height()
            self.ctx.scale(scale_x, scale_y)
            self.ctx.set_source_surface(surface)

            if alpha:
                self.ctx.paint_with_alpha(alpha)
            else:
                self.ctx.paint()

    def write(self, mimetype='image/png', f=None):
        if f is None:
            f = BytesIO()

        if mimetype == 'application/pdf':
            surface = cairo.PDFSurface(f, self.width, self.height)
            ctx = cairo.Context(surface)
            ctx.set_source_surface(self.ctx.get_target())
            ctx.paint()
            surface.finish()
        else:
            self.ctx.get_target().write_to_png(f)
        f.seek(0)
        return f

