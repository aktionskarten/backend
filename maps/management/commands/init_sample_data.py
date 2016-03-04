# -*- coding: utf-8 -*-
"""
helper to create sample data
"""

import json
import os
from django.core.management.base import BaseCommand

from maps.v1_serializers import MapSerializer, FeatureSerializer


class Command(BaseCommand):
    """
      Command to create sample data
    """
    help = 'create sample data'

    def handle(self, *args, **options):
        sample_data_dir = 'maps/management/sample_data/'
        os.chdir(sample_data_dir)
        os.chdir('maps')
        for file in os.listdir('.'):
            file_pointer = open(file)
            json_data = json.loads(file_pointer.read())
            map_serializer = MapSerializer(data=json_data)
            if map_serializer.is_valid():
                map_serializer.create(map_serializer.validated_data)
                self.stdout.write(file + u' imported')
            else:
                self.stdout.write(file + u' already exists')

            file_pointer.close()
        os.chdir('../features')
        for file in os.listdir('.'):
            self.stdout.write(file)
            file_pointer = open(file)
            json_data = json.loads(file_pointer.read())
            feature_serializer = FeatureSerializer(data=json_data)
            import ipdb; ipdb.set_trace();
            if feature_serializer.is_valid():
                feature_serializer.create(feature_serializer.validated_data)
                self.stdout.write(file + u' imported')
            else:
                self.stdout.write(file + u' was NOT READABLE')



