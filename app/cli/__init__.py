import click

from flask import current_app
from flask.cli import with_appcontext
from os import path
from shutil import rmtree
from app.cli.mapnik import mapnik as mapnik_cli
from app.cli.osm import osm as osm_cli
from app.cli.postgres import postgres as postgres_cli


@click.command(help="clear map directory")
@with_appcontext
def clearmaps():
    static_dir = current_app.static_folder
    rmtree(path.join(static_dir, 'maps'), ignore_errors=True)