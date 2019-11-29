import yaml
import click

from flask import current_app
from flask.cli import with_appcontext
from sh import wget, bzip2, osm2pgsql, psql,\
               dropuser as pgdropuser, dropdb as pgdropdb, python, ln,\
               ErrorReturnCode_1
from os import environ, makedirs, path
from os.path import abspath, join as pjoin
from path import Path

# support standalone and as flask cli
try:
    from app.cli.utils import default_option
    from app.cli.postgres import create_user, create_db, drop_db
except ImportError:
    from utils import default_option
    from postgres import create_user, create_db, drop_db

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
@click.option('--user', default=default_option('OSM_DB_USER'))
@click.option('--password', default=default_option('OSM_DB_PASS'))
@click.option('--name', default=default_option('OSM_DB_NAME'))
def initdb(user, password, name):
    create_user(user, password)

    if not create_db(name, user):
        return False

    psql('-Upostgres', "-d"+name, "-c CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS hstore;")

    return True


@osm.command(help="Drop postgres database")
@click.argument('name', default=default_option('OSM_DB_NAME'))
def dropdb(name):
    click.echo("Dropping database: "+name)
    drop_db(name)


@osm.command()
@click.option('--host', default=default_option('OSM_DB_HOST'))
@click.option('--user', default=default_option('OSM_DB_USER'))
@click.option('--password', default=default_option('OSM_DB_PASS'))
@click.option('--name', default=default_option('OSM_DB_NAME'))
def generate_style(host, user, password, name):
    with Path("libs/openstreetmap-carto"):
        click.echo("Updating credentials in project.mml")
        credentials = {
            'host': host,
            'dbname': name,
            'user': user,
            'password': password
        }
        project = {}
        with open("project.mml", "r+") as f:
            project = yaml.safe_load(f)
            for layer in project['Layer']:
                try:
                    if layer['Datasource']['type'] == 'postgis':
                        layer['Datasource'].update(credentials)
                except KeyError:
                    pass
            f.seek(0)
            f.write(yaml.dump(project))
            f.truncate()

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
@click.argument('path', default=OSM_DUMP_FILE_DEFAULT)
@click.option('--host', default=default_option('OSM_DB_HOST'))
@click.option('--user', default=default_option('OSM_DB_USER'))
@click.option('--password', default=default_option('OSM_DB_PASS'))
@click.option('--name', default=default_option('OSM_DB_NAME'))
def import_dump(path, host, user, password, name):
    osm_dump_path = _get_osm_dump_path(path) if '/' not in path else path
    with Path("libs/openstreetmap-carto"):
        pgsql = ['-d'+name]
        if host:
            pgsql.append('-H'+host)
        if user:
            pgsql.append('-U'+user)
        if password:
            environ['PGPASSWORD'] = password
        osm2pgsql('-G', '--hstore', osm_dump_path, *pgsql,
                  style='openstreetmap-carto.style',
                  tag_transform_script='openstreetmap-carto.lua',
                  _fg=True)
    click.secho("Successfully imported : " + osm_dump_path, fg="green")


@osm.command(help="Creates and imports osm database")
@click.option('--url', default=OSM_DUMP_URL_DEFAULT)
@click.option('--path', default=None)
@click.pass_context
def init(ctx, url, path):
    if not ctx.invoke(initdb):
        click.echo("Already initialized")
        return
    if path:
        ctx.invoke(import_dump, path=path)
    else:
        ctx.invoke(download_dump, url=url)
        ctx.invoke(import_dump, path=url.split('/')[-1])
    ctx.invoke(generate_style)

if __name__ == '__main__':
    osm()
