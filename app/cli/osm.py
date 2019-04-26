import yaml
import click

from flask import current_app
from flask.cli import with_appcontext
from sh import wget, bzip2, osm2pgsql, createdb, psql,\
               dropuser as pgdropuser, dropdb as pgdropdb, python, ln,\
               ErrorReturnCode_1
from os import environ, makedirs, path
from os.path import abspath, join as pjoin
from path import Path

DATA_DIR = 'data'
OSM_CARTO_STYLE_FILE = 'style.xml'
OSM_DUMP_FILE = 'berlin-latest.osm.pbf'
OSM_DUMP_PATH = abspath(pjoin(DATA_DIR, OSM_DUMP_FILE))
OSM_DUMP_URL = 'http://download.geofabrik.de/europe/germany/'+OSM_DUMP_FILE


@click.group(help="osm related commands")
def osm():
    pass


@osm.command(help="Creates postgres database and extensions")
@with_appcontext
def initdb():
    environ['PGUSER'] = "postgres"

    click.echo("Try creating user. Ignore if already exists")
    try:
        user = current_app.config['OSM_DB_USER']
        pw = current_app.config['OSM_DB_PASS']
        psql("-c CREATE USER {} WITH PASSWORD '{}';".format(user, pw))
    except ErrorReturnCode_1:
        pass

    click.echo("Creating database")
    db_name = current_app.config['OSM_DB_NAME']
    createdb('-O'+user, db_name, encoding='utf-8')

    click.echo("Creating extensions")
    psql("-d"+db_name, "-c CREATE EXTENSION postgis; CREATE EXTENSION hstore;")


@osm.command(help="Drop postgres database")
@with_appcontext
def dropdb():
    environ['PGUSER'] = "postgres"
    click.echo("Dropping databases")
    pgdropdb(current_app.config['OSM_DB_NAME'])


@osm.command()
@with_appcontext
def generate_style():
    with Path("libs/openstreetmap-carto"):
        try:
            from sh import npx
            # check if npx is present
        except ImportError:
            click.echo("Please install npx")
            return -1


        click.echo("Updating credentials in project.mml")
        credentials = {
            'host': current_app.config['OSM_DB_HOST'],
            'dbname': current_app.config['OSM_DB_NAME'],
            'user': current_app.config['OSM_DB_USER'],
            'password': current_app.config['OSM_DB_PASS']
        }
        with open("project.mml", "r+") as f:
            project = yaml.safe_load(f)
            for layer in project['Layer']:
                layer['Datasource'].update(credentials)
            f.seek(0)
            f.write(yaml.dump(project))

        click.echo("Downloading shapefiles")
        python("scripts/get-shapefiles.py", "-s", _fg=True)

        from sh import npx
        click.echo("Generating style")
        npx("carto", "project.mml", "-f", OSM_CARTO_STYLE_FILE)


@osm.command()
def download_dump():
    makedirs(DATA_DIR, exist_ok=True)

    if not path.isfile(OSM_DUMP_PATH):
        click.echo("Downloading OSM dump")
        wget('-nc', '-P'+DATA_DIR, OSM_DUMP_URL, _fg=True)

    click.secho("OSM dump: "+ OSM_DUMP_PATH, fg="green")

@osm.command()
@with_appcontext
def import_dump():
    with Path("libs/openstreetmap-carto"):
        environ['PGPASSWORD'] = current_app.config['OSM_DB_PASS']
        host = current_app.config['OSM_DB_HOST']
        user = current_app.config['OSM_DB_USER']
        name = current_app.config['OSM_DB_NAME']
        osm2pgsql('-H'+host, '-U'+user, '-d'+name, '-G', '--hstore', OSM_DUMP_PATH,
                  style='openstreetmap-carto.style',
                  tag_transform_script='openstreetmap-carto.lua',
                  _fg=True)
    click.secho("Successfully imported : " + OSM_DUMP_FILE, fg="green")


@osm.command(help="Creates and imports osm database")
@click.pass_context
def init(ctx):
    ctx.invoke(initdb)
    ctx.invoke(download_dump)
    ctx.invoke(import_dump)
    ctx.invoke(generate_style)
