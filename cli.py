import yaml
import click

from shutil import rmtree
from sh import wget, bzip2, osm2pgsql, npm, carto, createdb, psql, dropuser,\
               dropdb, python, ln
from os import environ, makedirs, path
from os.path import abspath, join as pjoin
from path import Path
from distutils.core import run_setup


DB_HOST = '127.0.0.1'
DB_USER = 'gis'
DB_PASS = 'gis'
DB_NAME = 'gis'
DATA_DIR = 'data'
OSM_CARTO_STYLE_FILE = 'style.xml'
OSM_DUMP_FILE_UNCOMPRESSED = 'berlin-latest.osm'
OSM_DUMP_PATH_UNCOMPRESSED = abspath(pjoin(DATA_DIR, OSM_DUMP_FILE_UNCOMPRESSED))
OSM_DUMP_FILE = OSM_DUMP_FILE_UNCOMPRESSED + '.bzip2'
OSM_DUMP_PATH = pjoin(DATA_DIR, OSM_DUMP_FILE)
OSM_DUMP_URL = 'http://download.geofabrik.de/europe/germany/'+OSM_DUMP_FILE


def mapnik_is_installed():
    try:
        import mapnik
        return mapnik.mapnik_version() > 0
    except ImportError:
        return False


def mapnik_install():
    if mapnik_is_installed():
        return

    environ['PYCAIRO'] = "true"
    with Path("libs/python-mapnik"):
        dist = run_setup('setup.py')
        dist.run_command('clean')
        dist.run_command('install')
    del environ['PYCAIRO']


@click.group(help="mapnik related commands")
def mapnik():
    pass


@mapnik.command()
def is_installed():
    if mapnik_is_installed():
        click.secho("Mapnik is installed and works!", fg='green')
    else:
        click.secho("Mapnik is missing!", fg='red')
        click.echo("Run 'mapnik install' do fix this")


@mapnik.command()
def install():
    mapnik_install()
    click.secho("Mapnik installed successfully!", fg='green')


@click.group(help="osm related commands")
def osm():
    pass


@osm.command()
def generate_style():
    with Path("libs/openstreetmap-carto"):
        click.echo("Installing carto")
        npm('install', 'carto')

        click.echo("Updating credentials in project.mml")
        credentials = {
            'host': DB_HOST,
            'dbname': DB_NAME,
            'user': DB_USER,
            'password': DB_PASS
        }
        with open("project.mml", "r+") as f:
            project = yaml.safe_load(f)
            for layer in project['Layer']:
                layer['Datasource'].update(credentials)
            f.seek(0)
            f.write(yaml.dump(project))

        click.echo("Downloading shapefiles")
        python("scripts/get-shapefiles.py", "-s")

        click.echo("Generating style")
        carto("project.mml", "-f", OSM_CARTO_STYLE_FILE)

    #with Path("data"):
    #    ln("-s", pjoin("../libs/openstreetmap-carto/", OSM_CARTO_STYLE_FILE))


@osm.command()
def download_dump():
    makedirs(DATA_DIR, exist_ok=True)

    if not path.isfile(OSM_DUMP_PATH_UNCOMPRESSED):
        click.echo("Downloading OSM dump")
        wget('-nc', '-P'+DATA_DIR, OSM_DUMP_URL, _fg=True)

        click.echo("Decompressing downloaded OSM dump")
        click.echo(bzip2('-d', OSM_DUMP_PATH))
    click.secho("OSM dump: "+ OSM_DUMP_PATH_UNCOMPRESSED, fg="green")

@osm.command()
def import_dump():
    with Path("libs/openstreetmap-carto"):
        environ['PGPASSWORD'] = "gis"
        osm2pgsql('-H'+DB_HOST, '-U'+DB_USER, '-d'+DB_NAME, '-G', '--hstore', OSM_DUMP_PATH_UNCOMPRESSED,
                  style='openstreetmap-carto.style',
                  tag_transform_script='openstreetmap-carto.lua',
                  _fg=True)
    click.secho("Successfully imported : "+ OSM_DUMP_FILE_UNCOMPRESSED, fg="green")


@click.group()
def cli():
    pass

cli.add_command(mapnik)
cli.add_command(osm)

@cli.command(help="Creates postgres user, database and extensions")
def initdb():
    environ['PGUSER'] = "postgres"

    click.echo("Creating user")
    psql("-c CREATE USER "+DB_USER+" WITH PASSWORD '"+DB_PASS+"';")

    click.echo("Creating databases")
    createdb("-Ogis", DB_NAME, encoding='utf-8')
    createdb("-Ogis", "maps", encoding='utf-8')

    click.echo("Creating extensions")
    psql("-d"+DB_NAME,"-c CREATE EXTENSION postgis; CREATE EXTENSION hstore;")
    psql("-dmaps", "-c CREATE EXTENSION postgis")


@cli.command(help="Deletes postgres user and corresponding databases")
def deletedb():
    environ['PGUSER'] = "postgres"

    click.echo("Dropping databases")
    dropdb(DB_NAME)
    dropdb("maps")

    click.echo("Dropping user")
    dropuser(DB_USER)

@cli.command(help="clear map directory")
def clearmaps():
    from app import app
    rmtree(path.join(app.static_folder, 'maps'), ignore_errors=True)


@cli.command(help="Install and configures everything")
@click.pass_context
def init(ctx):
    ctx.invoke(install)
    ctx.invoke(deletedb)
    ctx.invoke(initdb)
    ctx.invoke(download_dump)
    ctx.invoke(import_dump)
    ctx.invoke(generate_style)


if __name__ == '__main__':
    cli()
