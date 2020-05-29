import os
from flask_socketio import SocketIO, emit
from flask import Flask, session, render_template, request, redirect, jsonify
from flask_session import Session
import requests
from functools import wraps

app = Flask(__name__)
app.config["SECRET_KEY"] = "my secret key"
socketio = SocketIO(app)

logged_users = []



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
    return render_template('index.html')

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
    return redirect('/')
