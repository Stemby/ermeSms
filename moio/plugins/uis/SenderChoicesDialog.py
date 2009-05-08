# -*- coding: UTF-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from moio.plugins.Sender import Sender

class SenderChoicesDialog(QDialog):

    def __init__(self, mf):
        QDialog.__init__(self, mf, mf.defaultFlag)
        self.senderList = Sender.getPlugins().keys()
        self.senderList.sort()
        self.messageLabel = QLabel("Scegli i sender che utilizzerai (OK se " +
                                   "non sei sicuro)")
        self.okButton = QPushButton("OK")
        self.boxes = {}
        for i in self.senderList:
            self.boxes[i] = QCheckBox(i)
            self.boxes[i].setChecked(True)

        self.__set_properties()
        self.__do_layout()

        self.connect(self.okButton, SIGNAL('clicked(bool)'),
                     self.okButtonEventHandler)

        posx = (QDesktopWidget().width()-self.width())/2
        posy = ((QDesktopWidget().height()/3*2)-self.height())/2
        self.move(posx,posy)

    def __set_properties(self):
        self.setWindowTitle("Scegli i Sender")
        self.okButton.setDefault(True)

    def __do_layout(self):

        vbox = QVBoxLayout()
        hbox_1 = QHBoxLayout()
        hbox_1.addWidget(self.messageLabel, 0)
        hbox_1.addStretch(1)
        vbox.addLayout(hbox_1)
        vbox.addStretch(1)
        checkBox = QGroupBox("Scegli i Sender")
        grid = QGridLayout()
        y = 0
        x = 0
        for i in self.senderList:
            if y == 2:
                y = 0
                x += 1
            grid.addWidget(self.boxes[i], x, y)
            y += 1
        checkBox.setLayout(grid)
        vbox.addWidget(checkBox)
        vbox.addStretch(1)
        hbox_2 = QHBoxLayout()
        hbox_2.addStretch(1)
        hbox_2.addWidget(self.okButton, 0)
        hbox_2.addStretch(1)
        vbox.addLayout(hbox_2)

        self.setLayout(vbox)
        self.resize(self.minimumSizeHint())

    def okButtonEventHandler(self, event):
        self.done(1)

    def getSenderList(self):
        senderList = []
        for i in self.senderList:
            if self.boxes[i].isChecked():
                senderList.append(i)
        if not senderList:
            return self.senderList
        else: 
            return senderList


