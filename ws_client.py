#!/usr/bin/env python

import os
import sys
import optparse
from select import select
from socket import *
import tty
import signal

from websockify.websocket import WebSocket, \
    WebSocketWantReadError, WebSocketWantWriteError

parser = optparse.OptionParser(usage="%prog URL")
(opts, args) = parser.parse_args()

if len(args) == 1:
    URL = args[0]
else:
    parser.error("Invalid arguments")

sock = WebSocket()
print("Connecting to %s..." % URL)
sock.connect(URL)
print("Connected.")

mode = tty.tcgetattr(0)
tty.setraw(0)
cli = sock

while True:
    try:
        r,w,e = select([0,cli],[],[])
        if cli in r:
            data = cli.recvmsg()
            if data:
                os.write(1,data)
            else:
                print('bye')
                raise SystemExit
        if 0 in r:
            cli.sendmsg(os.read(0,1024))
    except:
        tty.tcsetattr(0,tty.TCSAFLUSH,mode)
        print('bye')
        raise SystemExit

