import click
import sh

from flask import current_app
from flask.cli import with_appcontext
from os import path
from shutil import rmtree
from app.cli.pymapnik import pymapnik as pymapnik_cli
from app.cli.osm import osm as osm_cli
from app.cli.postgres import postgres as postgres_cli


@click.command(help="clear map directory")
@with_appcontext
def clear_maps():
    static_dir = current_app.static_folder
    rmtree(path.join(static_dir, 'maps'), ignore_errors=True)


@click.command(help="generate markers")
def gen_markers():
    sh.Command('styles/markers/generate_markers')(_fg=True)
