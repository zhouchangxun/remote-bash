import sys
import os
import socket
import select
import pty
import signal


class ServerSide():
    def __init__(self, sock):
        pid, m, n = self.new_tty()
        self.pid = pid
        self.tty_master_fd = m
        self.tty_name = n
        self.sock = sock

    def getsockname(self):
        return self.sock.getsockname()

    def getpeername(self):
        return self.tty_name

    def new_tty(self):
        CHILD=0
        m, s = pty.openpty()
        n = os.ttyname(s)
    
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
            print 'imposible to run here'
        else:
            os.close(s)
            return pid, m, n

    def fileno(self):
        return self.tty_master_fd

    def send(self, data):
        os.write(self.tty_master_fd, data)

    def recv(self, size):
        return os.read(self.tty_master_fd, 1024)

    def close(self):
        os.kill(self.pid, signal.SIGTERM)


class LoadBalancer(object):
    """ Socket implementation of a load balancer.

    Flow Diagram:
    +---------------+      +-----------------------------------------+      +---------------+
    | client socket | <==> | client-side socket | server-side socket | <==> | server socket |
    |   <client>    |      |          < load balancer >              |      |    <server>   |
    +---------------+      +-----------------------------------------+      +---------------+

    Attributes:
        ip (str): virtual server's ip; client-side socket's ip
        port (int): virtual server's port; client-side socket's port
        algorithm (str): algorithm used to select a server
        flow_table (dict): mapping of client socket obj <==> server-side socket obj
        sockets (list): current connected and open socket obj
    """

    flow_table = dict()
    sockets = list()

    def __init__(self, ip, port, algorithm='random'):
        self.ip = ip
        self.port = port
        self.algorithm = algorithm

        # init a client-side socket
        self.cs_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # the SO_REUSEADDR flag tells the kernel to reuse a local socket in TIME_WAIT state,
        # without waiting for its natural timeout to expire.
        self.cs_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.cs_socket.bind((self.ip, self.port))
        print 'init client-side socket: %s' % (self.cs_socket.getsockname(),)
        self.cs_socket.listen(10) # max connections
        self.sockets.append(self.cs_socket)

    def start(self):
        while True:
            read_list, write_list, exception_list = select.select(self.sockets, [], [])
            for sock in read_list:
                # new connection
                if sock == self.cs_socket:
                    print '='*40+'flow start'+'='*39
                    self.on_accept()
                    break
                # incoming message from a client socket
                else:
                    try:
                        # In Windows, sometimes when a TCP program closes abruptly,
                        # a "Connection reset by peer" exception will be thrown
                        data = sock.recv(4096) # buffer size: 2^n
                        if data:
                            self.on_recv(sock, data)
                        else:
                            self.on_close(sock)
                            break
                    except:
                        self.on_close(sock)
                        break

    def on_accept(self):
        client_socket, client_addr = self.cs_socket.accept()
        print 'client connected: %s <==> %s' % (client_addr, self.cs_socket.getsockname())

        # select a server that forwards packets to
        #server_ip, server_port = self.select_server(SERVER_POOL, self.algorithm)

        # init a server-side socket
        #ss_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            #ss_socket.connect((server_ip, server_port))
            print 'init server-side shell. '
            ss_socket = ServerSide(client_socket)
            #print 'server connected: %s <==> %s' % (ss_socket.getsockname(),(socket.gethostbyname(server_ip), server_port))
        except:
            print "Can't establish connection with remote server, err: %s" % sys.exc_info()[0]
            print "Closing connection with client socket %s" % (client_addr,)
            client_socket.close()
            return

        self.sockets.append(client_socket)
        self.sockets.append(ss_socket)

        self.flow_table[client_socket] = ss_socket
        self.flow_table[ss_socket] = client_socket

    def on_recv(self, sock, data):
        print 'recving packets: %-20s ==> %-20s, data: %s' % (sock.getpeername(), sock.getsockname(), [data])
        # data can be modified before forwarding to server
        # lots of add-on features can be added here

        remote_socket = self.flow_table[sock]
        remote_socket.send(data)
        print 'sending packets: %-20s ==> %-20s, data: %s' % (remote_socket.getsockname(), remote_socket.getpeername(), [data])

    def on_close(self, sock):
        print 'client %s has disconnected' % (sock.getpeername(),)
        print '='*41+'flow end'+'='*40

        ss_socket = self.flow_table[sock]

        self.sockets.remove(sock)
        self.sockets.remove(ss_socket)

        sock.close() # close connection with client
        ss_socket.close() # close connection with server

        del self.flow_table[sock]
        del self.flow_table[ss_socket]

    def on_exit(self):
        print 'closing all sockets...'

def exit_handle():
    global server
    server.on_exit()

if __name__ == '__main__':
    global server
    # todo: register : signal.SIGTERM
    try:
        server = LoadBalancer('localhost', 5555, 'round robin')
        server.start()
        signal.signal(signal.SIGTERM, exit_handle)
    except KeyboardInterrupt:
        print "Ctrl C - Stopping tcp2bash server"
        exit_handle()
        sys.exit(0)
