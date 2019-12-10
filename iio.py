# This program uses DBus to read data from iio-sensor-proxy
# refs:
#  - https://developer.gnome.org/iio-sensor-proxy/1.0/gdbus-net.hadess.SensorProxy.html#gdbus-property-net-hadess-SensorProxy.LightLevel
#  - https://dbus.freedesktop.org/doc/dbus-python/tutorial.html#receiving-signals-from-a-proxy-object
#  - https://github.com/mrquincle/yoga-900-auto-rotate
import dbus
from dbus.mainloop.glib import DBusGMainLoop

DBusGMainLoop(set_as_default=True)
# bus = dbus.SessionBus()
bus = dbus.SystemBus()

def props_changed(sender, content, *args, **kwargs):
    if 'AccelerometerOrientation' in content:
        print("Yeah! orientation changed!")
    if 'LightLevel' in content:
        print("Yeah! light changed!")
    print("received something: args: ")
    print(args)
    print("kwargs:")
    print(kwargs)

iio = bus.get_object('net.hadess.SensorProxy',
                       '/net/hadess/SensorProxy')
iio_iface = dbus.Interface(iio,
    dbus_interface='net.hadess.SensorProxy')
accel = dbus.Interface(iio,
    dbus_interface='net.hadess.SensorProxy.AccelerometerOrientation')
# Call methods
iio_iface.ClaimLight()
iio_iface.ClaimAccelerometer()


props_iface = dbus.Interface(iio, 'org.freedesktop.DBus.Properties')
# Match properties changed
props_iface.connect_to_signal("PropertiesChanged", props_changed)
# list properties
# https://stackoverflow.com/a/24126305/5178528
print(props_iface.GetAll('net.hadess.SensorProxy'))

if __name__ == "__main__":
    from gi.repository import GLib
    
    loop = GLib.MainLoop()
    loop.run()
