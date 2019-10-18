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
OSM_DUMP_URL_DEFAULT = 'http://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf'
OSM_DUMP_FILE_DEFAULT = OSM_DUMP_URL_DEFAULT.split('/')[-1]


def _get_osm_dump_path(dump_file):
    filename = dump_file.split('/')[-1]
    return abspath(pjoin(DATA_DIR, filename))


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

        click.echo("Generating style")
        try:
            # check if carto is already installed
            from sh import carto
            carto("project.mml", "-f", OSM_CARTO_STYLE_FILE)
        except ImportError:
            try:
                # if not try to install through npm/npx
                from sh import npx
                npx("carto", "project.mml", "-f", OSM_CARTO_STYLE_FILE)
            except ImportError:
                click.echo("Please install npx")


@osm.command()
@click.option('--url', default=OSM_DUMP_URL_DEFAULT)
def download_dump(url):
    makedirs(DATA_DIR, exist_ok=True)

    filename = url.split('/')[-1]
    osm_dump_path = _get_osm_dump_path(filename)
    if not path.isfile(osm_dump_path):
        click.echo("Downloading OSM dump")
        wget('-nc', '-P'+DATA_DIR, url, _fg=True)

    click.secho("OSM dump: " + filename, fg="green")

@osm.command()
@with_appcontext
@click.option('--path', default=OSM_DUMP_FILE_DEFAULT)
def import_dump(path):
    osm_dump_path = _get_osm_dump_path(path) if '/' not in path else path
    with Path("libs/openstreetmap-carto"):
        environ['PGPASSWORD'] = current_app.config['OSM_DB_PASS']
        host = current_app.config['OSM_DB_HOST']
        user = current_app.config['OSM_DB_USER']
        name = current_app.config['OSM_DB_NAME']
        osm2pgsql('-H'+host, '-U'+user, '-d'+name, '-G', '--hstore',
                  osm_dump_path,
                  style='openstreetmap-carto.style',
                  tag_transform_script='openstreetmap-carto.lua',
                  _fg=True)
    click.secho("Successfully imported : " + osm_dump_path, fg="green")


@osm.command(help="Creates and imports osm database")
@click.option('--url', default=OSM_DUMP_URL_DEFAULT)
@click.option('--path', default=None)
@click.pass_context
def init(ctx, url, path):
    ctx.invoke(initdb)
    if path:
        ctx.invoke(import_dump, path=path)
    else:
        ctx.invoke(download_dump, url=url)
        ctx.invoke(import_dump, path=url.split('/')[-1])
    ctx.invoke(generate_style)
