#!/usr/bin/python
import os
import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk as gtk, GLib

try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3 as appindicator
except (ImportError, ValueError):
    appindicator = None
import dbus
bus = dbus.SessionBus()

def dbus_iface():
    _2in1 = bus.get_object('name.abondis.twoin1',
                       '/name/abondis/twoin1')
    return dbus.Interface(
            _2in1,
            dbus_interface='name.abondis.twoin1'
            )
_2in1_iface = dbus_iface()

def toggleAccel(widget, data=None):
    print('toggling Accel')
    _2in1_iface.ToggleAccel()

def toggleLight(widget, data=None):
    print('toggling Light')
    _2in1_iface.ToggleLight()

def restart(_):
    global _2in1_iface
    _2in1_iface = dbus_iface()


def show_menu(menu, icon):
    def menu_cb(widget, button, time, data=None):
        menu.show_all()
        menu.popup(
                None,
                None,
                gtk.StatusIcon.position_menu,
                icon,
                button,
                time
                )
    return menu_cb

def main():
    _menu = menu()
    if appindicator:
        indicator = appindicator.Indicator.new(
                "2in1",
                "preferences-desktop-screensaver",
                appindicator.IndicatorCategory.APPLICATION_STATUS
                )
        indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        indicator.set_menu(_menu)
    else:
        status_icon = gtk.StatusIcon()
        status_icon.set_from_icon_name('preferences-desktop-screensaver')
        status_icon.set_tooltip_text('Manage 2in1 stuff')
    if not appindicator:
        # Connect signals for status icon and show
        status_icon.connect('activate', toggleLight)
        status_icon.connect(
                'popup-menu',
                show_menu(_menu, status_icon)
                )
        status_icon.set_visible(True)
    gtk.main()

def menu():
  menu = gtk.Menu()
  
  command_one = gtk.CheckMenuItem.new_with_label('Toggle Rotation')
  command_one.connect('activate', toggleAccel)
  menu.append(command_one)
  restarttray = gtk.MenuItem.new_with_label('Restart Tray')
  restarttray.connect('activate', restart)
  exittray = gtk.MenuItem.new_with_label('Exit Tray')
  exittray.connect('activate', quit)
  menu.append(restarttray)
  menu.append(exittray)
  
  return menu
  
def note(_):
  os.system("gedit $HOME/Documents/notes.txt")
def quit(_):
  gtk.main_quit()
if __name__ == "__main__":
  main()
