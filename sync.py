import socket
import sys
import threading
import pickle
import wx
import asyncore
from wxvlc import Player

class DispatchingPlayer(Player):
	def __init__(self, title, dispatcher):
		Player.__init__(self, title)
		self.dispatcher = dispatcher
		self.Centre()
		self.Show()

	def OnPlay(self, evt, dispatch=True):
		super(DispatchingPlayer, self).OnPlay(evt)
		if dispatch: self.dispatcher.dispatch({"evt": "OnPlay", "args": (None,)})
	
	def OnPause(self, evt, dispatch=True):
		super(DispatchingPlayer, self).OnPause(evt)
		if dispatch: self.dispatcher.dispatch({"evt": "OnPause", "args": (None,)})
	
	def handleNetworkEvent(self, d):
		evt = d["evt"]
		if evt == "OnPlay":
			Player.OnPlay(self.player, None)
		elif evt == "OnPause":
			Player.OnPause(self.player, None)

class SyncServer(asyncore.dispatcher):
	def __init__(self, port):
		asyncore.dispatcher.__init__(self)
		# start listening for connections
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		#self.set_reuse_addr()
		host = ""
		self.bind((host, port))
		self.connections = []
		self.listen(5)
		# create actual player
		player = DispatchingPlayer("Sync'd VLC Server", self)		
	
	def handle_accept(self):		
		pair = self.accept()
		if pair is None:
			return
		print "got connection from %s" % str(pair[1])
		conn = DispatcherConnection(pair[0], self)
		self.connections.append(conn)
		conn.sendData("hello %s" % str(pair[1]))

	def dispatch(self, d):
		print "dispatching %s" % str(d)
		for c in self.connections:
			c.sendData(d)

class DispatcherConnection(asyncore.dispatcher_with_send):
	def __init__(self, connection, server):
		asyncore.dispatcher_with_send.__init__(self, connection)
		self.server = server

	def writable(self):
		return bool(self.out_buffer)

	def handle_write(self):
		self.initiate_send()

	#def log(self, message):
	#    self.mainwindow.LogString(message, sock=self)

	#def log_info(self, message, type='info'):
	#    if type != 'info':
	#        self.log(message)

	def handle_read(self):
		d = pickle.loads(self.recv(8192))
		print "received: %s " % d
		if type(d) == dict and "evt" in d:
			self.player.handleNetworkEvent(d)

	def handle_close(self):
		self.log("Connection dropped: %s"%(self.addr,))
		self.close()

	def sendData(self, d):
		print "sending %s" % str(d)
		self.send(pickle.dumps(d))

class SyncClient(asyncore.dispatcher):	
	def __init__(self, server, port):
		asyncore.dispatcher.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)		
		ret = self.connect((server, port))
		print ret
		# create actual player
		self.player = DispatchingPlayer("Sync'd VLC Client", self)	
		
	def handle_read(self):
		d = pickle.loads(self.recv(8192))
		print "received: %s " % d
		if type(d) == dict and "evt" in d:
			self.player.handleNetworkEvent(d)
	
	def dispatch(self, d):
		print "sending %s" % str(d)
		self.send(pickle.dumps(d))

def networkLoop():
	while True:
		asyncore.poll(0.01)

if __name__=='__main__':
	app = wx.PySimpleApp()
	
	argv = sys.argv[1:]
	if argv[0] == "serve":
		port = int(argv[1])
		print "serving on port %d" % port
		server = SyncServer(port)
	elif argv[0] == "connect":
		server = argv[1]
		port = int(argv[2])
		print "connecting to %s:%d" % (server, port)
		client = SyncClient(server, port)
	else:
		print "usage: TODO"
		sys.exit(1)
	
	networkThread = threading.Thread(target=networkLoop)
	networkThread.daemon = True
	networkThread.start()
	
	app.MainLoop()
	