import os
import time
import pty
import tty
import select
import signal
from socket import *

ADDR=("0.0.0.0",7777)
CHILD=0

m,s = pty.openpty()

print 'new tty: ' + os.ttyname(s)

def hup_handle(signum,frame):
    print 'interrupt'
    sock.send("\n")
    sock.close()
    raise SystemExit

pid = os.fork()
if pid == CHILD:
    os.setsid()
    os.close(m)
    os.dup2(s,0)
    os.dup2(s,1)
    os.dup2(s,2)

    tmp_fd = os.open(os.ttyname(s), os.O_RDWR)
    os.close(tmp_fd)
    os.execlp("/bin/bash","/bin/bash")
    os.close(s)
    print 'child end'
else:
    os.close(s)
    signal.signal(signal.SIGINT,hup_handle)
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET,SO_REUSEADDR ,1)
    sock.bind(ADDR)
    sock.listen(1)
    conn, addr = sock.accept()
    conn.settimeout(3)
    print 'client connected: ', addr
    fds = [m, conn]
    mode = tty.tcgetattr(0)
    #tty.setraw(0)
    try:
        while True:
            if not conn.connect_ex(addr):
                print 'remote client exit '
                raise Exception

            r,w,e = select.select(fds,[],[])
            if m in r:
                try:
                    data = os.read(m,1024)
                except:
                    print 'bash exit '
                    os.close(m)
                    break

                if data:
                    conn.send(data)
                else:
                    fds.remove(m)
            if conn in r:
                data = conn.recv(1024)
                if not data:
                    print 'client disconnect '
                    fds.remove(conn)
                if data:
                    os.write(m,data)
    except:
        print 'except occur'
    finally:
        print 'server disconnect'
        conn.close()
        sock.close()

print ' end'
