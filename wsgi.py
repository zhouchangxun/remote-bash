#!/usr/bin/env python

from gevent import monkey
monkey.patch_all()

from flask import Flask, request, abort, render_template
from werkzeug.exceptions import BadRequest
import gevent

#import proxy

app = Flask('wsgi')
app.debug = True
app.static_folder = './'

@app.route('/')
def index():
    return 'ws2tcp proxy server'

@app.route('/wssh/<hostname>/<username>')
def shell(hostname, username):
    print(hostname, username)
    return shell_server()

@app.route('/ws/shell')
def shell2():
    return shell_server()

def shell_server():
    # Abort if this is not a websocket request
    if not request.environ.get('wsgi.websocket'):
        app.logger.error('Abort: Request is not WebSocket upgradable')
        raise BadRequest()

    ws = request.environ['wsgi.websocket']
    try:
        print 'new ws', ws
        #ws.send('websocket ready...')
        session = proxy.Bridge(ws)
        session.open('localhost', 5555)
    except Exception as e:
        print 'exception'
        app.logger.exception('Error: {0}'.format( e.message))
        request.environ['wsgi.websocket'].close()
        return str('exception')

    print 'begin session'
    session.shell()
    print 'end session'
    # We have to manually close the websocket and return an empty response,
    # otherwise flask will complain about not returning a response and will
    # throw a 500 at our websocket client
    request.environ['wsgi.websocket'].close()
    return str()

@app.route('/ws/echo')
def echo_server():

    # Abort if this is not a websocket request
    if not request.environ.get('wsgi.websocket'):
        app.logger.error('Abort: Request is not WebSocket upgradable')
        raise BadRequest()

    ws = request.environ['wsgi.websocket']
    print 'begin ws session'
    try:
        #ws.send('websocket ready...')
        while True:
            data = ws.receive()
            if data:
                if data=='q': break
                ws.send('\r\n->echo '+data)
            else: break
    except Exception as e:
        print 'exception'
        app.logger.exception('Error: {0}'.format( e.message))
        request.environ['wsgi.websocket'].close()
        return str('exception')

    print 'end session'
    # We have to manually close the websocket and return an empty response,
    # otherwise flask will complain about not returning a response and will
    # throw a 500 at our websocket client
    request.environ['wsgi.websocket'].close()
    return str()

application = app
