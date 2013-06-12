#! /usr/bin/python
# -*- coding: utf-8 -*-

#
# WX example for VLC Python bindings
# Copyright (C) 2009-2010 the VideoLAN team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
#

# import external libraries
import wx # 2.8
import vlc

# import standard libraries
import os
import user
import time

class Player(wx.Frame):
    """The main window has to deal with events.
    """
    def __init__(self, title):
        wx.Frame.__init__(self, None, -1, title, pos=wx.DefaultPosition, size=(550, 500))
        self.title = title

        # Menu Bar        
        self.frame_menubar = wx.MenuBar()
        self.SetMenuBar(self.frame_menubar)
        # - file Menu
        self.file_menu = wx.Menu()
        self.file_menu.Append(1, "&Open", "Open from file..")
        self.file_menu.AppendSeparator()
        self.file_menu.Append(2, "&Close", "Quit")
        self.Bind(wx.EVT_MENU, self.OnOpen, id=1)
        self.Bind(wx.EVT_MENU, self.OnExit, id=2)
        self.frame_menubar.Append(self.file_menu, "File")
        # - transport menu
        self.transport_menu = wx.Menu()
        playMI = self.transport_menu.Append(wx.ID_ANY, "Play/Pause\tSpace")
        self.Bind(wx.EVT_MENU, self.OnPlayPause, id=playMI.GetId())
        self.frame_menubar.Append(self.transport_menu, "Transport")
        # - audio Menu
        self.audio_menu = wx.Menu()
        self.audio_menu_items = {}
        self.frame_menubar.Append(self.audio_menu, "Audio")
        # - video menu
        self.view_menu = wx.Menu()
        fullScreenMI = self.view_menu.Append(wx.ID_ANY,"Full Screen\tF12", "Toggles Full Screen Mode")
        self.Bind(wx.EVT_MENU, self.OnToggleFullScreen, id=fullScreenMI.GetId())        
        self.frame_menubar.Append(self.view_menu, "View")

        # Panels
        # The first panel holds the video and it's all black
        self.videopanel = wx.Panel(self, -1)
        self.videopanel.SetBackgroundColour(wx.BLACK)

        # The second panel holds controls
        ctrlpanel = wx.Panel(self, -1)
        self.ctrlpanel = ctrlpanel
        self.timeslider = wx.Slider(ctrlpanel, -1, 0, 0, 1000)
        self.timeslider.SetRange(0, 1000)
        pause  = wx.Button(ctrlpanel, label="Pause")
        play   = wx.Button(ctrlpanel, label="Play")
        stop   = wx.Button(ctrlpanel, label="Stop")
        volume = wx.Button(ctrlpanel, label="Mute")
        self.volslider = wx.Slider(ctrlpanel, -1, 0, 0, 100, size=(100, -1))
        self.timeDisplay = wx.StaticText(ctrlpanel, label=" 0:00:00", style=wx.ALIGN_RIGHT)

        # Bind controls to events
        self.Bind(wx.EVT_BUTTON, self.OnPlay, play)
        self.Bind(wx.EVT_BUTTON, self.OnPause, pause)
        self.Bind(wx.EVT_BUTTON, self.OnStop, stop)
        self.Bind(wx.EVT_BUTTON, self.OnToggleVolume, volume)
        self.Bind(wx.EVT_SLIDER, self.OnSetVolume, self.volslider)
        self.Bind(wx.EVT_SLIDER, self.OnMoveTimeSlider, self.timeslider)        

        # Give a pretty layout to the controls        
        ctrlbox = wx.BoxSizer(wx.VERTICAL)
        box1 = wx.BoxSizer(wx.HORIZONTAL)
        box2 = wx.BoxSizer(wx.HORIZONTAL)
        # box1 contains the timeslider
        box1.Add(self.timeDisplay, flag=wx.CENTER)
        box1.Add(self.timeslider, 1)
        # box2 contains some buttons and the volume controls
        box2.Add(play, flag=wx.RIGHT, border=0)
        box2.Add(pause)
        box2.Add(stop)        
        box2.Add((-1, -1), 1)
        box2.Add(volume)
        box2.Add(self.volslider, flag=wx.TOP | wx.LEFT, border=5)
        # Merge box1 and box2 to the ctrlsizer
        ctrlbox.Add(box1, flag=wx.EXPAND | wx.BOTTOM, border=10)
        ctrlbox.Add(box2, 1, wx.EXPAND)        
        ctrlpanel.SetSizer(ctrlbox)
        # Put everything together
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.videopanel, 1, flag=wx.EXPAND)
        sizer.Add(ctrlpanel, flag=wx.EXPAND | wx.BOTTOM | wx.TOP, border=0)
        self.SetSizer(sizer)
        
        self.SetMinSize((350, 300))        
        self.fullscreen = False        

        # finally create the timer, which updates the timeslider
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

        # VLC player controls
        self.Instance = vlc.Instance()
        self.player = self.Instance.media_player_new()        

    def play(self):
        if self.player.play() != -1:
            wx.CallAfter(self.timer.Start, 75)
    
    def pause(self):
        self.player.set_pause(1)
    
    def seek(self, time):
        self.player.set_time(time)
        
    def updateTimeSlider(self):
        # update length
        length = self.player.get_length()
        self.timeslider.SetRange(0, length)
        # update the time on the slider
        currentTime = self.getTime()
        self.timeslider.SetValue(currentTime)
        # update time display
        secs = currentTime / 1000        
        minutes = secs / 60
        hours = minutes / 60
        secs = secs % 60
        minutes = minutes % 60
        display = " %d:%02d:%02d" % (hours, minutes, secs)
        self.timeDisplay.SetLabel(display)
    
    def getTime(self):
        return self.player.get_time()

    def getMedia(self):
        return self.player.get_media()
    
    def isPlaying(self):
        return self.player.is_playing()

    def isPaused(self):
        return self.player.get_state() == vlc.State.Paused
    
    def open(self, path):
        self.Media = self.Instance.media_new(unicode(path))
        self.player.set_media(self.Media)
        # Report the title of the file chosen
        title = self.player.get_title()
        #  if an error was encountred while retriving the title, then use
        #  filename
        filename = os.path.basename(path)
        if title == -1:
            title = filename
        self.SetTitle("%s - %s" % (title, self.title))
        
        # set the window id where to render VLC's video output
        self.player.set_xwindow(self.videopanel.GetHandle()) # for Linux/Unix
        self.player.set_hwnd(self.videopanel.GetHandle()) # for Windows

        self.play()

        # wait until the video is really playing, so audio track query will work
        while not self.player.is_playing():
            time.sleep(0.01)
        
        # update audio menu
        for audio_track in self.audio_menu_items.values():
            self.audio_menu.RemoveItem(audio_track["menu_item"])
        self.audio_menu_items = {}
        self.player.video_get_track_description()
        tracks = self.player.audio_get_track_description() 
        if len(tracks) == 0: tracks = [(-1, "None"), (1, "1"), (2, "2")] # fallback (should no longer be required)
        for (track_no, name) in tracks:
            menu_item = self.audio_menu.Append(wx.ID_ANY, name)
            id = menu_item.GetId()
            self.audio_menu_items[id] = {"menu_item": menu_item, "track_no": track_no}
            self.Bind(wx.EVT_MENU, self.OnSelectAudioTrack, id=id)

        # set the volume slider to the current volume
        self.volslider.SetValue(self.player.audio_get_volume() / 2)

    
    def OnExit(self, evt):
        """Closes the window.
        """
        self.Close()

    def OnOpen(self, evt):
        """Pop up a new dialow window to choose a file, then play the selected file.
        """
        # if a file is already running, then stop it.
        #self.OnStop(None)

        # Create a file dialog opened in the current home directory, where
        # you can display all kind of files, having as title "Choose a file".
        dlg = wx.FileDialog(self, "Choose a file", user.home, "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            dirname = dlg.GetDirectory()
            filename = dlg.GetFilename()
            self.open(os.path.join(dirname, filename))

        # finally destroy the dialog
        dlg.Destroy()
    
    def OnSelectAudioTrack(self, evt):
        track = self.audio_menu_items[evt.GetId()]["track_no"]
        print "switching to audio track %d" % track
        self.player.audio_set_track(track)

    def OnPlay(self, evt):
        """Toggle the status to Play/Pause.

        If no file is loaded, open the dialog window.
        """
        # check if there is a file to play, otherwise open a
        # wx.FileDialog to select a file
        if self.getMedia() is None:
            self.OnOpen(None)
        else:
            self.play()
    
    def OnPause(self, evt):
        """Pause the player.
        """
        self.pause()

    def OnStop(self, evt):
        """Stop the player.
        """
        self.player.stop()
        # reset the time slider
        self.timeslider.SetValue(0)
        wx.CallAfter(self.timer.Stop)

    def OnTimer(self, evt):
        """Update the time slider according to the current movie time.
        """
        # since the self.player.get_length can change while playing,
        # re-set the timeslider to the correct range.
        self.updateTimeSlider()

    def OnToggleVolume(self, evt):
        """Mute/Unmute according to the audio button.
        """
        is_mute = self.player.audio_get_mute()

        self.player.audio_set_mute(not is_mute)
        # update the volume slider;
        # since vlc volume range is in [0, 200],
        # and our volume slider has range [0, 100], just divide by 2.
        self.volslider.SetValue(self.player.audio_get_volume() / 2)

    def OnSetVolume(self, evt):
        """Set the volume according to the volume sider.
        """
        volume = self.volslider.GetValue() * 2
        # vlc.MediaPlayer.audio_set_volume returns 0 if success, -1 otherwise
        if self.player.audio_set_volume(volume) == -1:
            self.errorDialog("Failed to set volume")
    
    def OnMoveTimeSlider(self, evt):
        time = self.timeslider.GetValue()
        self.OnSeek(time)
    
    def OnSeek(self, time):
        self.seek(time)
    
    def OnPlayPause(self, evt):
        if self.isPaused():
            self.OnPlay(None)
        else:
            self.OnPause(None)
    
    def OnToggleFullScreen(self, evt):
        self.fullscreen = not self.fullscreen
        self.ctrlpanel.Show(not self.fullscreen)
        self.ShowFullScreen(self.fullscreen)        

    def errorDialog(self, errormessage):
        """Display a simple error dialog.
        """
        edialog = wx.MessageDialog(self, errormessage, 'Error', wx.OK | wx.ICON_ERROR)
        edialog.ShowModal()
    
    def questionDialog(self, message, title = "Error"):
        """Displays a yes/no dialog, returning true if the user clicked yes, false otherwise
        """
        return wx.MessageDialog(self, message, title, wx.YES_NO | wx.ICON_QUESTION).ShowModal() == wx.ID_YES

if __name__ == "__main__":
    # Create a wx.App(), which handles the windowing system event loop
    app = wx.PySimpleApp()
    # Create the window containing our small media player
    player = Player("Simple PyVLC Player")
    # show the player window centred and run the application
    player.Centre()
    player.Show()
    app.MainLoop()
