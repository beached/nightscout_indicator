#!/usr/bin/env python3

# MIT License
# 
# Copyright (c) 2016 Darrell Wright
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import urllib3
import signal
import json
import gi
import time
import os
import io
import configparser
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1') 
gi.require_version('Notify', '0.7')
from gi.repository import Gtk, AppIndicator3, GObject
from threading import Thread
from urllib.parse import urljoin

configfile_name = os.path.join(os.path.expanduser("~"), '.ns_indicator.yaml' )

if not os.path.isfile(configfile_name):
    config = configparser.ConfigParser( )
    config.add_section('main')
    config.set('main', 'night_scout_url_base', 'https://servername.dom/')
    with open( configfile_name, 'w' ) as f:
        config.write( f )
    print( 'Please update ' + configfile_name )
    quit()

class Indicator():
    def __init__(self):

        self.app = 'Nightscout Indicator'
        iconpath = "/opt/abouttime/icon/indicator_icon.png"
        self.config = configparser.RawConfigParser( )
        self.config.read( configfile_name )

        self.indicator = AppIndicator3.Indicator.new( self.app, iconpath, AppIndicator3.IndicatorCategory.OTHER )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.create_menu())
        self.indicator.set_label("NO Data", self.app)
        # the thread:
        self.update = Thread(target=self.fetch_ns)
        # daemonize the thread to make the indicator stopable
        self.update.setDaemon(True)
        self.update.start()

    def create_menu(self):
        menu = Gtk.Menu()
        # menu item 1
        # separator
        # quit
        item_quit = Gtk.MenuItem('Quit')
        item_quit.connect('activate', self.stop)
        menu.append(item_quit)

        menu.show_all()
        return menu

    def fetch_ns_status(self):
        http = urllib3.PoolManager( )
        url = urljoin( self.config.get( 'main', 'night_scout_url_base' ), '/pebble' )
        r = http.request( 'GET', url )
        if 200 != r.status:
            return "No Data"
        glucose = json.loads( r.data.decode( 'utf-8' ))['bgs'][0]['sgv']
        return glucose

    def fetch_ns(self):
        t = 2
        while True:
            mention = self.fetch_ns_status( )
            # apply the interface update using  GObject.idle_add()
            GObject.idle_add( self.indicator.set_label, mention, self.app, priority=GObject.PRIORITY_DEFAULT )
            time.sleep(60)
            t += 1

    def stop(self, source):
        Gtk.main_quit()

Indicator()
# this is where we call GObject.threads_init()
GObject.threads_init()
signal.signal(signal.SIGINT, signal.SIG_DFL)
Gtk.main()
