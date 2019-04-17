import os
import mimetypes

from flask import Blueprint, request, jsonify, current_app, abort, url_for
from werkzeug.exceptions import NotFound
from hashlib import sha256
from flask import send_file
from rq.job import Job
from rq.exceptions import NoSuchJobError
from rq.registry import StartedJobRegistry, FinishedJobRegistry
from app.tasks import get_file_info, file_exists, get_version,\
                      UnsupportedFileType
from app.utils import InvalidUsage


renderer = Blueprint('Renderer', __name__)


@renderer.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error=error.message)
    response.status_code = error.status_code
    return response

# TODO:
#  * custom converters - use file_type instead of string in route like:
#       '/download/<string:map_id>.<file_type:file_type>'
@renderer.route('/download/<string:map_id>_<string:version>.<string:file_type>')
@renderer.route('/download/<string:map_id>.<string:file_type>')
def download(map_id, file_type, version=None):
    dirname = sha256(map_id.encode()).hexdigest()
    extension, *args = file_type.split(':')
    mimetype = mimetypes.types_map['.' + extension]

    if not version:
        version = 'LATEST'

    suffix = ''
    if len(args) > 0:
        suffix = '_' + args.pop()

    filename = '{}{}.{}'.format(version, suffix, extension)
    static_path = current_app.static_folder
    path = os.path.join(static_path, 'maps', dirname, filename)

    if not os.path.exists(path):
        abort(404)

    return send_file(path,
                     attachment_filename=filename,
                     mimetype=mimetype, cache_timeout=0)


def status_by_job(job):
    if not job:
        abort(404)

    status = job.get_status()
    data = {
        'job_id': job.id,
        'status': status,
    }

    if (status == 'finished'):
        file_info = get_file_info(job.meta['map_id'], job.meta['version'],
                                  job.meta['file_type'])
        data['url'] = url_for('static', filename=file_info['path'],
                              _external=True)

    return jsonify(**data, **job.meta)


@renderer.route('/status/<string:job_id>')
def status_by_job_id(job_id):
    queue = current_app.task_queue
    try:
        job = Job.fetch(job_id, connection=queue.connection)
        return status_by_job(job)
    except NoSuchJobError:
        abort(404)


def find_in_registry(registry, map_id, version, file_type):
    for job_id in reversed(registry.get_job_ids()):
        job = Job.fetch(job_id, connection=registry.connection)
        if job.meta['map_id'] == map_id and\
           job.meta['version'] == version and\
           job.meta['file_type'] == file_type:
            return job

# TODO:
#   * Add support for status without version (read version from LATEST symlink)
@renderer.route('/status/<string:map_id>/<string:version>/<string:file_type>')
def status_by_map(map_id, version, file_type):
    queue = current_app.task_queue

    # check if it is queued to be rendered
    for job in queue.get_jobs():
        if job.meta['map_id'] == map_id and\
           job.meta['version'] == version and\
           job.meta['file_type'] == file_type:
            return status_by_job(job)

    # check if it is currently rendering
    started = StartedJobRegistry(queue=queue)
    job = find_in_registry(started, map_id, version, file_type)
    if job:
        return status_by_job(job)

    # it it's not queued or rendering, it needs to be already rendered
    try:
        file_info = get_file_info(map_id, version, file_type)
        if not file_exists(file_info):
            abort(404)
    except UnsupportedFileType:
        abort(400)

    # enhance output with job_id if it is recently rendered
    finished = FinishedJobRegistry(queue=queue)
    job = find_in_registry(finished, map_id, version, file_type)
    if job:
        return status_by_job(job)

    data = {
        'map_id': map_id,
        'file_type': file_type,
        'version': version,
        'status': 'finished',
        'url': url_for('static', filename=file_info['path'], _external=True)
    }
    return jsonify(**data)


@renderer.route('/render/<string:file_type>', methods=['POST'])
def render(file_type):
    data = request.get_json()
    map_id = data['id']
    version = get_version(data)

    args = (data, file_type)
    force = request.args.get('force', default=False, type=bool)
    if force:
        args += (force,)

    # TODO: merge with file_info exception UnsupportedFileType
    extension = file_type.split(':')[0]
    if '.'+extension not in mimetypes.types_map:
        abort(400)

    try:
        if not force:
            return status_by_map(map_id, version, file_type)
    except NotFound:
        pass

    queue = current_app.task_queue
    meta = {
        'map_id': map_id,
        'version': version,
        'file_type': file_type,
    }
    job = queue.enqueue("app.tasks.render_map", *args, meta=meta)

    return status_by_job(job)
