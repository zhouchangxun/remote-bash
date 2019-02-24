#!/usr/bin/env python

import websockify
import sys,os

telnetd = '/home/leanengine/app/telnetd'
cmd = 'nohup '+telnetd+' &'
print '[run] ' + cmd
os.system(cmd)

sys.argv = [sys.argv[0],'--web','./','-D','3000','localhost:7777']
print sys.argv

websockify.websocketproxy.websockify_init()
