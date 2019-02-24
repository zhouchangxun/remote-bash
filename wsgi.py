#!/usr/bin/env python

import websockify
import sys,os

telnetd = os.path.dirname(os.path.realpath(__file__))+'/telnetd'
cmd = 'nohup '+telnetd+' &'
print '[run] ' + cmd
os.system(cmd)

sys.argv = sys.argv + ['--web','./','-D','3000','localhost:7777']
print sys.argv

websockify.websocketproxy.websockify_init()
