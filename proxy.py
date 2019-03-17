# -*- coding: utf-8 -*-

"""
wssh.server

This module provides server capabilities of wssh
"""

import gevent
from gevent.socket import wait_read, wait_write
from gevent.select import select
from gevent.event import Event


import socket

try:
    import simplejson as json
except ImportError:
    import json

from StringIO import StringIO


class Bridge(object):
    """ WebSocket to SSH Bridge Server """

    def __init__(self, websocket):
        """ Initialize a WSSH Bridge

        The websocket must be the one created by gevent-websocket
        """
        self._websocket = websocket
        self._ssh = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tasks = []

    def open(self, hostname='localhost', port=5555, timeout=None):
        """ Open a connection to a remote SSH server

        """
        try:
            upstream = (hostname, port)
            self._ssh.connect(upstream)
        except Exception as e:
            self._websocket.send(json.dumps({'error': e.message or str(e)}))
            raise

    def _forward_inbound(self, channel):
        """ Forward inbound traffic (websockets -> ssh) """
        try:
            while True:
                data = self._websocket.receive()
                print 'recv from ws %s' % data
                if not data:
                    print 'cli disconnect'
                    return
                #data = json.loads(str(data))
                #if 'resize' in data:
                #    channel.resize_pty(
                #        data['resize'].get('width', 80),
                #        data['resize'].get('height', 24))
                #if 'data' in data:
                #    channel.send(data['data'])
                print 'farword to upstream1: %s' % data
                channel.send(data)
                print 'farword to upstream2'
        finally:
            self.close()

    def _forward_outbound(self, channel):
        """ Forward outbound traffic (ssh -> websockets) """
        try:
            while True:
                wait_read(channel.fileno())
                data = channel.recv(1024)
                print 'recv from upstream: %s' % data
                if not data:
                    print 'upstream disconnect'
                    return
                #self._websocket.send(json.dumps({'data': data}))
                print 'farword to ws1: %s ' % data
                self._websocket.send(data)
                print 'farword to ws2'
        finally:
            self.close()

    def _bridge(self, channel):
        """ Full-duplex bridge between a websocket and a SSH channel """
        channel.setblocking(False)
        channel.settimeout(0.0)
        self._tasks = [
            gevent.spawn(self._forward_inbound, channel),
            gevent.spawn(self._forward_outbound, channel)
        ]
        gevent.joinall(self._tasks)

    def close(self):
        """ Terminate a bridge session """
        gevent.killall(self._tasks, block=True)
        self._tasks = []
        self._ssh.close()

    def shell(self, term='xterm'):
        """ Start an interactive shell session

        This method invokes a shell on the remote SSH server and proxies
        traffic to/from both peers.

        You must connect to a SSH server using ssh_connect()
        prior to starting the session.
        """
        channel = self._ssh
        self._bridge(channel)
        channel.close()
