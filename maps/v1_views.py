# -*- coding: utf-8 -*-
"""
ViewSets define the view behavior

The Models are matched to their respective Serializers

"""

from rest_framework import viewsets

from maps.models import Map, Feature
from maps.v1_serializers import MapSerializer, MapListSerializer, FeatureSerializer


class MapViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Maps

    use MapListSerializer for list of maps
    use MapSerializer for Map
    to render Maps to JSON
    """
    # pylint: disable=no-member
    queryset = Map.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return MapListSerializer
        return MapSerializer


class FeatureViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Features

    use FeatureSerializer to render Features to JSON
    """
    # pylint: disable=no-member
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer

    def get_queryset(self):
        qs = super(FeatureViewSet, self).get_queryset()
        map_name = self.kwargs.get('map_name', '')
        return qs.filter(map__name=map_name)
