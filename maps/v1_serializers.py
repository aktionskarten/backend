# -*- coding: utf-8 -*-
"""
Serializers define the API representation

They render the Models to Json

"""

from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework.serializers import ModelSerializer

from maps.models import Map, Feature


class MapSerializer(GeoFeatureModelSerializer):
    """
    render Map to JSON

    with fields:
        id: String (name)
        bbox: [min_lat, min_lng, max_lat, max_lng]
        properties: {
            public: Boolean
            editable: Boolean
        }
        geometry: GeoJson for bbox

    """
    class Meta:
        model = Map
        geo_field = 'bbox'
        fields = ('name', 'bbox', 'public', 'editable')
        auto_bbox = True


class MapListSerializer(ModelSerializer):
    """
    render List of Maps to JSON

    with fields:
        name: String
        url: String (URL to Map on REST API)
    """
    class Meta:
        model = Map
        fields = ('url', 'name')
        read_only_fields = ('url',)


class FeatureSerializer(GeoFeatureModelSerializer):
    """
    render Feature to JSON
        id: int
        geometry: geoJSON for Feature
        properties : {
            map: String (name of Map the Feature belongs to)
        }
    """
    class Meta:
        model = Feature
        geo_field = 'geo'
        fields = ('geo', 'map', 'id', 'style')
