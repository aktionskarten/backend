import click
import sh

from flask import current_app
from flask.cli import with_appcontext
from os import path
from shutil import rmtree
from app.cli.pymapnik import pymapnik as pymapnik_cli
from app.cli.postgres import postgres as postgres_cli
from app.models import Map, db
from wand.image import Image
from path import Path
from app.tasks import render_map
from os import makedirs
from urllib.request import urlopen
from app.surface import SurfaceRenderer


@click.command(help="clear map directory")
@with_appcontext
def clear_maps():
    static_dir = current_app.static_folder
    rmtree(path.join(static_dir, 'maps'), ignore_errors=True)

@click.command(help="create all tables")
@with_appcontext
def create_tables():
    from app.models import db
    db.create_all()


@click.command(help="remove outdated maps from DB")
@with_appcontext
def remove_outdated_maps():
    outdated_maps = db.session.query(Map).filter_by(outdated=True).all()
    for m in outdated_maps:
        db.session.delete(m)
    db.session.commit()


@click.command(help="generate markers")
def gen_markers():
    URL = 'https://github.com/aktionskarten/AktionskartenMarker/raw/gh-pages/AktionskartenMarker.hq.png'
    STEP_SIZE = 150
    TARGET_DIR = 'styles/markers'
    COLORS = ['e04f9e', 'fe0000', 'ee9c00', 'ffff00', '00e13c', '00a54c',
              '00adf0', '7e55fc', '1f4199', '7d3411']
    NAMES = ['train', 'megaphone', 'tent', 'speaker', 'reheat', 'cooking-pot',
             'police', 'nuclear', 'empty', 'point', 'information',
             'exclamation-mark', 'star', 'star-megaphone', 'arrow', 'bang']

    print("Downloading " + URL)
    with Image(file=urlopen(URL)) as img:
        makedirs(TARGET_DIR, exist_ok=True)
        with Path(TARGET_DIR):
            for i in range(0, len(COLORS)):
                h = i*STEP_SIZE
                folder = '#'+COLORS[i]
                makedirs(folder, exist_ok=True)
                print("\n"+folder)
                for j in range(0, len(NAMES)):
                    w = j*STEP_SIZE
                    h_end = h+STEP_SIZE
                    w_end = w+STEP_SIZE
                    with Path(folder):
                        with img[w:w_end, h:h_end] as chunk:
                            name = NAMES[j]
                            chunk.save(filename='{}.png'.format(name))
                            print("\t* " + name)

@click.command(help="Render a given map")
@click.option('--mid')
@click.option('--filename')
@with_appcontext
def render(mid, filename):
    m = Map.get(mid)
    data = m.to_dict(grid_included=True, features_included=True)
    renderer = SurfaceRenderer(data)
    with open(filename, 'wb') as f2:
        f2.write(renderer.render('application/pdf').read())
