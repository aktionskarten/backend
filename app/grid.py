import numpy
import geojson
import json
from string import ascii_uppercase
from pprint import pprint
import itertools

GRID_STYLES = [
    ('red', [("#000", "#fff"), ('#F00', '#000')]),
    ('black', [("#000", "#fff")]),
    ('green', [("#000", "#fff"), ('#00ba60', '#000')]),
    ('violet', [("#000", "#fff"), ('#8A2BE2', '#fff')]),
    ('blue', [("#000", "#fff"), ('#00b1f0', '#fff')]),
    ('labels_only', [('#000',)])
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
    features = []
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
    features.append(feature)

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
            features.append(feature)

    # grid corner points
    for geometry in grid_corners_for_bbox(x_min, y_min, x_max, y_max):
        properties = {
            'lineCap': 'square',
            'color': style[0][0]
        }
        feature = geojson.Feature(geometry=geometry, properties=properties)
        features.append(feature)

    return geojson.FeatureCollection(features)
