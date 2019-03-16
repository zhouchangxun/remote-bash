#!/usr/bin/env python

import websockify
import sys,os


print sys.argv
sys.argv = [sys.argv[0],'-D','-v','--log-file=/home/leanengine/app/app.log', '--web=./','3000','localhost:7777']
print sys.argv

websockify.websocketproxy.websockify_init()

telnetd = '/home/leanengine/app/telnetd'
cmd = 'nohup '+telnetd+' &'
print '[run] ' + cmd
os.system(cmd)
