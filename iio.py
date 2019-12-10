# This program uses DBus to read data from iio-sensor-proxy
# refs:
#  - https://developer.gnome.org/iio-sensor-proxy/1.0/gdbus-net.hadess.SensorProxy.html#gdbus-property-net-hadess-SensorProxy.LightLevel
#  - https://dbus.freedesktop.org/doc/dbus-python/tutorial.html#receiving-signals-from-a-proxy-object
#  - https://github.com/mrquincle/yoga-900-auto-rotate
import dbus
import math
import subprocess
from dbus.mainloop.glib import DBusGMainLoop

DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()

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
# list properties
# https://stackoverflow.com/a/24126305/5178528
props = props_iface.GetAll('net.hadess.SensorProxy')

# adjust backlight based on lux and formula
# https://docs.microsoft.com/en-us/windows/win32/sensorsapi/understanding-and-interpreting-lux-values?redirectedfrom=MSDN
unit = props['LightLevelUnit']
def adjust_lux(val):
    val = max(1, val)
    # TODO: put ratio in conf
    res = round(
        math.log10(val)/8.0,
        3
    ) * 100
    # TODO: put min value in conf
    return max(0.1, res)

if unit == "lux":
    # adjust = lambda x: min(x, 1000) / 10
    adjust = adjust_lux
else:
    # if not lux ... use % brightness as the value to set the backlight
    # alternative : times 100k
    adjust = lambda x: x

ORIENTATIONS = {
    'normal': {'dir': 'normal', 'matrix': '1 0 0 0 1 0 0 0 1'},
    'left-up': {'dir': 'left', 'matrix': '0 -1 1 1 0 0 0 0 1'},
    'bottom-up': {'dir': 'inverted', 'matrix': '-1 0 1 0 -1 1 0 0 1'},
    'right-up': {'dir': 'right', 'matrix': '0 1 0 -1 0 1 0 0 1'},
}

DEV = str(11)
def change_orientation(orientation):
    pos = ORIENTATIONS[orientation]
    subprocess.check_call(['xrandr', '-o', pos['dir']])
    print(
                'xinput', 'set-prop', DEV,
                '"Coordinate Transformation Matrix"',
                pos['matrix'].split()
    )
    subprocess.check_call(["echo", "blah"])
    subprocess.check_call(
            [
                'xinput', 'set-prop', DEV,
                'Coordinate Transformation Matrix',
            ] + pos['matrix'].split()
    )

# Match properties changed
def props_changed(sender, content, *args, **kwargs):
    orientation = content.get('AccelerometerOrientation')
    lvl = content.get('LightLevel')
    if orientation:
        change_orientation(orientation)
        print("Yeah! orientation changed!")
    if lvl is not None:
        br= "{0:.1f}".format(
            adjust(lvl)
        )
        print("Yeah! light changed: " + br)
        subprocess.check_call(["xbacklight", "="+br])
    print(content)

props_iface.connect_to_signal("PropertiesChanged", props_changed)

if __name__ == "__main__":
    from gi.repository import GLib
    
    loop = GLib.MainLoop()
    loop.run()
