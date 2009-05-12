# -*- coding: utf-8 -*-

from moio.PreferenceManager import PreferenceManager

class SenderError(Exception):
    """Errore durante l'esecuzione di un Sender."""

    def __init__(self, site):
        """Costruttore standard."""
        Exception.__init__(self)
        self.site = site

    def __str__(self):
        msg = (u"Il sito " + self.site + u" si è rifiutato di mandare il tuo sms. \n"+
               u"Ci possono essere due ragioni: \n" +
               u"1) il sito " + self.site + u" ha un problema temporaneo \n"
               u"oppure \n" +
               u"2) il sito " + self.site + u" è stato modificato, pertanto \n"+
               u"MoioSMS necessita un aggiornamento. \n\n" +
               u"Se il problema persiste ed è possibile inviare SMS \n" +
               u"dal Web, controlla che non sia uscita una nuova \n" +
               u"versione sul forum del sito ufficiale: \n"
               u"http://www.moioli.net/forum/")

        return (msg)


