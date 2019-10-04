from geojson import FeatureCollection, Feature, MultiLineString, LineString
from numpy import linspace
from string import ascii_uppercase

STYLES = {
    'red': (("#000000", "#ffffff"), ('#FF0000', '#000000')),
    'green': (("#000000", "#ffffff"), ('#00FF00', '#000000')),
    'violet': (("#000000", "#ffffff"), ('#8A2BE2', '#ffffff')),
    'blue': (("#ffffff", "#000000"), ('#00b1f0', '#ffffff'))
}

class Grid:

    def __init__(self, min_x, min_y, max_x, max_y, style='red'):
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y
        self.style = style

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
                'color': STYLES[self.style][i%2][0],
                'labelColor': STYLES[self.style][i%2][1]
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
                'color': STYLES[self.style][i%2][0],
                'labelColor': STYLES[self.style][i%2][1]
            }
            for j, geo in enumerate(geos):
                data['pos'] = 'RIGHT' if j % 2 else 'LEFT'
                features.append(Feature(geometry=geo, properties=data.copy()))

            start = end

        # grid
        coords = []
        for x in linspace(self.min_x, self.max_x, num=cells):  # columns
            coords.append([(x, self.min_y), (x, self.max_y)])

        for y in linspace(self.min_y, self.max_y, num=cells):  # rows
            coords.append([(self.min_x, y), (self.max_x, y)])

        prop = {
            'type': 'grid',
            'color': "#999",
            'opacity': 0.3,
            'weight': 2
        }
        grid = Feature(geometry=MultiLineString(coords), properties=prop)
        features.append(grid)

        return FeatureCollection(features)
