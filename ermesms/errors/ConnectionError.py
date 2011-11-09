# -*- coding: utf-8 -*-

class ConnectionError(Exception):
    """Indica un problema con la connessione Internet."""


    def __init__(self):
        """Costruttore standard."""
        Exception.__init__(self)

    def __str__(self):
        return u"Errore di connessione. Internet funziona?"
