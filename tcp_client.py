
import os
from select import select
from socket import *
import tty
import signal

ADDR = ('127.0.0.1', 7777)


cli = socket(AF_INET, SOCK_STREAM)

cli.connect(ADDR)

print 'connected remote bash. begin forwad between i/o <-> tcp'

mode = tty.tcgetattr(0)
tty.setraw(0)

while True:
    if not cli.connect_ex(ADDR):
        break
    try:
        r,w,e = select([0,cli],[],[])
        if cli in r:
            data = cli.recv(1024)
            if data:
                os.write(1,data)
            else:
                tty.tcsetattr(0,tty.TCSAFLUSH,mode)
                break 
        if 0 in r:
            cli.send(os.read(0,1024))
    except:
        tty.tcsetattr(0,tty.TCSAFLUSH,mode)
        print 'except exit'
        break

print 'exit from remote bash'

