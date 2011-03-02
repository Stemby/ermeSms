# -*- coding: utf-8 -*-

from ermesms.Plugin import Plugin
from ermesms.PriorityPlugin import PriorityPlugin

class CaptchaDecoder(PriorityPlugin):
    """Classe base dei plugin per la decodifica dei captcha."""

    def decodeCaptcha(self, stream, senderName):
        """Questo metodo ritorna la stringa corrispondente all'immagine
        leggibile dallo stream specificato."""
        raise NotImplementedError()
