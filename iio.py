#!/usr/bin/env python
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
try:
    from iioconfig import config
except:
    raise("No config file, please copy config.py.sample to config.py and modify accordingly")
LUX_RATIO = config.get('lux_ratio')
MIN_BL = config.get('min_bl')
ORIENTATIONS = config.get('orientations', {})
DEVS = config.get('devices', [])
SCREEN = config.get('screen', 'eDP1')
DARK_TH = config.get('themes', {}).get('dark')
LIGHT_TH = config.get('themes',{}).get('light')
THRESHOLD = config.get('threshold', 10)
INVERT = config.get('invert_cmd', 'xrandr-invert-colors')
BACKLIGHT = config.get('backlight_cmd', ['xbacklight', '='])

# Number of measurements to use to adjust value (ie: sensor is too sensitive)
NB_MSR = config.get('nb_msr', 1)
MSR_CPT = 0
MEAN_LGT = 0

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
inverted = False

def call_invert(do_invert):
    global inverted
    # DEBUG print('Is inverted ' + str(inverted))
    if (do_invert != inverted) and INVERT:
        inverted = do_invert
        subprocess.check_call(
            shlex.split(
                INVERT
            )
        )
    # DEBUG print('Is inverted ' + str(inverted))

def call_theme_cmd(theme):
    if theme is None:
        return
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
        # DEBUG print("Theme changed!")

def update_backlight(lvl):
    br= "{0:.1f}".format(
        adjust(lvl)
    )
    # DEBUG print("Yeah! light changed: " + br)
    # subprocess.check_call(["xbacklight", "="+br])
    subprocess.check_call(BACKLIGHT+[br])
    if (float(lvl) < float(THRESHOLD)):
        call_theme_cmd(DARK_TH)
        call_invert(True)
    else:
        call_theme_cmd(LIGHT_TH)
        call_invert(False)


# Match properties changed
def props_changed(sender, content, *args, **kwargs):
    global MSR_CPT, MEAN_LGT, NB_MSR
    orientation = content.get('AccelerometerOrientation')
    lvl = content.get('LightLevel')
    if orientation and claimed_accel:
        change_orientation(orientation)
        # DEBUG print("Yeah! orientation changed!" + str(claimed_accel))
    if lvl is not None and claimed_light:
        MSR_CPT -= 1
        MEAN_LGT += lvl
        if MSR_CPT <= 0:
            MSR_CPT = NB_MSR
            lvl = round(MEAN_LGT / (NB_MSR))
            MEAN_LGT = 0
            # DEBUG pprint(lvl)
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
            # DEBUG print("Claimed Accel")
        else:
            iio_iface.ReleaseAccelerometer()
            # DEBUG print("Released Accel")

    @dbus.service.method(dbus_interface='name.abondis.twoin1',
                         in_signature='', out_signature='')
    def ToggleLight(self):
        self.claimedLight = not self.claimedLight
        global claimed_light, NB_MSR, MSR_CPT, MEAN_LGT
        claimed_light = self.claimedLight
        if self.claimedLight:
            iio_iface.ClaimLight()
            props = props_iface.GetAll('net.hadess.SensorProxy')
            update_backlight(props['LightLevel'])
            # DEBUG print("Claimed Light")
        else:
            iio_iface.ReleaseLight()
            # DEBUG print("Released Light")

if __name__ == "__main__":
    from gi.repository import GLib
    session_bus = dbus.SessionBus()
    name = dbus.service.BusName('name.abondis.twoin1', session_bus)
    toggle = Toggle(session_bus)

    loop = GLib.MainLoop()
    loop.run()
