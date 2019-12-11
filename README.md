# iio-python-2-in-1
Connect and read sensor data from IIO to use with 2 in 1 laptops

- `iio.py` listens to DBus signals from `iio-sensor-proxy` and automatically rotates screen+pen digitizer, and update brightness
- `tray.py` gives control over the daemon: click to disable auto bright, rightclick to open menu and disable auto rotation

## Config

For now in `iio.py` will be moved to a config file later

## TODO

- [X] xrandr
- [X] xinput set-props
- [X] xbacklight
- [ ] config file
- [X] update backlight when released
- [X] --pause on manual setting-- using systray we can activate/deactivate on click
- [X] systray icon
- [ ] code cleanup: setup proper classes, and remove `global` uses
- [ ] systemd service
- [ ] document setup
