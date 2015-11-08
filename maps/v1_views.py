# -*- coding: utf-8 -*-
from rest_framework import viewsets

# ViewSets define the view behavior.
from maps.models import Map
from maps.v1_serializers import MapSerializer


class MapViewSet(viewsets.ModelViewSet):
    queryset = Map.objects.public()
    serializer_class = MapSerializer
