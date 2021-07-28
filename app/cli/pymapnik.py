import click
import sys

from distutils.core import run_setup
from os import environ, getcwd
from os.path import isdir
from path import Path
from platform import release as os_release
from urllib.request import urlretrieve
from shutil import unpack_archive
from sh import patch

@click.group(help="mapnik related commands")
def pymapnik():
    pass


def _mapnik_is_installed():
    try:
        import mapnik
        return mapnik.mapnik_version() > 0
    except ImportError:
        return False


@pymapnik.command()
def is_installed():
    if _mapnik_is_installed():
        click.secho("Mapnik is installed and works!", fg='green')
    else:
        click.secho("Mapnik is missing!", fg='red')
        click.echo("Run 'mapnik install' do fix this")


@pymapnik.command()
def install():
    if _mapnik_is_installed():
        click.secho("Mapnik already installed!", fg='green')
        return

    environ['PYCAIRO'] = "true"


    with Path("libs/python-mapnik"):
        import subprocess
        #child = subprocess.call(['python', 'setup.py', 'clean'])
        #if child != 0:
        #    sys.exit(-1)

        import cairo
        include_path = '--include-dirs=' + cairo.get_include()
        child = subprocess.call([sys.executable, 'setup.py', 'build_ext', include_path])
        if child != 0:
            sys.exit(-1)

        child = subprocess.call(['python', 'setup.py', 'install'])
        if child != 0:
            sys.exit(-1)

        # following seems not to work in debian 9
        #dist = run_setup('setup.py')
        #dist.run_command('clean')
        #dist.run_command('install')

    click.secho("Mapnik installed successfully!", fg='green')


if __name__ == '__main__':
    pymapnik()
