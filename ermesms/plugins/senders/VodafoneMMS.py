# -*- coding: utf-8 -*-

import re
import sys
from cStringIO import StringIO

import pycurl

from ermesms.plugins.Sender import Sender
from ermesms.plugins.CaptchaDecoder import CaptchaDecoder
from ermesms.ConnectionManager import ConnectionManager
from ermesms.errors.SiteCustomError import SiteCustomError
from ermesms.errors.CaptchaError import CaptchaError
from ermesms.errors.SiteConnectionError import SiteConnectionError
from ermesms.errors.SiteAuthError import SiteAuthError
from ermesms.errors.SenderError import SenderError

class VodafoneMMS(Sender):
    """Permette di spedire MMS testuali dal sito vodafone.it"""

    maxLength = 500
    """Lunghezza massima del messaggio singolo inviabile da questo sito."""

    requiresRegistration = ['Mittente']
    """Cosa richiede questo plugin?"""

    def isAvailable(self):
        """Ritorna true se questo plugin è utilizzabile."""
        return True

    def sendOne(self, number, text, dati = None, ui = None):
        """Spedisce un SMS con soli caratteri ASCII e di lunghezza massima maxLength
        con le credenziali specificate, supponendo Internet raggiungibile.
        """
        try:
            #Costruisco un nuovo oggetto Curl e lo inizializzo
            c = self.connectionManager.getCurl()

            #Assegna le variabili standard
            mittente = dati['Mittente']

            if number[:3] == "+39":
                number = number[3:]
            elif number[0]=="+":
                raise SiteCustomError(self.__class__.__name__,
                u"Questo sito permette di inviare SMS solo verso cellulari italiani.")

            #Invio l'sms
            saver = StringIO()
            postFields = {}
            postFields["recipient"] = "+39" + number
            postFields["subjecttosend"] = "Da: "+mittente
            postFields["SmilName"] = ""
            postFields["TextName"] = text
            postFields["ImageName"] = ""
            postFields["AudioName"] = ""
            postFields["nextPage"] = "/web/servletresult.html"
            c.setopt(pycurl.POST, True)
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode(postFields))
            c.setopt(pycurl.URL, "http://mmsviaweb.net.vodafone.it/WebComposer/web/elaborapop.jsp")
            self.perform(self.stop, saver)
            self.checkForErrors(saver.getvalue())

            if (re.search("Il tuo messaggio &egrave; stato inviato", saver.getvalue()) is None):
                raise SenderError(self.__class__.__name__)

        except pycurl.error, e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))

    def checkForErrors(self, page):
        """Solleva un'eccezione se la pagina contiene una segnalazione d'errore dal sito."""
        if(re.search("verificato un errore durante la procedura", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Il sito è in manutenzione, riprova più tardi.")
