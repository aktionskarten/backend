# -*- coding: utf-8 -*-
from rest_framework import viewsets

# ViewSets define the view behavior.
from maps.models import Map, Feature
from maps.v1_serializers import MapSerializer, FeatureSerializer


class MapViewSet(viewsets.ModelViewSet):
    queryset = Map.objects.all()
    serializer_class = MapSerializer


class FeatureViewSet(viewsets.ModelViewSet):
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer

    def get_queryset(self):
        qs = super(FeatureViewSet, self).get_queryset()
        map_name = self.kwargs.get('map_name', '')
        return qs.filter(map__name=map_name)
