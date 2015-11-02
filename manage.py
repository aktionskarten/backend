# -*- coding: utf-8 -*-

from flask.ext.script import Manager
from app import create_app

# create app
app = create_app()
manager = Manager(app)


@manager.command
def resetdb():
    # drop and create all tables
    from app.exts import db
    db.drop_all()
    db.create_all()

if __name__ == '__main__':
    manager.run()
