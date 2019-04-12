import os
import mimetypes

from flask import Blueprint, request, jsonify, current_app, abort, url_for
from hashlib import sha256
from flask import send_file
from rq.job import Job
from rq.registry import FinishedJobRegistry
from app.tasks import get_file_info, file_exists, get_version
from app.utils import InvalidUsage


renderer = Blueprint('Renderer', __name__)


def _request_args_restricted(key, whitelist):
    value = request.args.get(key, default=whitelist[0], type=str)
    if value.split(':')[0] not in whitelist:
        raise InvalidUsage("unsupported " + key + " type")
    return value


def _parse_request():
    if not request.is_json:
        raise InvalidUsage("invalid request")

    content = request.get_json()
    if 'name' not in content:
        raise InvalidUsage("no name given")

    file_type = _request_args_restricted('file_type', ['png', 'pdf', 'svg'])
    return content, file_type


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

    return jsonify(**data, **job.meta), 200


@renderer.route('/status/<string:job_id>')
def status_by_job_id(job_id):
    queue = current_app.task_queue
    job = Job.fetch(job_id, connection=queue.connection)
    return status_by_job(job)


# TODO:
#   * Add support for status without version (read version from LATEST symlink)
@renderer.route('/status/<string:map_id>/<string:version>/<string:file_type>')
def status_by_map(map_id, version, file_type):
    queue = current_app.task_queue

    # search in task queue (iterate in descending order newest->oldest)
    for job in reversed(queue.get_jobs()):
        if job.meta['map_id'] == map_id and job.meta['version'] == version and\
           job.meta['file_type'] == file_type:  # TODO: size for PNG
            return status_by_job(job)

    # check if it has been finished recently
    registry = FinishedJobRegistry('default', queue=queue)
    for job_id in reversed(registry.get_job_ids()):
        job = Job.fetch(job_id, connection=queue.connection)
        if job.meta['map_id'] == map_id and job.meta['version'] == version and\
           job.meta['file_type'] == file_type:
            return status_by_job(job)

    # not found in our queues or registries, check if has been rendered at all
    file_info = get_file_info(map_id, version, file_type)
    if not file_exists(file_info):
        abort(404)

    data = {
        'map_id': map_id,
        'file_type': file_type,
        'version': version,
        'state': 'finished',
        'url': url_for('static', filename=file_info['path'], _external=True)
    }
    return jsonify(**data), 200


@renderer.route('/render', methods=['POST'])
def render():
    # arg: blocking = true -> send_map
    data, file_type = args = _parse_request()

    map_id = data['map_id']
    version = get_version(data)
    file_info = get_file_info(map_id, version, file_type)

    meta = {
        'map_id': map_id,
        'version': version,
        'file_type': file_type,
    }

    force = request.args.get('force', default=False, type=bool)
    if force:
        args += (force,)

    # if map already is rendered, do nothing
    if not force and file_exists(file_info):
        meta['status'] = 'finished'
        return jsonify(**meta)

    # check if map:version:file_type is already in enqueued
    queue = current_app.task_queue
    job = None
    for j in queue.get_jobs():
        if j.meta['map_id'] == map_id and j.meta['version'] == version and\
           j.meta['file_type'] == file_type:  # TODO: size for PNG
            job = j
            break

    # if there is no job, enqueue it
    if not job:
        job = queue.enqueue("app.tasks.render_map", *args, meta=meta)

    data = {
        'job_id': job.id,
        'status': job.get_status(),
        'created_at': job.created_at
    }
    return jsonify(**data, **job.meta), 200
