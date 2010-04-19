# -*- coding: utf-8 -*-

from moio.errors.SenderError import SenderError

class SiteCustomError(SenderError):
    """Errore specifico di un Sender."""

    def __init__(self, site, msg):
        """Costruttore standard."""
        SenderError.__init__(self, site)
        self.msg = msg

    def __str__(self):
        return self.msg
