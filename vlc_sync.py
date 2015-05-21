import wx
import sys
from sync import SyncClient, SyncServer, startNetworkThread
import os
import pickle

class ConnectionDialog(wx.Dialog):
    def __init__(self, title, mode=None, server=None, port=None, ipv6=None):
        super(ConnectionDialog, self).__init__(None, style=wx.CAPTION) 
            
        self.SetTitle(title)
        
        pnl = wx.Panel(self, size=(250,200))
        gbs = wx.GridBagSizer(7, 7)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)        
        self.rbClient = wx.RadioButton(pnl, label='Client  ', style=wx.RB_GROUP)
        self.rbServer = wx.RadioButton(pnl, label='Server')
        self.rbClient.Bind(wx.EVT_RADIOBUTTON, self.onSelectMode)
        self.rbServer.Bind(wx.EVT_RADIOBUTTON, self.onSelectMode)
        if mode is not None:
            self.rbServer.SetValue(mode == "serve")
        hbox.Add(self.rbClient)
        hbox.Add(self.rbServer)
        gbs.Add(hbox, pos=(0, 0), span=(1,2), flag=wx.EXPAND | wx.ALL)
        
        self.serverInput = wx.TextCtrl(pnl, size=(250,-1))
        if server is not None:
            self.serverInput.SetValue(server)

        self.portInput = wx.TextCtrl(pnl, size=(50,-1))
        if port is not None:
            self.portInput.SetValue(str(port))
            
        self.cbIPV6 = wx.CheckBox(pnl, label="IPv6")
        if ipv6 is not None:
            self.cbIPV6.SetValue(ipv6)
    
        gbs.Add(wx.StaticText(pnl, label="Server:  "), pos=(1,0))
        gbs.Add(self.serverInput, pos=(1,1), flag=wx.EXPAND | wx.HORIZONTAL)
        gbs.Add(wx.StaticText(pnl, label="Port:"), pos=(2,0))
        gbs.Add(self.portInput, pos=(2,1))
        gbs.Add(self.cbIPV6, pos=(3,1))
        gbs.AddGrowableCol(1)
        gbs.AddGrowableRow(2)
        
        self.button = wx.Button(pnl, label="Start")
        gbs.Add(self.button, pos=(4,0), span=(1,2), flag=wx.EXPAND | wx.HORIZONTAL, border=5)
        self.button.Bind(wx.EVT_BUTTON, self.onStart)
        
        pnl.SetSizerAndFit(gbs)
        
        hbox = wx.BoxSizer(wx.VERTICAL)
        hbox.Add(pnl, proportion=1, flag=wx.ALL|wx.EXPAND, border=15)
        self.SetSizerAndFit(hbox)
        
        self.onSelectMode(None)
    
    def onSelectMode(self, evt):
        if self.rbClient.GetValue():
            self.serverInput.Enable()
        else:
            self.serverInput.Disable()
    
    def onStart(self, evt):
        self.Close(True)
    
    def getData(self):
        return ("connect" if self.rbClient.GetValue() else "serve", self.serverInput.GetValue(), self.portInput.GetValue(), self.cbIPV6.GetValue())

if __name__=='__main__':
    app = wx.App(redirect=False)
    
    argv = sys.argv[1:]
    if len(argv) == 0:
        argv = ["--gui"]
    
    file = None
    mode = None
    server = None
    port = None
    ipv6 = False
    help = False
    gui = False
    while len(argv) > 0:
        a = argv[0]
        if a == "serve" and len(argv) in (2, 3):
            mode = a
            port = int(argv[1])
            if len(argv) == 3: file = argv[2]
            break
        elif a == "connect" and len(argv) in (3, 4):
            mode = a
            server = argv[1]
            port = int(argv[2])
            if len(argv) == 4: file = argv[3]
            break
        elif a == "--ipv6":
            ipv6 = True            
        elif a == "--gui":
            gui = True
        elif a in ("--help", "-?", "-h", "/?", "/h"):
            help = True
            break
        else:
            print "invalid series of arguments: %s" % str(argv)
            help = True
            break
        argv = argv[1:]
    
    if not gui and mode is None:
        help = True
            
    if help:
        appName = "vlc_sync"
        print "\nvlc_sync by Dominik Jain\n\n"
        print "usage:"
        print "   server:  %s [options] [serve <port> [file]]" % appName
        print "   client:  %s [options] [connect <server> <port> [file]]" % appName
        print "\noptions:"
        print "   --ipv6   use IPv6 instead of IPv4"
        print "   --gui    use GUI to specify client/server parameters"
        sys.exit(0)

    home = os.path.expanduser("~")
    configfile = os.path.join(home, ".vlc_sync")
    
    def openPlayer():
        print "parameters: %s" % str((mode, server, port, ipv6))
        with open(configfile, "wb") as f:
            pickle.dump({"mode":mode, "server":server, "port":port, "ipv6":ipv6}, f)
        if mode == "serve":
            print "serving on port %d" % port
            player = SyncServer(port, ipv6=ipv6).player
        else:
            print "connecting to %s:%d" % (server, port)
            player = SyncClient(server, port, ipv6=ipv6).player
        
        if file is not None:
            player.open(file)
    
        startNetworkThread()

    if not gui:
        openPlayer()
    else:
        if mode is None:
            if os.path.exists(configfile):
                with open(configfile, "rb") as f:
                    try:
                        config = pickle.load(f)
                    except:
                        config = {}
                mode = config.get("mode")
                server = config.get("server")
                port = config.get("port")
                ipv6 = config.get("ipv6")
        dlg = ConnectionDialog("VLC_SYNC", mode=mode, server=server, port=port, ipv6=ipv6)
        dlg.ShowModal()
        mode, server, port, ipv6 = dlg.getData()
        port = int(port)
        dlg.Destroy()
        openPlayer()        
    
    app.MainLoop()