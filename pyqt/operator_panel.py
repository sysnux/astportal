#! /usr/bin/env python
# -*- coding: utf-8 -*-
#

import sys
try:
   import simplejson as json
except:
   import json
from time import time, sleep
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from operator_widget import Ui_AsteriskOperatorPanel
import codecs, ConfigParser

class Operator(QWidget):

   def __init__(self, parent=None):
      super(Operator, self).__init__(parent,
         Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowSystemMenuHint)
#      Qt.X11BypassWindowManagerHint | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowSystemMenuHint)

      quitAction = QAction("&Quitter", self, shortcut="Ctrl+Q",
         triggered=qApp.quit)
      self.addAction(quitAction)
      self.setContextMenuPolicy(Qt.ActionsContextMenu)

      # Default values
      url = None
      self.operator = None
      self.color_normal = 'green'
      self.color_warning = 'yellow'
      self.color_alert = 'red'
      self.size = 10
      self.print_debug = False
      self.blf = []

      # Read and parse config file
      conf = ConfigParser.ConfigParser()
      conf.readfp(codecs.open("operator.cfg", "r", "utf8"))
      try:
         self.blf = conf.items('BLFs')
         url = conf.get('general', 'url')
         self.operator = conf.get('general', 'operator')
         self.size = conf.getint('general', 'size')
         self.print_debug = conf.getboolean('general', 'debug')
         self.color_normal = conf.get('colors', 'normal')
         self.color_alert = conf.get('colors', 'alert')
         self.color_warning = conf.get('colors', 'warning')

      except ConfigParser.NoOptionError:
         pass

      except ConfigParser.NoSectionError:
         pass

      if self.operator is None:
         sys.stderr.write(
            "ERREUR: opérateur non défini, verifier fichier de configuration, sortie.\n")
         sys.exit(1)

      if url is None:
         sys.stderr.write(
            "ERREUR: pas d'URL, verifier fichier de configuration, sortie.\n")
         sys.exit(1)

      self.debug(u'''Parameters : 
         URL = %s,
         operator = %s,
         color_normal = %s,
         color_warning = %s,
         color_alert = %s,
         size = %d,
         print_debug = %s.
         self.blf = %s\n''' % (
            url, self.operator,
            self.color_normal, self.color_warning, self.color_alert, 
            self.size, self.print_debug, self.blf))

      # Init panel
      self.ui = Ui_AsteriskOperatorPanel()
      self.ui.setupUi(self, self.blf)
 
      # Connect button events to functions
      for i, (k, blf) in enumerate(self.ui.blf_button.iteritems()):
         self.debug(u'BLF button #%d : %s (ext %s)' % (i, k, blf.exten))
         blf.clicked.connect(self.originate)
         self.connect(blf, SIGNAL("dropped"), self.transfer)
         self.connect(blf, SIGNAL("menu_transfer"), self.menu_transfer)

      # Position panel on screen, make it semi-transparent
      screen = QDesktopWidget().screenGeometry()
      my_size = self.geometry()
      self.move((screen.width()-my_size.width()), (screen.height()-my_size.height())/2)
      self.setWindowOpacity(.7)

      # Variables
      self.requests = 0 # Number of requests
      self.last = 0.0 # Last update (integer representing 1/100 seconds)
      self.channels = {} # Channels dict
      self.time_diff = 0 # Time difference beetwen host and server
      self.url_channels = QUrl(url + 'monitor/update_channels')
      self.url_users = QUrl(url + 'users/list')
      self.url_redirect = QUrl(url + 'monitor/redirect')
      self.url_originate = QUrl(url + 'monitor/originate')
      self.man = QNetworkAccessManager()

      # Init request users timer
      self.req_users()
      self.users_timer = QTimer()
#      QObject.connect( self.users_timer, SIGNAL('timeout()'), self.req_users)
#      self.users_timer.setInterval(10000)

      # Init request channels timer
      self.channels_timer = QTimer()
      self.channels_timer.singleShot(314, self.req_channels)

   def debug(self, x):
      if self.print_debug:
         print x

   def menu_transfer(self, s):
      self.debug(u'Menu transfer on %s' % s)
      users_list = []
      for u in self.users:
         user = u'%s %s' % (u[0], u[1])
         for p in u[2]:
            if p != s.exten:
               users_list.append( user + ' (' + p + ')' )
      self.debug(u'Menu transfer user_list=%s' % users_list)

      text, ok = QInputDialog.getItem(self,
         u'Transfert', 
         u'Transférer vers :',
         sorted(users_list),
         0,
         True)

      if ok:
         print u'Transfert libre vers %s' % text
      else:
         print u'Transfert libre annulé !'

   def transfer(self, s, d):
      self.debug(u'Transfer %s -> %s' % (s.channel, d))
      channel = None
      for c in self.channels:
         if c[:12].lower() == s.device: # XXX ConfigParser lower cases keys... ?!?!
             channel = c
             break
      else:
         self.debug(u'Transfer cancelled because channel %s not found' % channel)
         return
      exten = d.exten
      self.debug(u'Redirect %s -> %s' % (channel, exten))
      req = QNetworkRequest(self.url_redirect)
      req.setRawHeader('User-Agent', 'SysNux Operator Panel 0.1')
      req.setRawHeader('Content-Type',
         'application/x-www-form-urlencoded; charset=utf-8');
      self.rsp = self.man.post(req,
         QByteArray('channel=%s&exten=%s' % (channel, exten)))
      self.rsp.finished.connect(self.originate_finished)


   def originate(self):
      self.debug(u'Originate sender=%s' % self.sender())
      exten = self.sender().exten
      self.debug(u'Originate %s' % exten)
      req = QNetworkRequest(self.url_originate)
      req.setRawHeader('User-Agent', 'SysNux Operator Panel 0.1')
      req.setRawHeader('Content-Type', 
         'application/x-www-form-urlencoded; charset=utf-8');
      self.rsp = self.man.post(req,
         QByteArray('channel=%s&exten=%s' % (self.operator, exten)))
      self.rsp.finished.connect(self.originate_finished)

   def originate_finished(self):
      s = str(self.rsp.readAll())
      self.debug('Originate returns %d finished' % (self.requests))

   def mousePressEvent(self, event):
      if event.button() == Qt.LeftButton:
         self.dragPosition = event.globalPos() - self.frameGeometry().topLeft()
         event.accept()

   def mouseMoveEvent(self, event):
      if event.buttons() == Qt.LeftButton:
         self.move(event.globalPos() - self.dragPosition)
         event.accept()

   def req_users(self):
      self.debug('New users request %s' % self.url_users)
      req = QNetworkRequest(self.url_users)
      req.setRawHeader('User-Agent', 'SysNux Operator Panel 0.1')
      req.setRawHeader('Content-Type', 
         'application/x-www-form-urlencoded; charset=utf-8');
      self.rsp_users = self.man.get(req)
      self.rsp_users.finished.connect(self.rsp_users_finished)

   def rsp_users_finished(self):
      err = self.rsp_users.error()
      self.debug('Response users received, error=%d' % err)
      if err == 0:
         s = str(self.rsp_users.readAll())
         if s:
            try:
               js = json.loads(s)
            except:
               self.debug('Data received is not JSON: <%s>?' % s)
            self.users = js['users']
            self.debug('users list=%s' % (self.users))

         else:
            self.debug('No data!')

      self.rsp_users.deleteLater()
      self.users_timer.singleShot(600000, self.req_users)

   def req_channels(self):
      self.requests += 1
      self.debug('New request %d, last=%f' % (self.requests, self.last))
      req = QNetworkRequest(self.url_channels)
      req.setRawHeader('User-Agent', 'SysNux Operator Panel 0.1')
      req.setRawHeader('Content-Type', 
         'application/x-www-form-urlencoded; charset=utf-8');
      self.rsp_channels = self.man.post(req,
         QByteArray('last=%f' % self.last))
      self.rsp_channels.finished.connect(self.rsp_channels_finished)

   def rsp_channels_finished(self):
      err = self.rsp_channels.error()
      self.debug('Response %d received, error=%d' % (self.requests, err))
      if err == 0:
         s = str(self.rsp_channels.readAll())
         if s:
            try:
               js = json.loads(s)
            except:
               self.debug('Data received is not JSON: <%s>?' % s)
            self.last = js['last_update']
            self.time_diff = float(self.last)/100 - time()
            self.channels = js['channels']
            self.debug('Last=%f, channels=%s' % (self.last, self.channels))
            self.update_screen()

         else:
            self.debug('No data!')

      self.rsp_channels.deleteLater()
      self.channels_timer.singleShot(314, self.req_channels)

   def times(self, wait):
      ''' Convert epoch times list to string '1: 1m23s, 2: 0m12s'
      '''
      now = time() + self.time_diff
      x = []
      for i, w in enumerate(wait):
         m, s = divmod(now - int(w), 60)
         x.append('%d: %dm%02ds' % (1+i, m, s))
      return ', '.join(x)

   def update_screen(self):
      self.debug('Screen update !')

      # Check operator states
      chan = [c for c in self.channels]
      for l in self.ui.line_button:
         for c in chan:
            if c[:12] == self.operator:
                state = self.channels[c]['State']
                l.channel = c
                chan.remove(c) # Remove from temporary list of channels
                l.setToolTip(l.channel)
                self.debug(u'BLF %s is %s' % (c[:12], state))
                break
         else:
             state = 'Down'
             l.channel = None
             l.setToolTip('')

         if state=='Down':
             l.setStyleSheet("background-color: rgb(0, 192, 0);")
         elif state=='Up':
             l.setStyleSheet("background-color: rgb(192, 0, 0);")
         elif state=='Ring':
             l.setStyleSheet("background-color: rgb(192, 192, 0);")
         elif state=='Ringing':
             l.setStyleSheet("background-color: rgb(0, 192, 192);")
         else:
             self.debug(u'Active channel %s, unknown state %s' % (c, self.channels[c]))

      # Check BLF states
      for k, b in self.ui.blf_button.iteritems():
         for c in chan:
            if c[:12].lower() == k: # XXX ConfigParser lower cases keys... ?!?!
                b.channel = c
                state = self.channels[c]['State']
                chan.remove(c) # Remove from temporary list of channels
                b.setToolTip(b.channel)
                self.debug(u'BLF %s is %s' % (c[:12], state))
                break
         else:
             state = 'Down'
             b.channel = None
             b.setToolTip('')

         if state=='Down':
             b.setStyleSheet("background-color: rgb(0, 192, 0);")
         elif state=='Up':
             b.setStyleSheet("background-color: rgb(192, 0, 0);")
         elif state=='Ring':
             b.setStyleSheet("background-color: rgb(192, 192, 0);")
         elif state=='Ringing':
             b.setStyleSheet("background-color: rgb(0, 192, 192);")
         else:
             self.info(u'Active channel %s, unknown state %s' % (c, self.channels[c]))


if __name__ == '__main__':
   app = QApplication(sys.argv)
   mon = Operator()

   mon.show()
#   mon.update_timer.start(1000)
   sys.exit(app.exec_())

