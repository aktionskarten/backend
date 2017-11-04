from models import Feature
from flask_socketio import SocketIO, join_room, leave_room, send


socketio = SocketIO()


@socketio.on('join')
def on_join(map_id):
    join_room(map_id)
    send('user joined', room=map_id)


@socketio.on('leave')
def on_leave(map_id):
    leave_room(map_id)
    send('user left', room=map_id)


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
