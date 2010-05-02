# -*- coding: utf-8 -*-

# TODO: finish to translate in English
# TODO: better aspect

import sys

from moio.CodingManager import CodingManager
from moio.plugins.Sender import Sender
from moio.plugins.UI import UI

class HelpUI(UI):
    """Interfaccia utente quando-tutto-il-resto-fallisce: una spiegazione
    dell'uso del programma."""

    def isAvailable(self):
        """Questa interfaccia è sempre utilizzabile."""
        return True

    def getPriority(self):
        """Priorità minima."""
        return 0

    def run(self):
        """Avvia questa interfaccia."""
        print "pyMoioSMS by Thomas Bertani\n"
        print "Website: http://github.com/sylarpowa/pyMoioSMS\n"
        print "USO:"
        print "MODALITA' INTERATTIVA: pymoiosms\n"
        print "MODALITA' A LINEA DI COMANDO: "
        print 'pymoiosms number "text" (send a SMS to a phone number)'
        print 'pymoiosms name "text" (send a SMS to a phone number present into the phone book)'
        print "pymoiosms -a name number (add a phone number into the phone book)"
        print "pymoiosms -s (display the phone book)\n"
        print "Per usare un sito in particolare, aggiungere uno dei parametri"
        print "seguenti:"
        for i in Sender.getPlugins():
            print i
        print "\nPer usare un proxy, aggiungere -p indirizzo:porta in coda"
        print "(usare -p no per disabilitare)"
        print "Rubrica, password e settaggi sono nel file .pymoiosms/config.ini."
        print "Commenti/Suggerimenti/Bug: sylar@anche.no"

    def showFatalException(self, message):
        """Questo metodo viene richiamato nel caso in cui venga catturata
        un'eccezione non gestita nel programma principale."""
        sys.stdout.write('\a')#Beep
        sys.stdout.flush()
        print CodingManager.getInstance().encodeStdout(message)
