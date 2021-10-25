#!/usr/bin/env python2

#############################################################################
##
## Copyright (C) 2010 Hans-Peter Jansen <hpj@urpla.net>.
## All rights reserved.
##
## This file is part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
###########################################################################
# This code was based on a cpp version found here:
# http://www.qtcentre.org/wiki/index.php?title=Rich_text_pushbutton_implementation

from PyQt4 import QtCore, QtGui


class RichTextPushButton(QtGui.QPushButton):
    SIZEADJ = 6
    def __init__(self, parent = None):
        super(RichTextPushButton, self).__init__(parent)
        self._htmlText = None
        self._isRichText = False
 
    def setHtml(self, text):
        self._htmlText = text
        self._isRichText = True
        palette = QtGui.QPalette()
        palette.setBrush(QtGui.QPalette.ButtonText, QtCore.Qt.transparent)
        self.setPalette(palette)

    def setText(self, text):
        self._isRichText = False
        super(RichTextPushButton, self).setText(text)

    def text(self):
        if self._isRichText:
            richText = QtGui.QTextDocument()
            richText.setHtml(self._htmlText)
            return richText.toPlainText()
        else:
            return super(RichTextPushButton, self).text()

    def sizeHint(self):
        if self._isRichText:
            richTextLabel = QtGui.QTextDocument()
            richTextLabel.setHtml(self._htmlText)
            sizeHint = QtCore.QSize(richTextLabel.size().width()
                                    + RichTextPushButton.SIZEADJ,
                                    richTextLabel.size().height()
                                    + RichTextPushButton.SIZEADJ)
            if not self.icon().isNull():
                sizeHint = QtCore.QSize(sizeHint.width()
                                        + self.iconSize().width()
                                        + RichTextPushButton.SIZEADJ,
                                        max(sizeHint.height()
                                            + RichTextPushButton.SIZEADJ,
                                            self.iconSize().height()
                                            + RichTextPushButton.SIZEADJ))
            return sizeHint
        else:
            return super(RichTextPushButton, self).sizeHint()

    def paintEvent(self, event):
        if self._isRichText:
            painter = QtGui.QStylePainter(self)
     
            buttonRect = QtCore.QRect(self.rect())
     
            richTextLabel = QtGui.QTextDocument()
            richTextLabel.setHtml(self._htmlText)
     
            richTextPixmap = QtGui.QPixmap(richTextLabel.size().width(),
                                           richTextLabel.size().height())
            richTextPixmap.fill(QtCore.Qt.transparent)
            richTextPainter = QtGui.QPainter(richTextPixmap)
            richTextLabel.drawContents(richTextPainter,
                                       QtCore.QRectF(richTextPixmap.rect()))
            richTextPainter.end()

            if not self.icon().isNull():
                point = QtCore.QPoint(buttonRect.x()
                                      + buttonRect.width() / 2
                                      + self.iconSize().width() / 2 + 2,
                                      buttonRect.y() + buttonRect.height() / 2)
            else:
                point = QtCore.QPoint(0, # buttonRect.x() + buttonRect.width() / 2 - 1,
                                      buttonRect.y() + buttonRect.height() / 2)
     
            buttonRect.translate(point.x(), # - richTextPixmap.width() / 2,
                                 point.y() - richTextPixmap.height() / 2)
     
            painter.drawControl(QtGui.QStyle.CE_PushButton, self.getStyleOption())
            painter.drawPixmap(buttonRect.left(), buttonRect.top(),
                               richTextPixmap.width(), richTextPixmap.height(),
                               richTextPixmap)
        else:
            super(RichTextPushButton, self).paintEvent(event)
    
    def getStyleOption(self):
        opt = QtGui.QStyleOptionButton()
        opt.initFrom(self)
        opt.features = QtGui.QStyleOptionButton.None
        if self.isFlat():
            opt.features |= QtGui.QStyleOptionButton.Flat
        if self.menu():
            opt.features |= QtGui.QStyleOptionButton.HasMenu
        if self.autoDefault() or self.isDefault():
            opt.features |= QtGui.QStyleOptionButton.AutoDefaultButton
        if self.isDefault():
            opt.features |= QtGui.QStyleOptionButton.DefaultButton
        if self.isDown() or (self.menu() and self.menu().isVisible()):
            opt.state |= QtGui.QStyle.State_Sunken
        if self.isChecked():
            opt.state |= QtGui.QStyle.State_On
        if not self.isFlat() and not self.isDown():
            opt.state |= QtGui.QStyle.State_Raised
        opt.text = self.text()
        opt.icon = self.icon()
        opt.iconSize = self.iconSize()
        return opt


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)

    rtb = RichTextPushButton()
    rtb.setHtml("Do not press <font color=red><b>THIS</b></font> button!")
    rtb.setIcon(QtGui.QIcon("/usr/share/icons/oxygen/32x32/actions/draw-brush.png"))
    rtb.setIconSize(QtCore.QSize(32, 32))
    rtb.show()

    sys.exit(app.exec_())

