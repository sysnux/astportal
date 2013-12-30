#!/usr/bin/env python
# coding=UTF-8
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

      # Read config file
      conf = ConfigParser.ConfigParser()
#      conf.read('operator.cfg')
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
#      self.debug(u'BLF buttons = %s' % self.ui.blf_button)

#      # Le mapping des différents signaux  
#      self.signalMap=QSignalMapper(self)  
#      self.connect(  
#            self.signalMap,  
#            SIGNAL("mapped(int)"),  
#            self.slotMapped  
#        )
#
#      for i, b in enumerate(self.ui.blf_button):
#         # Le bouton est ajouté au mapping  
#         self.signalMap.setMapping(self.ui.blf_button[b], i)  
#                          
#         # Enregistrement du signal dans le mapping  
#         self.connect(
#                self.ui.blf_button[b],
#                SIGNAL("clicked()"),
#                self.signalMap,
#                SLOT("map()")
#            )
#         #self.ui.blf_button[b].clicked.connect(self.originate)

      # Center panel at top of screen, make it semi-transparent
      screen = QDesktopWidget().screenGeometry()
      my_size = self.geometry()
      self.move((screen.width()-my_size.width()), (screen.height()-my_size.height())/2)
      self.setWindowOpacity(.7)

      # Init screen update timer
      self.update_timer = QTimer()
      QObject.connect(self.update_timer, SIGNAL("timeout()"), self.update_screen)

      # Variables
      self.requests = 0 # Number of requests
      self.last = 0.0 # Last update (integer representing 1/100 seconds)
      self.channels = {} # Queues dict
      self.time_diff = 0 # Time difference beetwen host and server
      self.url = QUrl(url)
      self.man = QNetworkAccessManager()

      # Init request timer
      self.request_timer = QTimer()
      self.request_timer.singleShot(100, self.make_request)

   def debug(self, x):
      if self.print_debug:
         print x

   def slotMapped(self, i):
      print u'Button %d pressed !' % i

   def originate(self):
      exten = ((self.sender().text()).split('\n'))[0]
      self.debug(u'Originate %s' % exten)
      req = QNetworkRequest(QUrl('http://localhost:8080/monitor/originate'))
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

   def make_request(self):
      self.requests += 1
      self.debug('New request %d, last=%f' % (self.requests, self.last))
      req = QNetworkRequest(self.url)
      req.setRawHeader('User-Agent', 'SysNux Operator Panel 0.1')
      req.setRawHeader('Content-Type', 
         'application/x-www-form-urlencoded; charset=utf-8');
      self.rsp = self.man.post(req,
         QByteArray('last=%f' % self.last))
      self.rsp.finished.connect(self.response_finished)

   def response_finished(self):
      s = str(self.rsp.readAll())
      self.debug('Response %d received' % (self.requests))
      if s:
         js = json.loads(s)
         self.last = js['last_update']
         self.time_diff = float(self.last)/100 - time()
         self.channels = js['channels']
         self.debug('Last=%f, channels=%s' % (self.last, self.channels))
         self.update_screen()

      else:
         self.debug('No data!')

      self.rsp.deleteLater()
      self.request_timer.singleShot(314, self.make_request)

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
      for c in self.channels:
         if c[:12] == self.operator:
             state = self.channels[c]['State']
             self.debug(u'BLF %s is %s' % (c[:12], state))
             break
      else:
          state = 'Down'
#      if state=='Down':
#          self.ui.line_button[0].setStyleSheet("background-color: rgb(0, 192, 0);")
#      elif state=='Up':
#          self.ui.line_button[0].setStyleSheet("background-color: rgb(192, 0, 0);")
#      elif state=='Ring':
#          self.ui.line_button[0].setStyleSheet("background-color: rgb(192, 192, 0);")
#      elif state=='Ringing':
#          self.ui.line_button[0].setStyleSheet("background-color: rgb(0, 192, 192);")
#      else:
#          self.debug(u'Active channel %s, unknown state %s' % (c, self.channels[c]))

      # Check BLF states
      for b in self.blf:
         for c in self.channels:
            if c[:12].lower() == b[0]: # XXX ConfigParser lower cases keys... ?!?!
                state = self.channels[c]['State']
                self.debug(u'BLF %s is %s' % (c[:12], state))
                break
         else:
             state = 'Down'
         if state=='Down':
             self.ui.blf_button[b[0]].setStyleSheet("background-color: rgb(0, 192, 0);")
         elif state=='Up':
             self.ui.blf_button[b[0]].setStyleSheet("background-color: rgb(192, 0, 0);")
         elif state=='Ring':
             self.ui.blf_button[b[0]].setStyleSheet("background-color: rgb(192, 192, 0);")
         elif state=='Ringing':
             self.ui.blf_button[b[0]].setStyleSheet("background-color: rgb(0, 192, 192);")
         else:
             self.debug(u'Active channel %s, unknown state %s' % (c, self.channels[c]))


if __name__ == '__main__':
   app = QApplication(sys.argv)
   mon = Operator()

   mon.show()
#   mon.update_timer.start(1000)
   sys.exit(app.exec_())

