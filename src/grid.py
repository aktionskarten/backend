from geojson import FeatureCollection, Feature, MultiLineString, LineString
from numpy import linspace
from string import ascii_uppercase


class Grid:

    def __init__(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

    def generate(self, cells = 12):
        features = []

        # top and bottom labels
        entries = linspace(self.min_x, self.max_x, num=cells)
        start = entries[0]
        for i, end in enumerate(entries[1:]):
            geos = [
                LineString([(start, self.min_y), (end, self.min_y)]),  # bottom
                LineString([(start, self.max_y), (end, self.max_y)]),  # top
            ]

            data = {
                'label': ascii_uppercase[i],
                'color': "#000000" if i % 2 else "#FF0000",
                'labelColor': "#FFFFFF" if i % 2 else "#000000"
            }
            for j, geo in enumerate(geos):
                data['pos'] = 'TOP' if j % 2 else 'BOTTOM'
                features.append(Feature(geometry=geo, properties=data.copy()))

            start = end

        # left and right labels
        entries = linspace(self.min_y, self.max_y, num=cells)
        start = entries[0]
        for i, end in enumerate(entries[1:]):
            geos = [
                LineString([(self.min_x, start), (self.min_x, end)]),  # left
                LineString([(self.max_x, start), (self.max_x, end)])   # right
            ]

            data = {
                'label': len(entries) - i - 1,
                'color': "#000000" if i % 2 else "#FF0000",
                'labelColor': "#FFFFFF" if i % 2 else "#000000"
            }
            for j, geo in enumerate(geos):
                data['pos'] = 'RIGHT' if j % 2 else 'LEFT'
                features.append(Feature(geometry=geo, properties=data.copy()))

            start = end

        return FeatureCollection(features)
