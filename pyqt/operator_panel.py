#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Asterisk Operator Panel: GUI app that displays extensions, allow to pickup 
# when ringing, or transfer, or park...
# 
# Author: Jean-Denis Girard <jd.girard@sysnux.pf>

from sys import argv, exit, stderr
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

   def __init__(self, argv=None, parent=None):
      super(Operator, self).__init__(parent,
         Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowSystemMenuHint)
#      Qt.X11BypassWindowManagerHint | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowSystemMenuHint)

      self.addAction( QAction(u'\xC0 propos', self, triggered=self.about))
      self.addAction( QAction(u'&Quitter', self, shortcut="Ctrl+Q",
         triggered=qApp.quit))
      self.setContextMenuPolicy(Qt.ActionsContextMenu)

      # Default values
      url = None
      self.op_channel = None
      self.op_exten = None
      username = None
      secret = None
      self.color_normal = 'green'
      self.color_warning = 'yellow'
      self.color_alert = 'red'
      self.size = 10
      self.print_debug = False
      self.blf = []
      self.certificate = None
      self.ignore_ssl_errors = False

      # Read and parse config file
      conf = ConfigParser.ConfigParser()
      conf.optionxform = str # Preserve case
      try:
         conf.readfp(codecs.open(argv[1], 'r', 'utf8'))
      except:
         stderr.write('Usage: %s fichier_configuration\n' % argv[0])
         exit(1)

      try:
         self.blf = conf.items('BLFs')
         url = conf.get('general', 'url')
         username = conf.get('general', 'username')
         secret = conf.get('general', 'secret')
         op_c, op_e = conf.get('general', 'operator').split(',')
         self.op_channel, self.op_exten = op_c.strip(), op_e.strip()
         self.print_debug = conf.getboolean('general', 'debug')
         self.ignore_ssl_errors = conf.getboolean('general', 'ignore_ssl_errors')
         self.certificate = conf.get('general', 'ssl_certificates_file')

      except ConfigParser.NoOptionError, ConfigParser.NoSectionError:
         pass

      except ConfigParser.NoSectionError:
         pass

      if None in (username, secret, self.op_channel, self.op_exten):
         stderr.write(
            "ERREUR: verifier fichier de configuration, sortie.\n")
         exit(1)

      if url is None:
         stderr.write(
            "ERREUR: pas d'URL, verifier fichier de configuration, sortie.\n")
         exit(1)

      self.debug(u'''Parameters : 
         URL = %s,
         operator = %s %s,
         color_normal = %s,
         color_warning = %s,
         color_alert = %s,
         size = %d,
         print_debug = %s.
         ssl_certificates_file = %s,
         ignore_ssl_errors = %s,
         self.blf = %s\n''' % (
            url, self.op_channel, self.op_exten,
            self.color_normal, self.color_warning, self.color_alert, 
            self.size, self.print_debug, self.certificate,
            self.ignore_ssl_errors, self.blf))

      # Init panel
      self.ui = Ui_AsteriskOperatorPanel()
      self.ui.setupUI(self, self.op_channel, self.blf)
 
      # Connect button events to functions
      for i, (k, blf) in enumerate(self.ui.blf_button.iteritems()):
         blf.clicked.connect(self.originate)
         self.connect(blf, SIGNAL("dropped"), self.transfer)
         self.connect(blf, SIGNAL("menu_transfer"), self.menu_transfer)

      # Connect parking button events to functions
      for i, park in enumerate(self.ui.park_button):
         park.clicked.connect(self.originate)
         self.connect(park, SIGNAL("dropped"), self.transfer)
         self.connect(park, SIGNAL("menu_transfer"), self.menu_transfer)
      self.connect(self.ui.op_button[0], SIGNAL("menu_transfer"), self.menu_transfer)

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
      self.url_login = url + 'login_handler'
      self.url_channels = url + 'monitor/update_channels'
      self.url_users = url + 'users/list'
      self.url_redirect = url + 'monitor/redirect'
      self.url_originate = url + 'monitor/originate'
      self.url_park = url + 'monitor/park'
      self.authtkt = ''

      # Read certificate(s) from file, add them to all SSL connections
      if self.certificate:
         try:
            certs = QSslCertificate.fromPath(self.certificate)
         except:
            stderr.write('Error reading certificates file %s' % self.certificate)
            exit(1)
         self.debug('Read %d certificate(s)' % len(certs))
         if len(certs) == 0:
            stderr.write('No certificates found in file "%s"!\n' % self.certificate)
            exit(1)
         for i, c in enumerate(certs):
            self.debug('Certificate %d is %svalid' % ( i+1,
               '' if c.isValid() else '*not* '))
            QSslSocket.addDefaultCaCertificate(c)

      self.man = QNetworkAccessManager()
      self.connect(self.man, 
         SIGNAL('sslErrors(QNetworkReply *, const QList<QSslError> &)'),
         self.SSLerrors)

      # Login
      self.login( username, secret)

      # Init request channels timer
      self.channels_timer = QTimer()
      self.users_timer = QTimer()

   def SSLerrors(self, reply, errors):
      if self.ignore_ssl_errors:
         self.debug('Warning, SSL errors ignored!')
         reply.ignoreSslErrors()
      else:
         stderr.write('SSL errors:\n')
         for e in errors:
            stderr.write(' . %d: %s\n' % (e.error(), e.errorString()))
         exit(1)

   def about(self):
      html = '''\
<html><body bgcolor="#ffffff">
<h2>Console Standardiste pour Asterisk<sup>&copy;</sup></h2>
<div style="float: left;">
   <img src="logo-320x240.jpg" width="64" height="48" border="0"/>
par SysNux <a href="http://www.sysnux.pf/">http://www.sysnux.pf/</a>
</div>
</body></html>
'''
      QMessageBox.about(self, u'A propos', html)

   def debug(self, x):
      if self.print_debug:
         print x

   def request(self, url, params, callback):
      req = QNetworkRequest(QUrl(url))
      req.setRawHeader('User-Agent', 'SysNux Operator Panel 0.1')
      req.setRawHeader('Cookie', self.authtkt)
      req.setRawHeader('Content-Type',
         'application/x-www-form-urlencoded; charset=utf-8');
      resp = self.man.post(req, QByteArray(params))
      resp.finished.connect(callback)

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

      if not ok:
         self.debug(u'Transfer cancelled !')
         return

      self.debug(u'Menu transfert to %s' % text)
      for c in self.channels:
            if c[:-9] == s.device:
               channel = self.channels[c]['From']
               break

      if channel is None:
         self.debug(u'Menu transfer cancelled because channel %s not found')
         return

      self.debug(u'Transfer %s -> %s' % (url, params))
      self.request(self.url_redirect, 
         'channel=%s&exten=%s' % (channel, text[-4:-1]),
         self.originate_finished)

   def transfer(self, s, d):
      self.debug(u'Transfer %s -> %s' % (s, d))

      channel = None
      if s.variant=='parking':
         for i, c in enumerate(self.channels):
            parked = self.channels[c].get('Park')
            if parked is not None and parked == '7%02d' % (i+1):
               channel = c
               break

      else:
         for c in self.channels:
            if c[:-9] == s.device:
               channel = self.channels[c]['From']
               break

      if channel is None:
         self.debug(u'Transfer cancelled because channel %s not found')
         return

      if d.variant=='parking':
         url = self.url_park
         params = 'channel=%s' % channel
      else:
         url = self.url_redirect
         params = 'channel=%s&exten=%s' % (channel, d.exten)

      self.debug(u'Transfer %s -> %s' % (url, params))
      self.request(url, params, self.originate_finished )


   def originate(self):
      self.debug(u'Originate sender=%s' % self.sender())
      exten = self.sender().exten
      state = self.sender().bstate
      if state=='Down':
         url = self.url_originate
         params = 'channel=%s&exten=%s' % (self.op_channel, exten)
      elif state=='Ringing':
         # If destination is ringing, redirect to the operator extension
         url = self.url_redirect
         for c in self.channels:
            if c[:-9] == self.sender().device:
               src = self.channels[c]['From']
               break
         else:
            self.debug(u'Transfer cancelled because channel %s not found' % channel)
            return
         params = 'channel=%s&exten=%s' % (src, self.op_exten)
      else:
         self.debug(u'Originate ERROR state=%s' % state)
         QMessageBox.warning(self, u'Erreur', u'Hello :)', QMessageBox.Ok)
         return
      self.request(url, params, self.originate_finished )

   def originate_finished(self):
      s = str(self.sender().readAll())
      self.debug('Originate returns %d finished' % (self.requests))

   def mousePressEvent(self, event):
      if event.button() == Qt.LeftButton:
         self.dragPosition = event.globalPos() - self.frameGeometry().topLeft()
         event.accept()

   def mouseMoveEvent(self, event):
      if event.buttons() == Qt.LeftButton:
         self.move(event.globalPos() - self.dragPosition)
         event.accept()

   def login(self, user, pwd):
      self.debug('Login!')
      self.request(self.url_login,
         'login=%s&password=%s' % (user, pwd),
         self.rsp_login_finished )

   def rsp_login_finished(self):
      rsp = self.sender()
      err = rsp.error() #self.rsp_login.error()
      self.debug('Response login received, error=%d' % err)
      for k, v in rsp.rawHeaderPairs():
         if k == 'Set-Cookie' and str(v).startswith('authtkt='):
            self.authtkt = v
            self.debug('Auth = "%s"' % (self.authtkt))
            break
      rsp.deleteLater()
      self.req_users()
      self.req_channels()

   def req_users(self):
      self.debug('New users request %s' % self.url_users)
      self.request(self.url_users, '', self.rsp_users_finished )

   def rsp_users_finished(self):
      rsp = self.sender()
      err = rsp.error()
      self.debug('Response users received, error=%d' % err)
      if err == 0:
         s = str(rsp.readAll())
         if s:
            try:
               js = json.loads(s)
            except:
               self.debug('Data received is not JSON: <%s>?' % s)
               return
            self.users = js['users']
            self.debug('users list=%s' % (self.users))

         else:
            self.debug('No data!')

      rsp.deleteLater()
      self.users_timer.singleShot(600000, self.req_users)

   def req_channels(self):
      self.requests += 1
      self.debug('New request %d, last=%f' % (self.requests, self.last))
      self.request(self.url_channels,
         'last=%f' % self.last,
         self.rsp_channels_finished )

   def rsp_channels_finished(self):
      rsp = self.sender()
      err = rsp.error()
      self.debug('Response %d received, error=%d' % (self.requests, err))
      if err == 0:
         s = str(rsp.readAll())
         if s:
            try:
               js = json.loads(s)
            except:
               self.debug('Data received is not JSON: <%s>?' % s)
               return
            self.last = js['last_update']
            self.time_diff = float(self.last)/100 - time()
            self.channels = js['channels']
            self.debug('Last=%f, channels=%s' % (self.last, self.channels))
            self.update_screen()

         else:
            self.debug('No data!')

      rsp.deleteLater()
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
      for l in self.ui.op_button:
         for c in chan:
            if c[:-9] == self.op_channel:
                l.set_button_state(self.channels[c]['State'])
                l.channel = c
                chan.remove(c) # Remove from temporary list of channels
                l.setToolTip(l.channel)
                self.debug(u'BLF %s is %s' % (c[:-9], l.bstate))
                break
         else:
             l.set_button_state('Down')
             l.channel = None
             l.setToolTip('')

      # Check parking states
      for i, p in enumerate(self.ui.park_button):
         for c in self.channels:
             parked = self.channels[c].get('Park')
             if parked is not None and parked == '7%02d' % (i+1):
                p.set_button_state('Up')
                break
         else:
             p.set_button_state('Down')
             p.channel = None
             p.setToolTip('')

      # Check BLF states
      for k, b in self.ui.blf_button.iteritems():
         for c in chan:
            if c[:-9] == k:
                b.channel = c
                b.set_button_state(self.channels[c]['State'])
                chan.remove(c) # Remove from temporary list of channels
                b.setToolTip(b.channel)
                self.debug(u'BLF %s is %s' % (c[:-9], b.bstate))
                break
         else:
             b.set_button_state('Down')
             b.channel = None
             b.setToolTip('')


if __name__ == '__main__':
   app = QApplication(argv)
   mon = Operator(argv=argv)

   mon.show()
#   mon.update_timer.start(1000)
   exit(app.exec_())

