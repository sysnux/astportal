# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'monitor_widget.ui'
#
# Created: Fri Feb  3 15:55:18 2012
#      by: PyQt4 UI code generator 4.7.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_ast_queue_mon(object):

   def setupUi(self, ast_queue_mon, max_queues):
      ast_queue_mon.setObjectName("ast_queue_mon")
      ast_queue_mon.resize(467, 114)

      self.q = []
      for i in range(max_queues):
         self.q.append({'name': QtGui.QLabel(ast_queue_mon),
            'members': QtGui.QLabel(ast_queue_mon),
            'times': QtGui.QLabel(ast_queue_mon),
            'wait': QtGui.QLabel(ast_queue_mon) })
         self.q[i]['members'].setGeometry(QtCore.QRect(100, 8+20*i, 101, 21))
         self.q[i]['members'].setObjectName('q%d_members' % i)
         self.q[i]['name'].setGeometry(QtCore.QRect(117, 8+20*i, 101, 21))
         self.q[i]['name'].setObjectName('q%d_name' % i)
         self.q[i]['times'].setGeometry(QtCore.QRect(260, 8+20*i, 201, 21))
         self.q[i]['times'].setObjectName('q%d_times' % i)
         self.q[i]['wait'].setGeometry(QtCore.QRect(210, 8+20*i, 41, 21))
         self.q[i]['wait'].setObjectName('q%d_wait' % i)

      self.lcd = QtGui.QLCDNumber(ast_queue_mon)
      self.lcd.setGeometry(QtCore.QRect(0, 10, 91, 101))
      font = QtGui.QFont()
      font.setPointSize(14)
      self.lcd.setFont(font)
      self.lcd.setNumDigits(2)
      self.lcd.setProperty("intValue", 22)
      self.lcd.setObjectName("lcd")

      self.retranslateUi(ast_queue_mon)
      QtCore.QMetaObject.connectSlotsByName(ast_queue_mon)

   def retranslateUi(self, ast_queue_mon):
      ast_queue_mon.setWindowTitle(QtGui.QApplication.translate("ast_queue_mon", "Asterisk Queues Monitor", None, QtGui.QApplication.UnicodeUTF8))
      ast_queue_mon.setToolTip(QtGui.QApplication.translate("ast_queue_mon", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Déplacez le panneau</span> en cliquant sur le bonton <span style=\" font-style:italic;\">droit</span> de la souris,</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">puis en déplacant la souris <span style=\" font-style:italic;\">sans relacher le bouton</span>.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Accédez au menu</span> en en cliquant sur le bonton <span style=\" font-style:italic;\">gauche</span> de la souris.</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
