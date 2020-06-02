import os
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from flask import Flask, session, render_template, request, redirect, jsonify
from flask_session import Session
import requests
from functools import wraps
from collections import deque

app = Flask(__name__)
app.config["SECRET_KEY"] = "my secret key"
socketio = SocketIO(app)

logged_users = []
channels = []
channelsMessages = dict()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('username') is None:
            return redirect('/signin')
        else:
            return f(*args, **kwargs)
    return decorated

@app.route("/")
@login_required
def index():
    return render_template('index.html', channels=channels)

@app.route("/signin", methods=['GET','POST'])
def signin():
    session.clear()
    username = request.form.get("username")

    if request.method == 'POST':
        if len(username) < 2:
            return render_template('error.html', message="Username can't be empty!")
        if username in logged_users:
            return render_template('error.html', message='User is already logged in!')

        session['username'] = username
        logged_users.append(username)
        # Remember the user session on a cookie if the browser is closed.
        session.permanent = True

        return redirect("/")
    else:
        return render_template("signin.html")

@app.route("/logout", methods=['GET'])
def logout():
    try:
        logged_users.remove(session.get('username'))
        session.clear()
    except: pass
    return redirect('/signin')


@app.route('/create', methods=['GET','POST'])
def create():
    channel = request.form.get('channel')
    if request.method == 'POST':

        if channel == '':
            return render_template('error.html', message="Channel name can not be empty!")
        if channel in channels:
            return render_template('chatroom.html', channel_name=channel, channels=channels, messages=channelsMessages[channel])
        else:
            channels.append(channel)
            channelsMessages[channel] = deque()
            return redirect("/channel/"+str(channel))
            #return render_template('chatroom.html', channel_name=channel, channels=channels)



@app.route("/channel/<channel>", methods=['GET','POST'])
@login_required
def view(channel):

    session['current_channel'] = channel
    return render_template('chatroom.html',channel_name=channel, channels=channels, messages=channelsMessages[channel])



@socketio.on("joined", namespace='/')
def joined():
    """ Send message to announce that user has entered the channel """

    # Save current channel to join room.
    room = session.get('current_channel')

    join_room(room)
    print('da5lt', room,session.get('username'))
    emit('status', {
        'userJoined': session.get('username'),
        'channel': room,
        'msg': session.get('username') + ' has entered the channel'},
        room=room)

@socketio.on("left", namespace='/')
def left():
    """ Send message to announce that user has left the channel """

    room = session.get('current_channel')

    leave_room(room)
    emit('status', {
        'msg': session.get('username') + ' has left the channel'},
        room=room)


@socketio.on('send message')
def send_msg(msg, timestamp):
    """ Receive message with timestamp and broadcast on the channel """

    # Broadcast only to users on the same channel.
    room = session.get('current_channel')

    # Save 100 messages and pass them when a user joins a specific channel.

    if len(channelsMessages[room]) > 100:
        # Pop the oldest message
        channelsMessages[room].popleft()
    print(msg)
    channelsMessages[room].append([timestamp, session.get('username'), msg])

    emit('announce message', {
        'user': session.get('username'),
        'timestamp': timestamp,
        'msg': msg},
        room=room)
