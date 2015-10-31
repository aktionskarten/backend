from flask import Flask
from flask_restful import Resource, Api
from flask.ext.script import Manager

app = Flask(__name__)
api = Api(app)
manager = Manager(app)

class Maps(Resource):
    def get(self, name):
        return { 'name': name }

api.add_resource(Maps, '/maps/<string:name>')

if __name__ == '__main__':
    manager.run()
