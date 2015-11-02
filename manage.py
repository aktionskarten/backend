# -*- coding: utf-8 -*-

from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from app import create_app
from app.exts import db

# create app
app = create_app()
manager = Manager(app)
migrate = Migrate(app, db)

# add manager scripts
manager.add_command('db', MigrateCommand)

@manager.command
def resetdb():
    # drop and create all tables
    from app.exts import db
    db.drop_all()
    db.create_all()

if __name__ == '__main__':
    manager.run()
