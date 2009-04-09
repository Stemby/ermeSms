# -*- coding: utf-8 -*-

from moio.errors.SenderError import SenderError

class CaptchaError(SenderError):
    """Errore per indicare un problema con la connessione ad un sito (scaricamento captcha)."""

    def __init__(self):
        """Costruttore standard."""
        SenderError.__init__(self, repr('Captcha'))

    def __str__(self):
        return u"Impossibile decodificare l'immagine captcha."
