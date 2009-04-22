# -*- coding: UTF-8 -*-

# Author:
#    Francesco Marella <francesco.marella@gmail.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import exceptions

#TODO: add logic for preferences

class PreferenceDialog(QDialog):

    def __init__(self, mf):
        QDialog.__init__(self, mf, mf.defaultFlag)

        self.bookComboBox = QComboBox()
        self.bookComboBox.addItems(['BuiltInBook', 'EvolutionBook'])
        self.okButton = QPushButton("Applica")
        self.closeButton = QPushButton("Chiudi")

        self.setMinimumWidth(100)             

        self.__set_properties()
        self.__do_layout()

        self.mf = mf
        self.connect(self.okButton, SIGNAL('clicked(bool)'),
                 self.okButtonEventHandler)
        self.connect(self.closeButton, SIGNAL('clicked(bool)'),
                 self, SLOT('close()'))
        
        posx = (QDesktopWidget().width()-self.width())/2
        posy = ((QDesktopWidget().height()/3*2)-self.height())/2
        self.move(posx,posy)           
        
    def __set_properties(self):
        self.setWindowTitle("Preferenze")
        self.okButton.setDefault(True)

    def __do_layout(self):

        vbox = QVBoxLayout()
        
        hbox_1 = QHBoxLayout()
        bookBox = QGroupBox("Seleziona la rubrica:")
        hbox_2 = QHBoxLayout()
        hbox_2.addWidget(self.bookComboBox, 1)
        bookBox.setLayout(hbox_2)
        hbox_1.addWidget(bookBox, 1)
        vbox.addLayout(hbox_1, 0)
        
        hbox_3 = QHBoxLayout()
        hbox_3.addWidget(self.okButton, 0)        
        hbox_3.addStretch(1)
        hbox_3.addWidget(self.closeButton, 0)
        vbox.addLayout(hbox_3, 0)

        self.setLayout(vbox)
        self.resize(self.sizeHint())

    def okButtonEventHandler(self):
        pass
    
    def closeEvent(self, event):
        """Evento di chiusura della finestra"""
        pass
