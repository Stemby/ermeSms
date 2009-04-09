# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from moio.errors.SiteConnectionError import SiteConnectionError
from moio.errors.SenderError import SenderError
from moio.errors.CaptchaError import CaptchaError

class CaptchaDialog(QDialog):

    image = None
    """Immagine captcha da visualizzare."""

    def __init__(self, mf):
        QDialog.__init__(self, mf, mf.defaultFlag)
        self.captchaLabel = QLabel("Not Loaded")
        self.decodeText = QLineEdit("")
        self.okButton = QPushButton("OK")
        
        self.__set_properties()
        self.__do_layout()

        self.connect(self.okButton, SIGNAL('clicked(bool)'),
                     self.okButtonEventHandler)

    def __set_properties(self):
        self.setWindowTitle("Scrivi quello che leggi!")
        self.decodeText.setFocus()
        self.okButton.setDefault(True)

    def __do_layout(self):

        vbox = QVBoxLayout()
        vbox.addWidget(self.captchaLabel, 0)
        vbox.addWidget(self.decodeText, 0)
        vbox.addWidget(self.okButton, 0)

        self.setLayout(vbox)
        self.resize(self.minimumSizeHint())

    def okButtonEventHandler(self, event):
        """Chiude la finestra."""
        self.done(1)

    def getUserInput(self):
        """Ritorna la stringa immessa dall'utente."""
        text = unicode(self.decodeText.text())
        return text

    def setImage(self, stream):
        stream.seek(0)
        pixmap = QPixmap()
        loaded = pixmap.loadFromData(stream.getvalue())
        if not loaded: raise
        self.captchaLabel.setPixmap(pixmap)       
