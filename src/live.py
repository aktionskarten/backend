#from flask_socketio import SocketIO, join_room, leave_room, send
#
#socketio = SocketIO(app, path="/api/live")
#
#
#@socketio.on('message')
#def handle_message(message):
#    print('received message: ' + message)
#
#@socketio.on('my event')
#def handle_my_custom_event(json):
#    print('received json: ' + str(json))
#
#@socketio.on('join')
#def on_join(data):
#    map_id = data['map_id']
#    print("joined room")
#    join_room(map_id)
#    send('has entered the room.', room=map_id)
#
#
#@socketio.on('leave')
#def on_leave(data):
#    map_id = data['map_id']
#    print("left room")
#    leave_room(map_id)
#    #send(username + ' has left the room.', room=room)
#
#@app.route('/live')
#def live():
#    return '''
#    <script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/socket.io/1.3.6/socket.io.min.js"></script>
#<script type="text/javascript" charset="utf-8">
#    var socket = io.connect('http://' + document.domain + ':' + location.port, {'path': '/api/live'});
#    var map_id = 1
#    socket.on('connect', function() {
#        socket.emit('join', {'map_id':map_id});
#    });
#
#    socket.on('message', function(data) {
#        console.log(data);
#//        socket.emit('leave', {'map_id':map_id})
#    });
#
#    console.log("started");
#</script>
#    '''
