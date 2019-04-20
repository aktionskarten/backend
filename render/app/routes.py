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
    """ Download a map identified by map_id, file_type and optional version.

    Only already rendered maps can be downloaded. Each file format has to be
    rendered separately. If a map is not found you will get an 404 error
    statuscode.

    :param map_id: id of map
    :param file_type: `svg`, `pdf` or `png[:small|medium|large]`
    :status 200: sends content of map
    :status 404: map, version or file_type not found
    """
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
    """ Retrieve status of a render job by its job id

    To get informations if a job is still running or finished you may use
    `status_by_job`.

    :param job_id: id of job
    :status 200: informations about current job
    :status 404: map, version or file_type not found
    """
    queue = current_app.task_queue
    try:
        job = Job.fetch(job_id, connection=queue.connection)
        return status_by_job(job)
    except NoSuchJobError:
        abort(404)


def _find_in_registry(registry, map_id, version, file_type):
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
    """ Retrieve status of a render job by it `map_id`, `verison` and
    `file_type`


    :param map_id: map id
    :param version: version
    :param file_type: filetype
    :status 200: informations about current job
    :status 400: invalid file type
    :status 404: map and or version of map not found
    """
    queue = current_app.task_queue

    # check if it is queued to be rendered
    for job in queue.get_jobs():
        if job.meta['map_id'] == map_id and\
           job.meta['version'] == version and\
           job.meta['file_type'] == file_type:
            return status_by_job(job)

    # check if it is currently rendering
    started = StartedJobRegistry(queue=queue)
    job = _find_in_registry(started, map_id, version, file_type)
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
    job = _find_in_registry(finished, map_id, version, file_type)
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
    """Renders a map

        **Example request**:

        .. sourcecode:: bash

          $ curl -i -X POST -H "Content-Type: application/json" -d @tests/data/test_map.json http://localhost:5000/render/png

        **Example response**:

        .. sourcecode:: http

          HTTP/1.1 202 Accepted
          Content-Type: application/json

          {
            "file_type": "png",
            "job_id": "fce3b682-feaa-48b7-b945-ad243ce62df4",
            "map_id": "test123",
            "status": "queued",
            "version": "c8bbde29fa1cfd1109fae1835fcc1ea1f92f4e31292c1b3d338c782f18333605"
          }

        :param file_type: file type of rendered map. Either `pdf`, `svg` or `png:<size>` with size `small`, `medium` or `large`
        """
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

    return status_by_job(job), 202
