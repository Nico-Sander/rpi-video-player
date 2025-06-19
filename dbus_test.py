'''attempt at controlling omxplayer on Raspberry Pi over dbus with Python
launch the video with something like:
 $ omxplayer movie.mp4 -s --loop --no-osd --with-info
references:
https://github.com/andresromero/RPI-Cast/blob/master/omxplayer-dbus.py
https://github.com/popcornmix/omxplayer/blob/master/README.md#dbus-control
'''
import dbus, time

with open('/tmp/omxplayerdbus.pi', 'r+') as fd:
    sock_info = fd.read().strip()

bus = dbus.bus.BusConnection(sock_info)

obj = bus.get_object('org.mpris.MediaPlayer2.omxplayer',
                     '/org/mpris/MediaPlayer2', introspect=False)
ifp = dbus.Interface(obj, 'org.freedesktop.DBus.Properties')
ifk = dbus.Interface(obj, 'org.mpris.MediaPlayer2.Player')

# duration
print(ifp.Duration()) # in microseconds, one second is 1,000,000

# this works
#ifk.Pause()
#time.sleep(1)
#ifk.Play()

last_time = time.time()
for i in range(5):
    p = ifp.Position()
    t = time.time()
    print(p, t, t-last_time)
    last_time = t

# this doesn't work
r = ifk.SetPosition('', 2000000)
print(r, ifp.Position())
