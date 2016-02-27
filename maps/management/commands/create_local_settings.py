# -*- coding: utf-8 -*-
"""
helper to create local_settings.py for production
"""

from os import path
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

def get_secret_key():
    """
    Create a random secret key.

    Taken from the Django project.
    """
    chars = u'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    return get_random_string(50, chars)


class Command(BaseCommand):
    help = 'create local settings for production'

    def add_arguments(self, parser):
        parser.add_argument('--hosts', nargs='+', type=str)
        parser.add_argument('--cors', nargs='+', type=str)

    def handle(self, *args, **options):
        if not options['hosts']:
            self.stdout.write("No ALLOWED_HOSTS will be set!")

        if not options['cors']:
            self.stdout.write("CORSE_WHITELIST will be empty!")

        # get path for local_settings.py
        settings_local_dir = path.dirname(__file__)+'/../../../'
        settings_local_path = settings_local_dir + u'local_settings.py'

        if path.isfile(settings_local_path):
            self.stdout.write("local_settings.py already exists!")
            self.stdout.write("Please delete it manually then rerun the command.")
            return

        settings_file = open(settings_local_path, 'w')

        # create new secret key
        settings_file.write(u'SECRET_KEY = "' + get_secret_key() + u'"\n\n')

        # set hosts where backend runs
        settings_file.write(u'DEBUG = False\n\n')
        settings_file.write(u'ALLOWED_HOSTS = [\n')
        for host in options['hosts']:
            settings_file.write(u'    \'' + host + u'\',\n')
        settings_file.write(u']\n\n')

        # set cors whitelist (where the frontend resides)
        settings_file.write(u'CORS_ORIGIN_WHITELIST = (\n')
        for domain in options['cors']:
            settings_file.write(u'    "' + domain + u'",\n')
        settings_file.write(u')\n\n')
        settings_file.write(u'CORS_ORIGIN_ALLOW_ALL = False\n')

        settings_file.close()

        self.stdout.write("local_settings successfully created.")

