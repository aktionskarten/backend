from app.models import Map, Feature
from flask_socketio import SocketIO, join_room, leave_room, send

socketio = SocketIO()

@socketio.on('join')
def on_join(map_id):
    #TODO: authenticated
    if Map.get(map_id):
        join_room(map_id)
        send('user joined', room=map_id)


@socketio.on('leave')
def on_leave(map_id):
    if Map.get(map_id):
        leave_room(map_id)
        send('user left', room=map_id)

@Map.on_updated.connect
def map_on_updated(data):
    socketio.emit('map-updated', data['new'], room=data['new']['id'])

@Map.on_deleted.connect
def map_on_deleted(data):
    socketio.emit('map-deleted', data['new'], room=data['new']['id'])

@Feature.on_created.connect
def feature_on_created(data):
    room = data['new']['properties']['map_id']
    socketio.emit('feature-created', data['new'], room=room)
    print("create event", data)


@Feature.on_updated.connect
def feature_on_updated(data):
    room = data['new']['properties']['map_id']
    socketio.emit('feature-updated', data['new'], room=room)
    print("update event", data)


@Feature.on_deleted.connect
def feature_on_deleted(data):
    room = data['new']['properties']['map_id']
    socketio.emit('feature-deleted', data['new'], room=room)
    print("delete event", data)
