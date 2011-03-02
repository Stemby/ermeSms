# -*- coding: utf-8 -*-

from ermesms.errors.SenderError import SenderError

class SiteAuthError(SenderError):
    """Errore di un Sender: username e password vengono rifiutate."""


    def __init__(self, site):
        """Costruttore standard."""
        SenderError.__init__(self, site)

    def __str__(self):
        return u"Nome utente e password non sono stati accettati dal sito."
