# -*- coding: utf-8 -*-

class StopError(Exception):
    """Indica l'interruzione di invio da parte dell'utente"""

    def __init__(self):
        """Costruttore standard."""
        Exception.__init__(self)

    def __str__(self):
        return u"Invio interrotto per richiesta dell'utente"
