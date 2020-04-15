# iio-python-2-in-1
Connect and read sensor data from IIO to use with 2 in 1 laptops

- `iio.py` listens to DBus signals from `iio-sensor-proxy` and automatically rotates screen+pen digitizer, and update brightness
- `tray.py` gives control over the daemon: click to disable auto bright, rightclick to open menu and disable auto rotation

## What is it?!
Everything is optional and configurable
- auto rotates the screen, fixing the pen/finger orientation with it
- changes brightness based on light sensors
- changes themes on the fly based on light brightness threshold. For example in
  the dark a dark theme might be easier on the eyes
- adds a systray icon to toggle/lock settings

## Install
- clone
- copy or create iioconfig.py based on `iioconfig.py.sample`
- put iio.py in path (`ln -s (pwd)/iio.py ~/.local/bin/`)
- add service to user systemd (`ln -s (pwd)/iio-python.service ~/.config/systemd/user/iio-python.service`)
- enable user service (`systemd --user enable iio-python`)

## Config

There is a configuration example `iioconfig.py.sample`
In order to use `xrandr-inverse-color` compile and install https://github.com/zoltanp/xrandr-invert-colors

### Rotation mapping is incorrect

Apparently rectifying the information given by iiosensors should be as simple as
giving the proper matrix to ACCEL_MOUNT_MATRIX ( see
https://github.com/systemd/systemd/blob/master/hwdb.d/60-sensor.hwdb and
https://gitlab.freedesktop.org/hadess/iio-sensor-proxy/#accelerometer-orientation
) ... That didn't work for me ...

In order to address this using this repo, reorder the `dir` attributes of the
`orientations` setting  in `iioconfig.py`:

``` python
config = {
  # some settings
  # ...
  'orientations': {
    'normal': {'dir': 'normal'},
    'left-up': {'dir': 'left'},
    'bottom-up': {'dir': 'inverted'},
    'right-up': {'dir': 'right'},
  }
  # ...
  # some other settings
}
```

### Changing themes based on screen brightness

See `iioconfig.py.sample` in the section `themes` for an example with XFCE

### Changing colors in low luminosity environment

In `iioconfig.py` there are two setting:
  - `threshold`: the backlight threshold for low luminosity environment
  - `invert_cmd`: The command to call when changing backlight threshold (ie:
    from low to high luminosity)
    
## Tray applet

The tray applet lets you temporarily activate/deactivate automatic behaviours,
such as auto rotate or auto brightness. Run `tray.py`, for example at session
launch. If for any reason it doesn't work, it might have trouble with dbus. In
that case use the `restart` action in the applet's menu.

## TODO

- [X] xrandr
- [X] xinput set-props
- [X] backlight
- [X] config file
- [X] update backlight when released
- [X] --pause on manual setting-- using systray we can activate/deactivate on click
- [X] systray icon
- [ ] code cleanup: setup proper classes, and remove `global` uses
- [X] systemd service
- [X] change themes on the fly
- [X] change colors on the fly
- [X] document setup
- [X] change colors (ie: yellow with xrandr?) depending on brightness
- [X] FIX: if pen was not detected -> exception, should warn or silent fail
