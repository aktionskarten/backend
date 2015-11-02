# -*- coding: utf-8 -*-

from flask import request
from flask_restful import Resource


class Maps(Resource):

    def get(self, name):
        return { 'name': name }
    def post(self, name):
        bbox = request.form['bbox']

        public = request.form['public']
        editable = request.form['editable']

    def put(self, name):
        bbox = request.form['bbox']
        public = request.form['public']
        editable = request.form['editable']


