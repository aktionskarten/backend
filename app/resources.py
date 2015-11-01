# -*- coding: utf-8 -*-

from flask_restful import Resource

class Maps(Resource):
    def get(self, name):
        return { 'name': name }
