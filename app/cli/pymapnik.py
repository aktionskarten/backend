import click

from distutils.core import run_setup
from os import environ
from path import Path

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
        return

    environ['PYCAIRO'] = "true"
    with Path("libs/python-mapnik"):
        dist = run_setup('setup.py')
        dist.run_command('clean')
        dist.run_command('install')
    del environ['PYCAIRO']

    click.secho("Mapnik installed successfully!", fg='green')


if __name__ == '__main__':
    pymapnik()
