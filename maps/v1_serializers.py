# -*- coding: utf-8 -*-
"""
Serializers define the API representation
"""

from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework.serializers import ModelSerializer
from maps.models import Map, Feature


class MapSerializer(GeoFeatureModelSerializer):
    """
    serializer for Map Class
    """
    class Meta:
        model = Map
        geo_field = 'bbox'
        fields = ('name', 'bbox', 'public', 'editable')
        auto_bbox = True


class MapListSerializer(ModelSerializer):
    """
    serializer for List of Map Class
    """
    class Meta:
        model = Map
        fields = ('url', 'name')
        read_only_fields = ('url',)


class FeatureSerializer(GeoFeatureModelSerializer):
    """
    serializer for Feature class
    """
    class Meta:
        model = Feature
        geo_field = 'geo'
        fields = ('geo', 'map', 'id')
