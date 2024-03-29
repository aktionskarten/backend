import os

from tempfile import NamedTemporaryFile
from flask import current_app, has_app_context
from app.surface import SurfaceRenderer
from app.utils import file_exists, get_file_info


def render_map(data, file_type, force=False):
    if not has_app_context():
        from app import create_app
        from dotenv import load_dotenv
        load_dotenv('.flaskenv')
        app = create_app()
        app.app_context().push()

    map_id = data['id']
    version = data['version']
    file_info = get_file_info(map_id, version, file_type)

    # if map already is rendered, do nothing
    if not force and file_exists(file_info):
        return

    static_dir = current_app.static_folder
    map_dir = os.path.join(static_dir, file_info['dir'])
    os.makedirs(map_dir, exist_ok=True)

    renderer = SurfaceRenderer(data)
    data = renderer.render(file_info['mimetype']).read()

    # write file atomically (otherwise we end up in serving incomplete files)
    path = os.path.join(static_dir, file_info['path'])
    with NamedTemporaryFile(dir=os.path.dirname(path), delete=False) as tmp_f:
        tmp_f.write(data)
        tmp_f.flush()
        os.replace(tmp_f.name, path)

    # update latest symlink to this
    symlink_name = 'LATEST'+file_info['suffix']
    path_latest = os.path.join(static_dir, file_info['dir'], symlink_name)
    try:
        os.symlink(path, path_latest)
    except FileExistsError:
        os.unlink(path_latest)
        os.symlink(path, path_latest)
