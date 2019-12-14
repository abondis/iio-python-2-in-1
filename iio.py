# This program uses DBus to read data from iio-sensor-proxy
# refs:
#  - https://developer.gnome.org/iio-sensor-proxy/1.0/gdbus-net.hadess.SensorProxy.html#gdbus-property-net-hadess-SensorProxy.LightLevel
#  - https://dbus.freedesktop.org/doc/dbus-python/tutorial.html#receiving-signals-from-a-proxy-object
#  - https://github.com/mrquincle/yoga-900-auto-rotate
import dbus
import dbus.service
import math
import shlex
import subprocess
from dbus.mainloop.glib import DBusGMainLoop
config = {
    # adjust backlight calculation, default=8.0
    'lux_ratio': 14.0,
    # min backlight value
    'min_bl': 0.1,
    # orientation settings: dir is xrandr rotation param, matrix is xinput
    # matrix transformation
    'orientations': {
        'normal': {'dir': 'normal', 'matrix': '1 0 0 0 1 0 0 0 1'},
        'left-up': {'dir': 'left', 'matrix': '0 -1 1 1 0 0 0 0 1'},
        'bottom-up': {'dir': 'inverted', 'matrix': '-1 0 1 0 -1 1 0 0 1'},
        'right-up': {'dir': 'right', 'matrix': '0 1 0 -1 0 1 0 0 1'},
    },
    # list of devices to configure use the name or number from xinput list
    'devices': [
        "Wacom HID 485E Finger",
        "Wacom HID 485E Pen Pen (0x1c820027)",
    ],
    'screen': 'eDP1',
    # themes to use depending on screen brightness
    'themes': {
        'dark': {
            'name': 'Adwaita-dark',
            # TODO: move to script
            # NOTE: needs xfsettingsd running
            'cmd': 'xfconf-query -c xsettings -p /Net/ThemeName -s "{}"',
        },
        'light': {
            # TODO: move to script
            # NOTE: needs xfsettingsd running
            'cmd': 'xfconf-query -c xsettings -p /Net/ThemeName -s "{}"',
            'name': 'Adwaita-light',
        },
        'threshold': '10',
    }
}
LUX_RATIO = config.get('lux_ratio')
MIN_BL = config.get('min_bl')
ORIENTATIONS = config.get('orientations', {})
DEVS = config.get('devices', [])
SCREEN = config.get('screen', 'eDP1')
DARK_TH = config.get('themes', {}).get('dark')
LIGHT_TH = config.get('themes',{}).get('light')
TH_THRESHOLD = config.get('themes', {}).get('threshold')


DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()

iio = bus.get_object('net.hadess.SensorProxy',
                       '/net/hadess/SensorProxy')
iio_iface = dbus.Interface(iio,
    dbus_interface='net.hadess.SensorProxy')
accel = dbus.Interface(iio,
    dbus_interface='net.hadess.SensorProxy.AccelerometerOrientation')
# for properties
props_iface = dbus.Interface(iio, 'org.freedesktop.DBus.Properties')
# Call methods
iio_iface.ClaimLight()
iio_iface.ClaimAccelerometer()

claimed_accel = True
claimed_light = True


# list properties
# https://stackoverflow.com/a/24126305/5178528
props = props_iface.GetAll('net.hadess.SensorProxy')

# adjust backlight based on lux and formula
# https://docs.microsoft.com/en-us/windows/win32/sensorsapi/understanding-and-interpreting-lux-values?redirectedfrom=MSDN
unit = props['LightLevelUnit']
def adjust_lux(val):
    val = max(1, val)
    res = round(
        math.log10(val)/LUX_RATIO,
        3
    ) * 100
    return max(MIN_BL, res)

if unit == "lux":
    # adjust = lambda x: min(x, 1000) / 10
    adjust = adjust_lux
else:
    # if not lux ... use % brightness as the value to set the backlight
    # alternative : times 100k
    adjust = lambda x: x


def change_orientation(orientation):
    pos = ORIENTATIONS.get(orientation)
    if (pos is not None) and (SCREEN is not None):
        subprocess.check_call(['xrandr', '--output', SCREEN, '--rotate', pos['dir']])
        for dev in DEVS:
            try:
                subprocess.check_call(
                        [
                            'xinput', 'map-to-output', dev, SCREEN
                        ]
                )
            except:
                print(f"Could not map {dev} to {SCREEN}")
            # subprocess.check_call(
                    # [
                        # 'xinput', 'set-prop', dev,
                        # 'Coordinate Transformation Matrix',
                    # ] + pos['matrix'].split()
            # )

def call_theme_cmd(theme):
    if (
            (theme.get('name'))
            and (theme.get('cmd'))
    ):
        subprocess.check_call(
            shlex.split(
                theme['cmd'].format(
                    theme['name']
                )
            )
        )
        print("Theme changed!")

def update_backlight(lvl):
    br= "{0:.1f}".format(
        adjust(lvl)
    )
    if (br < TH_THRESHOLD):
        call_theme_cmd(DARK_TH)
    else:
        call_theme_cmd(LIGHT_TH)

    print("Yeah! light changed: " + br)
    subprocess.check_call(["xbacklight", "="+br])

# Match properties changed
def props_changed(sender, content, *args, **kwargs):
    orientation = content.get('AccelerometerOrientation')
    lvl = content.get('LightLevel')
    if orientation and claimed_accel:
        change_orientation(orientation)
        print("Yeah! orientation changed!" + str(claimed_accel))
    if lvl is not None and claimed_light:
        update_backlight(lvl)
    # print(content)

props_iface.connect_to_signal("PropertiesChanged", props_changed)

# listen for actions from widget
class Toggle(dbus.service.Object):
    def __init__(self, bus, object_path="/name/abondis/twoin1"):
        dbus.service.Object.__init__(self, bus, object_path)
        self.claimedLight = True
        self.claimedAccel = True

    @dbus.service.method(dbus_interface='name.abondis.twoin1',
                         in_signature='', out_signature='')
    def ToggleAccel(self):
        self.claimedAccel = not self.claimedAccel
        # FIXME: put everything in a class or pass toggle to the rest
        global claimed_accel
        claimed_accel = self.claimedAccel
        if self.claimedAccel:
            iio_iface.ClaimAccelerometer()
            print("Claimed Accel")
        else:
            iio_iface.ReleaseAccelerometer()
            print("Released Accel")

    @dbus.service.method(dbus_interface='name.abondis.twoin1',
                         in_signature='', out_signature='')
    def ToggleLight(self):
        self.claimedLight = not self.claimedLight
        global claimed_light
        claimed_light = self.claimedLight
        if self.claimedLight:
            iio_iface.ClaimLight()
            props = props_iface.GetAll('net.hadess.SensorProxy')
            update_backlight(props['LightLevel'])
            print("Claimed Light")
        else:
            iio_iface.ReleaseLight()
            print("Released Light")

if __name__ == "__main__":
    from gi.repository import GLib
    session_bus = dbus.SessionBus()
    name = dbus.service.BusName('name.abondis.twoin1', session_bus)
    toggle = Toggle(session_bus)

    loop = GLib.MainLoop()
    loop.run()
