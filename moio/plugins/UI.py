# -*- coding: utf-8 -*-

from moio.Plugin import Plugin
from moio.PriorityPlugin import PriorityPlugin

class UI(PriorityPlugin):
    """Classe base dei plugin per le interfacce utente."""

    def run(self):
        """Avvia questa interfaccia."""
        raise NotImplementedError()

    def showFatalException(self, message):
        """Questo metodo viene richiamato nel caso in cui venga catturata
        un'eccezione non gestita nel programma principale."""
        raise NotImplementedError()
