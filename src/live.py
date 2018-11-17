from models import Map, Feature
from flask_socketio import SocketIO, join_room, leave_room, send

socketio = SocketIO()


@socketio.on('join')
def on_join(map_id):
    m = Map.get(map_id)
    join_room(m.slug)
    send('user joined', room=m.slug)


@socketio.on('leave')
def on_leave(map_id):
    m = Map.get(map_id)
    leave_room(m.slug)
    send('user left', room=m.slug)

@Map.on_updated.connect
def map_on_updated(data):
    socketio.emit('map-updated', data['new'], room=data['new']['id'])

    # if we have old data, post as well in old room
    try:
        socketio.emit('map-updated', data['new'], room=data['old']['slug'])
    except KeyError:
        pass

    print("update event", data)

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
