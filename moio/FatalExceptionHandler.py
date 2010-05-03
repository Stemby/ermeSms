# -*- coding: utf-8 -*-

import sys
import traceback

class FatalExceptionHandler(object):
    """Gestisce le eccezioni che terminano il programma."""
    ui = None

    def __init__(self, ui):
        """Inizializza il gestore per l'interfaccia utente specificata."""
        self.ui = ui
        sys.excepthook = self.exceptionHook

    def exceptionHook(self, type, value, tb):
        """Metodo richiamato automaticamente per le eccezioni non gestite."""
        msg = "***SI E' VERIFICATO UN ERRORE IMPREVISTO***\n" +\
            "Per favore invia in una mail quanto\n" +\
            "riportato qui sotto:\n" +\
            "----------------------------------------------------------\n" +\
            "Eccezione: " + str(type) + "\n" +\
            "Valore: " + str(value) + "\n"
        for i in traceback.format_exception(type, value, tb):
            msg += i
        msg += "Argomenti dalla linea di comando: " + str(sys.argv) + "\n"+\
            "\nL'indirizzo mail al quale scrivere e':\n"+\
            "sylar@anche.no"

        #Visualizza l'errore
        self.ui.showFatalException(msg)

        #Termina il programma
        sys.exit(4)
