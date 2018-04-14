from models import Feature
from flask_socketio import SocketIO, join_room, leave_room, send
from models import Map


socketio = SocketIO()


@socketio.on('join')
def on_join(map_id):
    m = Map.get(map_id)
    join_room(m.id)
    send('user joined', room=m.id)


@socketio.on('leave')
def on_leave(map_id):
    m = Map.get(map_id)
    leave_room(m.id)
    send('user left', room=m.id)


@Feature.on_created.connect
def model_on_created(data):
    socketio.emit('created', data, room=data['properties']['map_id'])
    print("create event", data)


@Feature.on_updated.connect
def model_on_updated(data):
    socketio.emit('updated', data, room=data['properties']['map_id'])
    print("update event", data)


@Feature.on_deleted.connect
def model_on_deleted(data):
    socketio.emit('deleted', data, room=data['properties']['map_id'])
    print("delete event", data)
