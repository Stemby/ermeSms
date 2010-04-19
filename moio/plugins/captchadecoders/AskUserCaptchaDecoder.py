# -*- coding: utf-8 -*-

from moio.plugins.CaptchaDecoder import CaptchaDecoder
from moio.errors.CaptchaError import CaptchaError
from moio.plugins.uis.GraphicalUI import GraphicalUI

class AskUserCaptchaDecoder(CaptchaDecoder):
    """Chiede all'utente di decodificare il captcha. E' stupido, lo so."""

    def isAvailable(self):
        """Ritorna true se questo plugin è utilizzabile."""
        #Questo succede se c'è un'interfaccia grafica disponibile
        return GraphicalUI.getInstance().isAvailable()

    def getPriority(self):
        """Ritorna un indice di priorità (intero)."""
        return 1

    def decodeCaptcha(self, stream, sender):
        """Questo metodo ritorna la stringa corrispondente all'immagine
        leggibile dallo stream specificato."""
        GraphicalUI.getInstance().MainFrame.userDecodeCaptchaRequest(stream)
        result = GraphicalUI.getInstance().MainFrame.qCaptcha.get()
        if result == None: raise CaptchaError()
        else:
            return result
