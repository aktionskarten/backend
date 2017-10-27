from geojson import FeatureCollection, Feature, MultiLineString, LineString
from numpy import linspace
from string import ascii_uppercase


class Grid:

    def __init__(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

    def generate(self, cells):
        grid = self.generate_grid(cells)
        labels = self.generate_labels(cells)
        return FeatureCollection([grid] + labels)

    def generate_grid(self, cells):
        coords = []

        # columns
        for x in linspace(self.min_x, self.max_x, num=cells):
            coords.append([(x, self.min_y), (x, self.max_y)])

        # rows
        for y in linspace(self.min_y, self.max_y, num=cells):
            coords.append([(self.min_x, y), (self.max_x, y)])

        prop = {
            'type': 'grid',
            'color': "#999",
            'opacity': 0.3,
            'weight': 2
        }
        return Feature(geometry=MultiLineString(coords), properties=prop)

    def generate_labels(self, cells):
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
        print(entries)
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

        return features
