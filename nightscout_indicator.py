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
__author__ = "Darrell Wright"
__copyright__ = "Copyright (C) 2016 Darrell Wright"

__revision__ = "$Id$"
__version__ = "0.1"

import urllib3
import requests
import signal
import gi
import time
import os
import io
import math
import configparser
import sys
import datetime

from multiprocessing import Pool

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Notify', '0.7')
from gi.repository import Gtk, AppIndicator3, GObject
from threading import Thread
from urllib.parse import urljoin

configfile_name = os.path.join(os.path.expanduser("~"), '.nightscout_indicator.yaml')

if not os.path.isfile(configfile_name):
    config = configparser.ConfigParser()
    config.add_section('main')
    config.set('main', 'night_scout_url_base', 'https://servername.dom/')
    with open(configfile_name, 'w') as f:
        config.write(f)
    print('Please update ' + configfile_name)
    quit()


class Indicator():
    def __init__(self):

        self.app = 'Nightscout Indicator'
        iconpath = "nightscout_indicator_icon"
        self.config = configparser.RawConfigParser()
        self.config.read(configfile_name)
        #self.indicator = AppIndicator3.Indicator.new(self.app, iconpath, AppIndicator3.IndicatorCategory.OTHER)
        self.indicator = AppIndicator3.Indicator.new_with_path(self.app, iconpath, AppIndicator3.IndicatorCategory.OTHER,  os.path.dirname(os.path.realpath(__file__) ) )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.create_menu())
        self.indicator.set_label("No Data", self.app)
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
        glucose = "No Data"
        url = urljoin(self.config.get('main', 'night_scout_url_base'), '/pebble')
        r = requests.get( url )
        if 200 != r.status_code:
            return "No Data"

        arrows = { 0:'', 1:'⇈', 2: '↑', 3:'↗', 4:'→', 5:'↘', 6: '↓', 7: '⇊' }
        glucose = 'No Data'
       # try:
        j = r.json( )
        bg_info = j['bgs'][0]
        last_info = math.floor((int( j['status'][0]['now'] ) - int(bg_info['datetime']))/60000)
        sgv = bg_info['sgv']
        if float( sgv ) == 0.7:
            result = 'No Signal'
        else:
            result = bg_info['sgv'] + ' ' + arrows[bg_info['trend']] + ' (' + bg_info['bgdelta'] + ') '

        result = result + '[' + str(last_info) + ']'
        glucose = result
        #except:
        #    pass

        return glucose

    def fetch_ns(self):
        t = 2
        while True:
            mention = self.fetch_ns_status()
            # apply the interface update using  GObject.idle_add()
            GObject.idle_add(self.indicator.set_label, mention, self.app, priority=GObject.PRIORITY_DEFAULT)
            time.sleep(60)
            t += 1

    def stop(self, source):
        Gtk.main_quit()

    def run(self):
        Gtk.main()

    def signal_exit(self, signum, frame):
        print( 'Recieved signal: ', signum )
        print( 'Quitting...' )
        self.stop( )

if __name__ == '__main__':
    try:
        app = Indicator( )
        signal.signal(signal.SIGTERM, app.signal_exit)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        app.run()
    except KeyboardInterrupt:
        app.stop()

