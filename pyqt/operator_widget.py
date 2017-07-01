# -*- coding: utf-8 -*-
#
# Asterisk Operator Panel: GUI app that displays extensions, allow to pickup 
# when ringing, or transfer.
# 
# Author: Jean-Denis Girard <jd.girard@sysnux.pf>
#
# Form implementation generated from reading ui file 'operator_widget.ui'
#
# Created: Sun Dec  1 08:34:38 2013
#      by: PyQt4 UI code generator 4.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
from rich_text_button import RichTextPushButton

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class DragDropButton(RichTextPushButton):

    def __init__(self, parent, variant, device, exten, name, img, x, y, w, h):

        super(DragDropButton, self).__init__(parent)
        self.setFocusPolicy(QtCore.Qt.NoFocus) # No focus!
        self.device = device
        self.channel = None
        self.exten = exten
        self.name = name
        self.bstate = None
        self.variant = variant
        self.setAcceptDrops(True)
        html = u'''\
<table>
<tr><td><img src="%s"/></td>
<td><font size="+1">%s</font><br/><b>%s</b></td></tr>
</table>
''' % (img, exten, name)
        self.setHtml(html)
        self.setStyleSheet("background-color: rgb(120, 120, 120); font-weight: bold;")
        self.setGeometry(QtCore.QRect(x, y, w, h))
        QtCore.QObject.connect(
            self, QtCore.SIGNAL('clicked()'), self.blf_clicked)
        self.act_transfer = QtGui.QAction(u"&Transférer vers...", self,
                triggered=self.transfer)
        self.addAction(self.act_transfer)
        self.act_transfer.setEnabled(False)
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )

    def __repr__(self):
       return u'<DragDropButton: %s, %s, %s, %s>' %  (
           self.device, self.exten, self.name, self.bstate)

    def transfer(self):
        if self.channel is not None:
           self.emit(QtCore.SIGNAL("menu_transfer"), self)
        else:
           AsteriskOperatorPanel.debug('Transfer without channel %s' % self)

    def mouseMoveEvent(self, e):
        mimeData = QtCore.QMimeData()
        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.setHotSpot(e.pos() - self.rect().topLeft())
        dropAction = drag.start(QtCore.Qt.MoveAction)

    def dragEnterEvent(self, e):
        if type(e.source()) == type(self):
            e.accept()
        else:
            print 'DragEnter rejected (source type=%s)' % type(e.source())

    def dropEvent(self, e):       
        source = e.source()
        self.emit(QtCore.SIGNAL('dropped'), source, self)

    def blf_clicked(self):
        pass


    def set_button_state(self, state):

         self.bstate = state

         if self.bstate in ('NOT_INUSE', 'Down'):
             self.setStyleSheet("background-color: rgb(0, 192, 0);")
             self.act_transfer.setEnabled(False)
         elif self.bstate in ('BUSY', 'Up'):
             self.setStyleSheet("background-color: rgb(192, 0, 0);")
             self.act_transfer.setEnabled(True)
         elif self.bstate in ('RING', 'Ring'):
             self.setStyleSheet("background-color: rgb(192, 192, 0);")
         elif self.bstate in ('RINGING', 'Ringing'):
             self.setStyleSheet("background-color: rgb(0, 192, 192);")
         elif self.bstate in ('RINGINUSE', ):
             self.setStyleSheet("background-color: rgb(0, 10, 10);")
         else:
             self.setStyleSheet("background-color: rgb(100, 100, 100);")
             if self.bstate not in ('UNAVAILABLE', ):
                 print u'Button %s, unknown state %s' % (self, state)

class Ui_AsteriskOperatorPanel(object):

    def setupUI(self, AsteriskOperatorPanel, operator, blf):

        num = len(blf)
        h = (40+5) * num
        l = 160
        from math import ceil
        cols = int(ceil(h/l/3.0))
        rows = int(ceil(float(num)/cols))
        AsteriskOperatorPanel.debug(
            '%d buttons total height %d px (width %d px) %s cols %s rows' % \
            (num, h, l, cols, rows))

        AsteriskOperatorPanel.setObjectName(_fromUtf8("AsteriskOperatorPanel"))
        AsteriskOperatorPanel.resize(120+(160+15)*cols, rows*45+15)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, \
            QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(AsteriskOperatorPanel.sizePolicy().hasHeightForWidth())
        AsteriskOperatorPanel.setSizePolicy(sizePolicy)

        # BLF buttons
        self.blf_button = {}
        col = row = 0
        for i, b in enumerate(blf):
           if ',' in b[1]:
              ext, name = b[1].split(',')
              ext = ext.strip()
              name = name.strip()
           else:
              ext = name = b[1].strip()
#           print 'button %s (col %s, row %s)' % (i, col, row)
           self.blf_button[b[0]] = DragDropButton(
               AsteriskOperatorPanel, # Parent
               'phone',
               b[0], # Object name
               ext, # First line (extension)
               name, # Second line (name)
               'phone_inactive.png',
               130 + (160+15)*col, 10 + (40+5)*row, 160, 40 # x,y, w, h
            )
           row += 1
           if row >= rows:
              col += 1 
              row = 0

        # Operator button
        self.op_button = DragDropButton( 
               AsteriskOperatorPanel, # Parent
               'operator',
               operator, # Object name
               '',
               'Standard', # Button text
               'headphone.png',
               10, 10, 110, 40 # x,y, w, h
            )

        # Parking buttons
        self.park_button = []
        for i in range(4):
            self.park_button.append(DragDropButton( 
               AsteriskOperatorPanel, # Parent
               'parking',
               'park%d' % i, # Object name
               '900%d' % (i + 1), # Exten
               'Attente %d' % i, # Button text
               'parking.png',
               10, 100 + (40+5)*i, 110, 40 # x,y, w, h
            ))

        self.retranslateUi(AsteriskOperatorPanel)
        QtCore.QMetaObject.connectSlotsByName(AsteriskOperatorPanel)

    def retranslateUi(self, AsteriskOperatorPanel):
        AsteriskOperatorPanel.setWindowTitle(
            _translate("AsteriskOperatorPanel", u"Panneau Opérateur Asterisk", None))

