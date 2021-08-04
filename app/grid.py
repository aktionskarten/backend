import numpy
import geojson
import json
from string import ascii_uppercase
from pprint import pprint
import itertools

GRID_STYLES = [
    ('red', [("#000", "#fff"), ('#F00', '#000')]),
    ('green', [("#000", "#fff"), ('#00ba60', '#000')]),
    ('violet', [("#000", "#fff"), ('#8A2BE2', '#fff')]),
    ('pink', [("#000", "#fff"), ('#E04F9E', '#fff')]),
    ('blue', [("#000", "#fff"), ('#00b1f0', '#fff')]),
    ('only', [("#000", "#fff")]),
    ('labels_only', [('#000',)]),
    ('labels_only_white', [('#fff',)])
]

def steps(start, end, num, endpoint=True):
    if endpoint:
        num += 1
    numbers = numpy.linspace(start, end, num=num, endpoint=endpoint)
    start = numbers[0]
    for end in numbers[1:]:
        yield (start, end)
        start = end

def gen_lines(start, stop, start_fixed, end_fixed, num):
    for _,point in steps(start, stop, num, endpoint=False):
        _from = (point,start_fixed)
        to = (point,end_fixed)
        yield [_from,to]

def grid_lines_for_bbox(x_min, y_min, x_max, y_max, cells_x, cells_y):
    # top-down
    lines = list(gen_lines(x_min, x_max, y_min, y_max, cells_x))

    # left-right
    for _from,to in gen_lines(y_min, y_max, x_min, x_max, cells_y):
        lines.append([_from[::-1], to[::-1]]) # flip coordinates

    return geojson.MultiLineString(lines)

def grid_corners_for_bbox(x_min, y_min, x_max, y_max):
    points = ((x_min,y_min), (x_min,y_max), (x_max, y_min), (x_max, y_max))
    return (geojson.LineString([coord,coord]) for coord in points)

def gen_labels(start, end, fixed, num):
    for (start, end) in steps(start, end, num):
        _from = (start, fixed)
        to = (end, fixed)
        yield (_from, to)

def grid_labels_horizontally(start, end, y, num):
    labels = gen_labels(start, end, y, num)
    return [geojson.LineString(coords) for coords in labels]

def grid_labels_vertically(start, end, x, num):
    flipped = gen_labels(start, end, x, num)
    labels = ((_from[::-1], to[::-1]) for _from,to in flipped)
    return [geojson.LineString(coords) for coords in labels]

def grid_labels_for_bbox(x_min, y_min, x_max, y_max, cells_x, cells_y):
    labels = [
        (grid_labels_horizontally(x_min, x_max, y_min, cells_x), 'bottom'),
        (grid_labels_horizontally(x_min, x_max, y_max, cells_x), 'top'),
        (grid_labels_vertically(y_min, y_max, x_min, cells_y), 'left'),
        (grid_labels_vertically(y_min, y_max, x_max, cells_y), 'right')
    ]
    return labels
        
def grid_for_bbox(x_min, y_min, x_max, y_max, cells_x, cells_y, style_family=GRID_STYLES[0][0]):
    grid = []
    density = [cells_x, cells_y]
    style = dict(GRID_STYLES)[style_family]

    # grid lines
    properties = {
        'color': '#999',
        'opacity': 0.3,
        'weight': 2
    }
    coords = grid_lines_for_bbox(x_min, y_min, x_max, y_max, *density)
    feature = geojson.Feature(geometry=coords, properties=properties)
    grid.append(feature)

    # grid labels
    labels = grid_labels_for_bbox(x_min, y_min, x_max, y_max, cells_x, cells_y)
    for side, orientation in labels:
        size = len(side)
        for i,geometry in enumerate(side):
            use_numbers = orientation in ['left', 'right']
            properties = {
                'orientation': orientation,
                'lineCap': 'butt',
                'label': size-i if use_numbers else ascii_uppercase[i],
            }

            color_pair= style[i%len(style)]
            if len(color_pair)>1:
                properties['color'] = color_pair[0]
                properties['labelColor'] = color_pair[1]
            else:
                properties['labelColor'] = color_pair[0]

            feature = geojson.Feature(geometry=geometry, properties=properties)
            grid.append(feature)

    # grid corner points
    for geometry in grid_corners_for_bbox(x_min, y_min, x_max, y_max):
        properties = {
            'lineCap': 'square',
            'color': style[0][0]
        }
        feature = geojson.Feature(geometry=geometry, properties=properties)
        grid.append(feature)

    scalebar = scalebar_for_bbox(x_min, y_min, x_max, y_max)

    return geojson.FeatureCollection(grid+scalebar)


import mapnik
import math
from app.utils import get_size, nearest_n
from pyproj import Transformer

def scalebar_for_bbox(lng_min, lat_min, lng_max, lat_max, cells=5):
    south_east = mapnik.Coord(lng_min, lat_min)
    north_west = mapnik.Coord(lng_max, lat_max)

    # bbox in mercator
    wgs_to_merc = Transformer.from_crs(4326, 3857, always_xy=True)
    south_east_merc = mapnik.Coord(*wgs_to_merc.transform(lng_min, lat_min))
    north_west_merc = mapnik.Coord(*wgs_to_merc.transform(lng_max, lat_max))
    bbox_merc = mapnik.Box2d(south_east_merc, north_west_merc)

    # calculate distance of scalebar
    width, height = get_size(bbox_merc.width(), bbox_merc.height())
    _map = mapnik.Map(width, height, '+init=epsg:3857')
    _map.zoom_to_box(bbox_merc)
    pixel_per_meter = _map.scale()
    dist_in_m = nearest_n(max(_map.width, _map.height) * pixel_per_meter * 0.1)

    # calculate endpoint with padding-top and padding-right (so it is in our
    # grid)
    offset_x = bbox_merc.width() / 30
    offset_y = bbox_merc.height() / 30
    offset = mapnik.Coord(offset_x, offset_y)
    end_merc = north_west_merc - offset
    end = mapnik.Coord(*wgs_to_merc.transform(end_merc.x, end_merc.y, direction='INVERSE'))

    # calculate start as end-distance_in_m
    # see https://stackoverflow.com/questions/7477003/calculating-new-longitude-latitude-from-old-n-meters
    r_earth = 6378*1000.
    lng = end.x + ((-dist_in_m) / r_earth) * (180. / math.pi) / math.cos(end.y * math.pi/180.);
    start = mapnik.Coord(lng, end.y)

    # rectangles for scalebar (in black and white)
    scalebar = []
    geometries = grid_labels_horizontally(start.x, end.x, start.y, 5)
    for i, geometry in enumerate(geometries):
        properties = {
            'lineCap': 'butt',
            'color': '#fff' if i%2 else '#000'
        }
        scalebar.append(geojson.Feature(geometry=geometry, properties=properties))

    # add distance labels
    if dist_in_m >= 1000:
        dist = '{}km'.format(round(dist_in_m/1000.,1))
    else:
        dist = '{}m'.format(round(dist_in_m))

    for (coords, i) in [(start, 0), (end, dist)]:
        geometry = geojson.Point((coords.x, coords.y))
        properties = {'label': str(i)}
        scalebar.append(geojson.Feature(geometry=geometry, properties=properties))

    return scalebar
