# -*- coding: utf-8 -*-

# TODO: translate to English

import re
from cStringIO import StringIO

import pycurl

from ermesms.plugins.Sender import Sender
from ermesms.ConnectionManager import ConnectionManager
from ermesms.errors.SiteCustomError import SiteCustomError
from ermesms.errors.SiteConnectionError import SiteConnectionError
from ermesms.errors.SiteAuthError import SiteAuthError
from ermesms.errors.SenderError import SenderError

class Aimon(Sender):
    """Permette di spedire SMS acquistati dal sito Aimon.it"""

    maxLength = 160
    """Lunghezza massima del messaggio singolo inviabile da questo sito."""

    requiresRegistration = ['Nome utente','Password']
    """Cosa richiede questo plugin?"""

    def __init__(self):
        self.encoding = 'FIXME'

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

            if number[0] != "+": number = '39' + number
            else: number = number[1:]

            #Assegna le variabili standard
            username = dati['Nome utente']
            password = dati['Password']

            #Invio di un sms
            c.setopt(pycurl.POST, True)
            testo = self.codingManager.quoteBase64(text)[:-1]
            postFields = {}
            postFields["authlogin"] = username + '@aimon.it'
            postFields["authpasswd"] = password
            postFields["body"] = testo
            postFields["destination"] = number
            postFields["id_api"] = "106"
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode(postFields, self.encoding))
            c.setopt(pycurl.URL, 'https://secure.apisms.it/http/send_sms')
            saver = StringIO()
            self.perform(self.stop, saver)

            self.checkForErrors(saver.getvalue())

            if (re.search("SMS Queued", saver.getvalue()) is None):
                raise SenderError(self.__class__.__name__)

        except pycurl.error, e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))

    def checkForErrors(self, page, last = None):
        """Solleva un'eccezione se la pagina contiene una segnalazione d'errore dal sito."""
        if(re.search("Access denied", page) is not None):
            raise SiteAuthError(self.__class__.__name__)
        if(re.search("destination invalid parameter type", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Destinatario non valido")
        if(re.search("body not specified", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Manca il testo")
        if(re.search("sender contains invalid characters or is too long", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Mittente non valido")
        if(re.search("Not enough credit", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Credito esaurito")
        if(re.search("body contains invalid characters or is too long", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Testo non valido")

