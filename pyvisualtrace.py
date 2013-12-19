#!/usr/bin/python
'''
The MIT License (MIT)

Copyright (c) 2013 Quentin Gibert

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

This product includes GeoLite2 data created by MaxMind, available from http://www.maxmind.com
'''

from gi.repository import Gtk, Gdk, GLib
import threading, subprocess, re, os, time, Image
import geoip2.database
import geoip2.models
import geoip2.errors

class MyWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Traceroute")

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(self.vbox)

        self.img = Gtk.Image.new_from_file("default.jpg")

        self.frame_rgb = Gtk.Frame(label='Map')
        self.frame_rgb.set_label_align(0.5, 0.5)
        self.frame_rgb.set_shadow_type(Gtk.ShadowType.IN)
        self.frame_rgb.add(self.img)

        self.vbox.pack_start(self.frame_rgb, True, True, 0)

        self.hbox = Gtk.Box(spacing=0)
        self.vbox.pack_start(self.hbox, False, False, 0)

        self.entry = Gtk.Entry()
        self.entry.set_text("www.example.com")
        self.hbox.pack_start(self.entry, True, True, 6)


        self.button1 = Gtk.Button(label="Trace")
        self.button1.connect("clicked", self.on_button_clicked)
        self.hbox.pack_start(self.button1, False, False, 6)

        self.statusbar = Gtk.Statusbar()
        self.vbox.pack_start(self.statusbar, False, False, 0)

    def on_button_clicked(self, widget):
        text = str(self.entry.get_text())
        self.button1.set_sensitive(False)
        threading.Thread(target=self.worker_trace, args=(text, )).start()

    def worker_trace(self, text):
        status_msg = "tracing " + str(text) + "..."
        print status_msg
        self.statusbar.push(self.statusbar.get_context_id("statusbar"), status_msg)
        ip_list = trace_route(str(text))
        locate_nodes(ip_list)
        trace_map()
        status_msg = "done tracing " + str(text) + "   "
        time.sleep(1)
        print status_msg
        self.statusbar.push(self.statusbar.get_context_id("statusbar"), status_msg)
        self.img.set_from_file("result.jpg")
        self.button1.set_sensitive(True)

def trace_route(host):
    output = subprocess.check_output(['traceroute', host])
    pattern = re.compile("\((\d+\.\d+\.\d+\.\d+)\)")
    ip_list = pattern.findall(output)
    del ip_list[0]
    del ip_list[0]
    return ip_list

def locate_nodes(ip_list):
    points = open("points.dat", "w")
    start_stop = open("start_stop.dat", "w")
    points_list = []
    reader = geoip2.database.Reader('GeoLite2-City.mmdb')
    for ip in ip_list:
        response = reader.city(ip)
        if response != None:
            print ip
            output = '''    Country: %s
    City: %s
    Latitude: %s
    Longitude: %s
        ''' % (response.country.iso_code,
            response.city.name,
            response.location.latitude,
            response.location.longitude)
            pts_output = '''%s %s 0.1\n''' % (response.location.longitude, response.location.latitude)
            points.write(pts_output)
            points_list.append(pts_output)
            print output
    stop = points_list.pop()
    start = points_list.pop(0)
    start_stop.write(str(start) + "\n" + str(stop))
    start_stop.close()
    points.close()

def trace_map():
    ps_file = open("map.ps", "w")
    os.environ['PATH'] = "/usr/lib/lightdm/lightdm:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/lib/gmt/bin"
    ps_map = subprocess.check_output(['pscoast', '-Rd', '-JN0/20c', '-Bg30', '-Dc', '-A10000', '-Ggray', '-P', '-X0.5c', '-Y10c', '-K'])
    ps_points = subprocess.check_output(['psxy', 'points.dat', '-O', '-Rd', '-JN', '-Dc', '-A10000', '-P', '-Sc', '-G0', '-K'])
    ps_start_stop = subprocess.check_output(['psxy', 'start_stop.dat', '-O', '-Rd', '-JN', '-Dc', '-A10000', '-P', '-Sc0.05', '-G255/0/0'])
    ps_file.write(ps_map)
    ps_file.write(ps_points)
    ps_file.write(ps_start_stop)
    ps_file.close()
    subprocess.call(['ps2raster', 'map.ps', '-Tj', '-A'])
    image = Image.open("map.jpg")
    width = 1024
    height = 520
    resized_img = image.resize((width, height), Image.ANTIALIAS)
    resized_img.save("result.jpg")


win = MyWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
GLib.threads_init()
Gdk.threads_init()
Gdk.threads_enter()
Gtk.main()
Gdk.threads_leave()
