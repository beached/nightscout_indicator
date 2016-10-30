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

import requests
import signal
import gi
import time
import os
import io
import socks
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
from urllib.parse import urlparse

configfile_name = os.path.join(os.path.expanduser("~"), '.nightscout_indicator.yaml')

if not os.path.isfile(configfile_name):
    config = configparser.ConfigParser()
    config.add_section('main')
    config.set('main', 'night_scout_url_base', 'https://servername.dom/')
    config.set('main', 'show_trend', 'True' )
    config.set('main', 'show_bgdelta', 'True' )
    config.set('main', 'show_age', 'True' )
    config.add_section('proxy')
    config.set('proxy', 'http', '' )
    config.set('proxy', 'https', '' )

    with open(configfile_name, 'w') as f:
        config.write(f)
    print('Please update ' + configfile_name)
    quit()


class Indicator():
    def __init__( self ):
        self.app = 'Nightscout Indicator'
        iconpath = "nightscout_indicator_icon"
        self.config = configparser.RawConfigParser()
        self.config.read(configfile_name)
        #self.indicator = AppIndicator3.Indicator.new( self.app, iconpath, AppIndicator3.IndicatorCategory.OTHER)
        self.indicator = AppIndicator3.Indicator.new_with_path( self.app, iconpath, AppIndicator3.IndicatorCategory.OTHER,  os.path.dirname(os.path.realpath(__file__) ) )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu( self.create_menu())
        self.indicator.set_label("No Data", self.app)
        # the thread:
        self.update = Thread(target=self.fetch_ns)
        # daemonize the thread to make the indicator stopable
        self.update.setDaemon(True)
        self.update.start()

    def create_menu( self ):
        menu = Gtk.Menu()
        # menu item 1
        # separator
        # quit
        item_quit = Gtk.MenuItem('Quit')
        item_quit.connect('activate', self.stop)
        menu.append(item_quit)

        menu.show_all()
        return menu

    def calc_age_minutes( self, server_now, sgv_time ):
        return str( math.floor((int( server_now ) - int( sgv_time ))/60000) )

    def build_display( self, json_resp ):
        bg_info = json_resp['bgs'][0]

        sgv = bg_info['sgv']
        if float( sgv ) == 0.7:
            result = 'No Signal'
        elif float( sgv ) == 0.3:
            result = 'Calibration Needed'
        else:
            result = sgv
            if self.config.get('main', 'show_trend' ) in [ 'True', 'true', 'yes', 'Yes' ]:
                arrows = { 0:'', 1:'⇈', 2: '↑', 3:'↗', 4:'→', 5:'↘', 6: '↓', 7: '⇊' }
                result += ' ' + arrows[bg_info['trend']] 

            if self.config.get('main', 'show_bgdelta' ) in [ 'True', 'true', 'yes', 'Yes' ]:
                result += ' (' + bg_info['bgdelta'] + ')'

            if self.config.get('main', 'show_age' ) in [ 'True', 'true', 'yes', 'Yes' ]:
                result += ' [' + self.calc_age_minutes( json_resp['status'][0]['now'], bg_info['datetime'] ) + ']'

        return result

    def fetch_ns_status( self ):
        glucose = "No Data"
        #try:
        url = urljoin( self.config.get('main', 'night_scout_url_base'), '/pebble')
        scheme = urlparse( url ).scheme 

        if self.config.get( 'proxy', scheme ) != '':
            r = requests.get( url, proxies={ scheme : self.config.get('proxy', scheme) } )
        else:
            r = requests.get( url )

        if 200 != r.status_code:
            return 'No Data'
        #except:
        #    pass

        result = 'No Data'
        try:
            result = self.build_display( r.json( ) )
        except:
            pass
        return result

    def fetch_ns( self ):
        t = 2
        while True:
            mention = self.fetch_ns_status()
            # apply the interface update using  GObject.idle_add()
            GObject.idle_add( self.indicator.set_label, mention, self.app, priority=GObject.PRIORITY_DEFAULT)
            time.sleep(60)
            t += 1

    def stop( self, source):
        Gtk.main_quit()

    def run( self ):
        Gtk.main()

    def signal_exit( self, signum, frame):
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

