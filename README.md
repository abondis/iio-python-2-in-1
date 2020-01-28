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
- put iio.py in path (`ln -s (pwd)/iio.py ~/.local/bin/`)
- add service to user systemd (`ln -s (pwd)/iio-python.service ~/.config/systemd/user/iio-python.service`)
- enable user service (`systemd --user enable iio-python`)

## Config

For now in `iio.py` will be moved to a config file later
In order to use `xrandr-inverse-color` compile and install https://github.com/zoltanp/xrandr-invert-colors

## TODO

- [X] xrandr
- [X] xinput set-props
- [X] xbacklight
- [X] config file
- [X] update backlight when released
- [X] --pause on manual setting-- using systray we can activate/deactivate on click
- [X] systray icon
- [ ] code cleanup: setup proper classes, and remove `global` uses
- [X] systemd service
- [X] change themes on the fly
- [X] change colors on the fly
- [X] document setup
- [ ] change colors (ie: yellow with xrandr?) depending on brightness
- [X] FIX: if pen was not detected -> exception, should warn or silent fail
