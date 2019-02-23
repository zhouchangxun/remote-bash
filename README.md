# remote-bash
remote bash by multi channel (tcp/websocket)

# usage
1. remote bash by tcp
  1. python tcp_server.py(listen 7777)
  2. python tcp_client.py(connect to 7777)

2. remote bash by websocket
  1. python tcp_server.py
  2. python ws2tcp.py 6666 localhost:7777(proxy 6666 to 7777)
  3. python ws_client.py ws://localhost:6666

# TODO
 1. [tcp_server]support multi connection 

