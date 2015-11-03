# -*- coding: utf-8 -*-
import re
from shapely.geometry.polygon import Polygon


def parse_bbox_string(bbox_string):
    """
    :param bbox_string: BBox defined in string should be: [(lat,lon), (lat,lon), (lat,lon), (lat,lon)]
    :return: Shaply Polygon
    """

    class NoBBoxException(Exception):
        pass

    # ensure string is well formatted
    pattern = re.compile('^\s*\[\s*(?P<tuple_list>.*)\s*\]\s*')
    match = pattern.match(bbox_string)
    if not match:
        raise NoBBoxException('Outer square brackets missing.')
    bbox_string = match.groupdict()['tuple_list']

    # ensure tuples with floats
    pattern = '\s*\(\s*(\d+\.\d+),\s*(\d+\.\d+)\s*\)'

    points = []
    for point in re.findall(pattern, bbox_string):
        points.append(
            (float(point[0]), float(point[1]))
        )

    # ensure exactly 4 points
    if len(points) != 4:
        raise NoBBoxException('Not 4 coordinates.')

    return Polygon(points)
