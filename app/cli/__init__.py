import click
import sh

from flask import current_app
from flask.cli import with_appcontext
from os import path
from shutil import rmtree
from app.cli.pymapnik import pymapnik as pymapnik_cli
from app.cli.osm import osm as osm_cli
from app.cli.postgres import postgres as postgres_cli
from app.models import Map, db


@click.command(help="clear map directory")
@with_appcontext
def clear_maps():
    static_dir = current_app.static_folder
    rmtree(path.join(static_dir, 'maps'), ignore_errors=True)


@click.command(help="remove outdated maps from DB")
@with_appcontext
def remove_outdated_maps():
    outdated_maps = db.session.query(Map).filter_by(outdated=True).all()
    for m in outdated_maps:
        db.session.delete(m)
    db.session.commit()


@click.command(help="generate markers")
def gen_markers():
    sh.Command('styles/markers/generate_markers')(_fg=True)
