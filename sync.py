# vlc_sync
#
# (C) 2012 by Dominik Jain (djain@gmx.net)
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import socket
import sys
import threading
import pickle
import wx
import asyncore
from wxvlc import Player
import time as t
import traceback

class DispatchingPlayer(Player):
	def __init__(self, title, dispatcher, isServer):
		Player.__init__(self, title)
		self.dispatcher = dispatcher
		self.isServer = isServer
		self.lastPing = t.time()
		self.Centre()
		self.Show()

	def OnOpen(self, evt):
		super(DispatchingPlayer, self).OnOpen(evt)
		if not self.isServer:
			self.dispatch(evt="OnQueryPlayLoc", args=())
	
	def OnQueryPlayLoc(self, dispatch=True):
		if not self.isServer or self.getMedia() is None: return
		self.dispatch(evt="OnPlayAt" if not self.isPaused() else "OnPauseAt", args=(self.getTime(),))

	def OnPlay(self, evt, dispatch=True):
		if self.getMedia() is None:
			self.OnOpen(None)
			if not self.isServer:
				dispatch = False				
		else:
			self.play()
		if dispatch: self.dispatch(evt="OnPlayAt", args=(self.getTime(),))
	
	def OnPlayAt(self, time, dispatch=False):
		self.seek(time)
		self.play()
	
	def OnPause(self, evt, dispatch=True):
		if self.isServer and not hasattr(self, "doneit"):
			self.doneit=True
			print "closing client connections"
			for conn in self.dispatcher.connections:
				conn.handle_close()			
			return
		super(DispatchingPlayer, self).OnPause(evt)
		if dispatch:
			self.dispatch(evt="OnPauseAt", args=(self.getTime(),))
	
	def OnPauseAt(self, time, dispatch=False):
		self.seek(time)
		self.pause()
	
	def OnSeek(self, time, dispatch=True):
		super(DispatchingPlayer, self).OnSeek(time)
		if dispatch: self.dispatch(evt="OnSeek", args=(time,))
	
	def dispatch(self, **d):
		self.dispatcher.dispatch(d)

	def handleNetworkEvent(self, d):
		exec("self.%s(*d['args'], dispatch=False)" % d["evt"])
		
	def OnTimer(self, evt):
		Player.OnTimer(self, evt)
		# perform periodic ping from client to server
		if not self.isServer:
			if t.time() - self.lastPing > 1:
				self.lastPing = t.time()
				self.dispatch(ping = True)
	
class SyncServer(asyncore.dispatcher):
	def __init__(self, port):
		asyncore.dispatcher.__init__(self)
		# start listening for connections
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		host = ""
		self.bind((host, port))
		self.connections = []
		self.listen(5)
		# create actual player
		self.player = DispatchingPlayer("Sync'd VLC Server", self, True)		
	
	def handle_accept(self):		
		pair = self.accept()
		if pair is None:
			return
		print "incoming connection from %s" % str(pair[1])
		conn = DispatcherConnection(pair[0], self)
		self.connections.append(conn)
		conn.sendData("hello %s" % str(pair[1]))

	def dispatch(self, d, exclude=None):
		print "dispatching %s to %d client(s)" % (str(d), len(self.connections) if exclude is None else len(self.connections)-1)
		for c in self.connections:
			if c != exclude:
				c.sendData(d)
	
	def removeConnection(self, conn):
		if not conn in self.connections:
			print "tried to remove non-present connection"
		self.connections.remove(conn)
		if len(self.connections) == 0:
			self.player.pause()
			self.player.errorDialog("All client connections have been closed.")			

class DispatcherConnection(asyncore.dispatcher_with_send):
	def __init__(self, connection, server):
		asyncore.dispatcher_with_send.__init__(self, connection)
		self.syncserver = server

	def writable(self):
		return bool(self.out_buffer)

	def handle_write(self):
		self.initiate_send()

	def handle_read(self):
		d = self.recv(8192)
		if d == "": # connection closed from other end			
			return
		d = pickle.loads(d)
		if type(d) == dict and "ping" in d: # ignore pings
			return
		print "received: %s " % d
		if type(d) == dict and "evt" in d:
			# forward event to other clients
			self.syncserver.dispatch(d, exclude=self)
			# handle in own player
			self.syncserver.player.handleNetworkEvent(d)			

	def remove(self):
		print "client connection dropped"
		self.syncserver.removeConnection(self)

	def handle_close(self):
		self.remove()
		self.close()

	def sendData(self, d):
		self.send(pickle.dumps(d))

class SyncClient(asyncore.dispatcher):	
	def __init__(self, server, port):
		asyncore.dispatcher.__init__(self)		
		self.serverAddress = (server, port)
		self.connectedToServer = self.connectingToServer = False
		self.connectToServer()
		# create actual player
		self.player = DispatchingPlayer("Sync'd VLC Client", self, False)

	def connectToServer(self):
		self.connectingToServer = True
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)		
		self.connect(self.serverAddress)
	
	def handle_connect(self):
		self.connectingToServer = False
		self.connectedToServer = True
		# immediately request current playback data
		self.player.dispatch(evt="OnQueryPlayLoc", args=())
		
	def handle_read(self):
		d = self.recv(8192)
		if d == "": # server connection lost
			return
		d = pickle.loads(d)
		print "received: %s " % d
		if type(d) == dict and "evt" in d:
			self.player.handleNetworkEvent(d)
	
	def handle_close(self):
		self.close()
		
	def readable(self):
		return True
	
	def writable(self):
		return True
		
	def close(self):
		asyncore.dispatcher.close(self)
		traceback.print_stack()
		self.connectedToServer = False
		self.player.pause()
		self.player.errorDialog("Connection lost. Click OK to attempt reconnect.")		
	
	def dispatch(self, d):
		if not self.connectedToServer:
			if not self.connectingToServer:
				self.connectToServer()
			return
		if not (type(d) == dict and "ping" in d):
			print "sending %s" % str(d)
		self.send(pickle.dumps(d))

if __name__=='__main__':
	app = wx.PySimpleApp()
	
	argv = sys.argv[1:]
	file = None
	if len(argv) in (2, 3) and argv[0] == "serve":
		port = int(argv[1])
		print "serving on port %d" % port
		server = SyncServer(port)
		player = server.player
		if len(argv) == 3: file = argv[2]
	elif len(argv) in (3, 4) and argv[0] == "connect":
		server = argv[1]
		port = int(argv[2])
		print "connecting to %s:%d" % (server, port)
		client = SyncClient(server, port)
		player = client.player
		if len(argv) == 4: file = argv[3]
	else:
		appName = "sync.py"
		print "\nvlc_sync\n\n"
		print "usage:"
		print "   server:  %s serve <port> [file]" % appName
		print "   client:  %s connect <server> <port> [file]" % appName
		sys.exit(1)
	
	if file is not None:
		player.open(file)
	
	networkThread = threading.Thread(target=lambda:asyncore.loop())
	networkThread.daemon = True
	networkThread.start()
	
	app.MainLoop()
	