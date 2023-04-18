# coding=utf-8
import os
import pty
import tty
import select
import socket
import sys

class EndpointShell:
    def __init__(self):
        self.type = 'shell'
        self.fd = None
        self.pid = None

    def fileno(self):
        return self.fd

    def close(self):
        print('exit shell with pid: ', self.pid)

    def connect(self):
        print('connect to shell')
        m, s = pty.openpty()
        print ('new tty: ' + os.ttyname(s))
        pid = os.fork()
        if pid != 0:
            print('shell pid: ', pid)
            os.close(s)
            self.fd = m
            self.pid = pid
            return
        # next code for child process
        os.setsid()
        os.close(m)
        os.dup2(s,0)
        os.dup2(s,1)
        os.dup2(s,2)
        tmp_fd = os.open(os.ttyname(s), os.O_RDWR)
        os.close(tmp_fd)
        #tty.setraw(0)
        os.execlp("/bin/bash","/bin/bash")

    def send(self, data):
        print('send ', data)
        os.write(self.fd, data)

    def recv(self, size=1024):
        try:
          data = os.read(self.fd, size)
          print('recv ', data)
        except:
          data = None
        return data


class Proxy:
    def __init__(self, listen_addr, to_addr):
        '''
        :param listen_addr: 本地监听地址
        :param to_addr: 转发地址
        '''
        self.proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.proxy.bind(listen_addr)
        self.proxy.listen(10)
        self.inputs = [self.proxy]
        self.route = {}
        self.to_addr = to_addr

    def serve_forever(self):
        print('proxy listen...')
        while 1:
            readable, _, _ = select.select(self.inputs, [], [])
            for self.sock in readable:
                if self.sock == self.proxy:
                    self.on_join()
                else:
                    data = self.sock.recv(8096)
                    if not data:
                        self.on_quit()
                    else:
                        self.route[self.sock].send(data)

    def on_join(self, backend_type='shell,tcp'):
        newsocket, addr = self.proxy.accept()
        client = newsocket
        print(addr, 'connect req')
        if backend_type == 'tcp':
            backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            backend.connect(self.to_addr)
        else:
            backend = EndpointShell()
            backend.connect()
        self.inputs += [client, backend]
        self.route[client] = backend
        self.route[backend] = client

    def on_quit(self):
        for s in self.sock, self.route[self.sock]:
            self.inputs.remove(s)
            del self.route[s]
            s.close()


if __name__ == '__main__':
    try:
        Proxy(('0.0.0.0', 7777),('127.0.0.1', 80)).serve_forever()  # 代理服务器监听的地址
    except KeyboardInterrupt:
        sys.exit(1)
