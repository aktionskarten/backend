# -*- coding: utf-8 -*-
# Serializers define the API representation.

from rest_framework import serializers
from maps.models import Map, Feature
from maps.utils import parse_bbox_string, get_bbox_string


class MapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Map
        fields = ('name', 'bbox', 'public', 'editable')

    def create(self, validated_data):
        validated_data['bbox'] = parse_bbox_string(validated_data['bbox'])
        return super(MapSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        validated_data['bbox'] = parse_bbox_string(validated_data['bbox'])
        return super(MapSerializer, self).update(instance, validated_data)

    def to_representation(self, instance):
        response = super(MapSerializer, self).to_representation(instance)
        response['bbox'] = get_bbox_string(instance.bbox)
        return response


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ('geo', 'map', 'id')

    def to_representation(self, instance):
        response = super(FeatureSerializer, self).to_representation(instance)
        response['geo'] = instance.geo.json
        return response
