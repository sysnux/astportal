# -*- coding: utf-8 -*-

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

    def __init__(self, parent, channel, ext, name, x, y, w, h):
        super(DragDropButton, self).__init__(parent)
        self.channel = channel
        self.ext = ext
        self.name = name
        self.state = 'Down'
        self.setAcceptDrops(True)
#        self.setObjectName(_fromUtf8(object_name))
#        self.setText(ext + '\n' + name)
        self.setHtml(u'''
<table>
<tr><td>
<img src="/usr/share/icons/oxygen/32x32/actions/draw-brush.png" width="20" height="32"/>
</td>
<td><font size="+1">%s</font><br/><b>%s</b></td></tr>
</table>
''' % (ext, name))
        self.setStyleSheet("background-color: rgb(0, 192, 0); font-weight: bold;")
        self.setGeometry(QtCore.QRect(x, y, w, h))
        QtCore.QObject.connect(
            self, QtCore.SIGNAL('clicked()'), self.blf_clicked)

    def __repr__(self):
       return u'<DragDropButton: %s, %s, %s, %s>' %  (
           self.channel, self.ext, self.name, self.state)

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
        print 'Drop: %s -> %s' % (source, self)

    def blf_clicked(self):
        print 'Clicked: %s' % (self)

class Ui_AsteriskOperatorPanel(object):

    def setupUi(self, AsteriskOperatorPanel, blf):

        AsteriskOperatorPanel.setObjectName(_fromUtf8("AsteriskOperatorPanel"))
#        AsteriskOperatorPanel.resize(280, len(blf)*45+15)
        AsteriskOperatorPanel.resize(200, len(blf)*45+15)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(AsteriskOperatorPanel.sizePolicy().hasHeightForWidth())
        AsteriskOperatorPanel.setSizePolicy(sizePolicy)

        # BLF buttons
        self.blf_button = {}
        for i, b in enumerate(blf):
           if ',' in b[1]:
              ext, name = b[1].split(',')
           else:
              ext = name = b[1]
           self.blf_button[b[0]] = DragDropButton(
               AsteriskOperatorPanel, # Parent
               b[0], # Object name
               ext, # First line (extension)
               name, # Second line (name)
               20, 10 + (40+5)*i, 160, 40 # x,y, w, h
#               110, 10 + (40+5)*i, 160, 40 # x,y, w, h
            )

        # Line buttons
#        self.line_button = []
#        for i in range(4):
#            self.line_button.append(DragButton( 
#               AsteriskOperatorPanel, # Parent
#               'line_%d' % i, # Object name
#               'Ligne %d' % i, # Button text
#               10, 10 + (25+5)*i, 80, 25 # x,y, w, h
#            ))

        self.retranslateUi(AsteriskOperatorPanel)
        QtCore.QMetaObject.connectSlotsByName(AsteriskOperatorPanel)

    def retranslateUi(self, AsteriskOperatorPanel):
        AsteriskOperatorPanel.setWindowTitle(
            _translate("AsteriskOperatorPanel", u"Panneau Opérateur Asterisk", None))

