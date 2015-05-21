![vlc_sync](http://www.power-xs.net/opcode/nop/software/external/vlc-sync.jpg)

**vlc_sync** is a synchronizing video player for social video watching.

It allows you to watch videos with your friends even though they are not in front of the same screen. The program can synchronize play, pause and seek operations across several computers all running vlc\_sync with the same video file loaded. 

To complete the social experience, fire up a voice chat application such as Skype alongside it to share your thoughts.

As the name suggests, vlc\_sync builds upon the technology of VideoLAN's famous VLC media player, which can flawlessly play most videos out there. vlc\_sync is written in Python and thus supports a wide range of platforms. If a computer runs VLC media player, it will typically run vlc\_sync, too.

## Prerequisites ##

To run the source version of vlc_sync, you will need to have the following software installed:

- [VLC media player](http://www.videolan.org/vlc/index.html)
- [Python 2.x](https://www.python.org/downloads/) version 2.5 or newer
- [wxPython](http://www.wxpython.org/)

**VLC media player version compatibility**

vlc_sync was successfully tested with [VLC media player v1.1.x](http://download.videolan.org/pub/videolan/vlc/1.1.11/) on Windows and Linux. Other versions may work, but certain 2.x versions are known not to work correctly *on Windows*, while no issues have yet been reported on Linux. 

If your version of VLC media player turns out to be incompatible, you *need not downgrade* your installation. Instead, on Windows, copy the .dll files from the [ZIP file of version 1.1.11](http://download.videolan.org/pub/videolan/vlc/1.1.11/win32/vlc-1.1.11-win32.zip) to the vlc\_sync directory and you are good to go. 

## Usage ##

The general procedure is this:

- Start a vlc\_sync server
- Start one or more vlc\_sync clients on remote machines, connecting to the previously started server
- Load the desired video file on all machines
- Seek, play and pause are synchronized. Enjoy the video.

The Python script `vlc_sync.py` is used to spawn both servers and clients. Simply run the script from the command line and a dialog prompting for connection parameters will appear. Alternatively, connection parameters may be specified directly from the command line. Run the script with parameter `--help` for additional information. 

Note that for connections to be established, a port on the computer running the server must be reachable to the clients (which may necessitate changes to the home network's routing or firewall configuration).
