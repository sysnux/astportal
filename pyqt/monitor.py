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
from monitor_widget import Ui_ast_queue_mon
import ConfigParser

class Monitor(QWidget):

   def __init__(self, parent=None):
      super(Monitor, self).__init__(parent,
         Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowSystemMenuHint)
#      Qt.X11BypassWindowManagerHint | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowSystemMenuHint)

      quitAction = QAction("&Quitter", self, shortcut="Ctrl+Q",
         triggered=qApp.quit)
      self.addAction(quitAction)
      self.setContextMenuPolicy(Qt.ActionsContextMenu)

      # Default values
      url = None
      self.members_warning = 2
      self.members_alert = 1
      self.queues_warning = 1
      self.queues_alert = 2
      self.color_normal = 'green'
      self.color_warning = 'yellow'
      self.color_alert = 'red'
      self.size = 10
      self.print_debug = False
      self.max_queues = 5 # Display only N queues

      # Read config file
      conf = ConfigParser.ConfigParser()
      conf.read('monitor.cfg')
      try:
         url = conf.get('general', 'url')
         self.size = conf.getint('general', 'size')
         self.max_queues = conf.getint('general', 'max_queues')
         self.print_debug = conf.getboolean('general', 'debug')
         self.members_warning = conf.getint('members', 'warning')
         self.members_alert = conf.getint('members', 'alert')
         self.queues_warning = conf.getint('queues', 'warning')
         self.queues_alert = conf.getint('queues', 'alert')
         self.color_normal = conf.get('colors', 'normal')
         self.color_alert = conf.get('colors', 'alert')
         self.color_warning = conf.get('colors', 'warning')
      except ConfigParser.NoOptionError:
         pass

      if url is None:
         sys.stderr.write(
            "ERREUR: pas d'URL, verifier fichier de configuration, sortie.\n")
         sys.exit(1)

      self.debug(u'''Parameters : 
      URL = %s,
      max_queues = %d,
      members_warning = %d,
      members_alert = %d,
      queues_warning = %d,
      queues_alert = %d,
      color_normal = %s,
      color_warning = %s,
      color_alert = %s,
      size = %d,
      print_debug = %s.''' % (
         url, self.max_queues, self.members_warning, self.members_alert,
         self.queues_warning, self.queues_alert, self.color_normal,
         self.color_warning, self.color_alert, self.size, self.print_debug))

      # Init panel
      self.ui = Ui_ast_queue_mon()
      self.ui.setupUi(self, self.max_queues, self.size)
      self.ui.lcd.setProperty('value', 0)
      self.ui.lcd.setStyleSheet("QWidget { background-color: transparent; }")
      for i in range(self.max_queues):
         self.ui.q[i]['name'].setText('-')
         self.ui.q[i]['members'].setText('0')
         self.ui.q[i]['wait'].setText('0')
         self.ui.q[i]['times'].setText('-')
         self.ui.q[i]['time'] = 0

      # Center panel at top of screen, make it semi-transparent
      screen = QDesktopWidget().screenGeometry()
      my_size = self.geometry()
      self.move((screen.width()-my_size.width())/2, 0)
      self.setWindowOpacity(.7)

      # Init screen update timer
      self.update_timer = QTimer()
      QObject.connect(self.update_timer, SIGNAL("timeout()"), self.update_screen)

      # Variables
      self.requests = 0 # Number of requests
      self.last = 0 # Last update (integer representing 1/100 seconds)
      self.queues = {} # Queues dict
      self.time_diff = 0 # Time difference beetwen host and server
      self.url = QUrl(url)
      self.man = QNetworkAccessManager()

      # Init request timer
      self.request_timer = QTimer()
      self.request_timer.singleShot(100, self.make_request)

   def debug(self, x):
      if self.print_debug:
         print x

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
      self.debug('New request %d, last=%s' % (self.requests, self.last))
      req = QNetworkRequest(self.url)
      req.setRawHeader('User-Agent', 'SysNux Queue Monitor 0.1')
      req.setRawHeader('Content-Type', 
         'application/x-www-form-urlencoded; charset=utf-8');
      self.rsp = self.man.post(req,
         QByteArray('last=%d' % self.last))
      self.rsp.finished.connect(self.response_finished)

   def response_finished(self):
      s = str(self.rsp.readAll())
      self.debug('Response %d finished' % (self.requests))
      self.debug(s)
      if s:
         js = json.loads(s)
         self.last = js['last']
         self.time_diff = float(self.last)/100 - time()
         self.queues = js['queues']
         self.debug('Last=%s, queues=%s' % (self.last, self.queues))
         self.update_screen()

      else:
         self.debug('No data!')

      self.rsp.deleteLater()
      self.request_timer.singleShot(314, self.make_request)

   def times(self, wait):
      ''' Convert epoch times list to string '1: 1m23s, 2: 0m12s'
      '''
      now = time() #+ self.time_diff
      x = []
      for i, w in enumerate(wait):
         m, s = divmod(now - w, 60)
         x.append('%d: %dm%02ds' % (1+i, m, s))
      return ', '.join(x)

   def update_screen(self):
      self.debug('Screen update !')
      tot = 0
      for i, q in enumerate(self.queues):
         if i>=self.max_queues: break
         self.debug('Queue %d, name = %s, weight = %s, members = %s, wait = %s' % (
            i, q['name'], q['params']['Weight'], q['params']['Members'], q['params']['Wait']))
         self.ui.q[i]['name'].setText(q['name'])
         self.ui.q[i]['members'].setText('%d' % len(q['params']['Members']))

         if len(q['params']['Members'])<self.members_alert:
            self.ui.q[i]['members'].setStyleSheet(
               'QWidget { color: %s; }' % self.color_alert)
         elif len(q['params']['Members'])<self.members_warning:
            self.ui.q[i]['members'].setStyleSheet(
               'QWidget { color: %s; }' % self.color_warning)
         else:
            self.ui.q[i]['members'].setStyleSheet(
               'QWidget { color: %s; }' % self.color_normal)

         if q['params']['Wait']:
            tot += len(q['params']['Wait'])
            self.ui.q[i]['wait'].setText('%d' % len(q['params']['Wait']))
            self.ui.q[i]['times'].setText(self.times(q['params']['Wait']))
         else:
            self.ui.q[i]['wait'].setText('0')
            self.ui.q[i]['times'].setText('-')

      if tot>self.queues_alert:
         mon.ui.lcd.setStyleSheet(
               'QWidget { color: %s; }' % self.color_alert)
      elif tot>self.queues_warning:
         mon.ui.lcd.setStyleSheet(
               'QWidget { color: %s; }' % self.color_warning)
      else:
         mon.ui.lcd.setStyleSheet(
               'QWidget { color: %s; }' % self.color_normal)
 
      mon.ui.lcd.setProperty('value', tot)


if __name__ == '__main__':

   # No printing on pythonw!
   if sys.executable.endswith("pythonw.exe"):
      sys.stdout = sys.stderr = None

   app = QApplication(sys.argv)
   mon = Monitor()

   mon.show()
   mon.update_timer.start(1000)
   sys.exit(app.exec_())

