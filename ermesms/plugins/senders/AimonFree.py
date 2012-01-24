# -*- coding: utf-8 -*-

import re
from cStringIO import StringIO

import pycurl

from ermesms.plugins.Sender import Sender
from ermesms.ConnectionManager import ConnectionManager
from ermesms.errors.SiteCustomError import SiteCustomError
from ermesms.errors.SiteConnectionError import SiteConnectionError
from ermesms.errors.SiteAuthError import SiteAuthError
from ermesms.errors.SenderError import SenderError

class AimonFree(Sender):
    """Permette di spedire SMS dal sito Aimon.it"""
   
    maxLength = 114
    """Lunghezza massima del messaggio singolo inviabile da questo sito."""
   
    requiresRegistration = ['Nome utente','Password']
    """Cosa richiede questo plugin?"""

    incValue = 2
    """Incremento della gauge per pagina."""     
   
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
            
            if number[:3] == "+39": number = number[3:]

            #Assegna le variabili standard
            username = dati['Nome utente']
            password = dati['Password']                  
        
            c.setopt(pycurl.URL, "http://aimon.it/?cmd=smsgratis")
            postFields = {}
            postFields["inputUsername"] = username + '@aimon.it'
            postFields["inputPassword"] = password
            postFields["submit"] = 'procedi'
            c.setopt(pycurl.POST, True)
            c.setopt(pycurl.POSTFIELDS, self.codingManager.urlEncode(postFields))
            saver = StringIO()
            self.perform(self.stop, saver)
            self.checkForErrors(saver.getvalue())

            if ui: ui.gaugeIncrement(self.incValue)

            #Invio di un sms
            saver = StringIO()
            c.setopt(pycurl.POST, True)
            postFields = {}
            postFields["tiposms"] = '0'
            postFields["tipomittente"] = '1'
            postFields["testo"] = text
            postFields["destinatario"] = number
            postFields["btnSubmit"] = "Invia SMS"
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode(postFields))
            c.setopt(pycurl.URL, 'http://aimon.it/index.php?cmd=smsgratis&sez=smsgratis')
            self.perform(self.stop, saver)
            self.checkForErrors(saver.getvalue())
            
            if (re.search("Messaggio inviato con successo", saver.getvalue()) is None):
                raise SenderError(self.__class__.__name__)
           
        except pycurl.error, e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))

    def checkForErrors(self, page):
        """Solleva un'eccezione se la pagina contiene una segnalazione d'errore dal sito."""
        if(re.search("Username o Password errati", page) is not None):
            raise SiteAuthError(self.__class__.__name__)
        if(re.search("Credito non sufficiente", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"SMS gratuiti esauriti")
        if(re.search("Mittente non valido", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Il mittente deve essere un numero di telefono")
        if(re.search("Destinatario richiesto", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Manca il numero a cui inviare")
        if(re.search("Testo richiesto", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Testo messaggio vuoto")
        if(re.search("Messaggio non inviato per errore di spedizione", page) is not None):
            raise SiteSenderError(self.__class__.__name__)
        if(re.search("limite massimo di sms inviabili gratis in 24 ore", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Troppi sms in 24h per questo destinatario")
        if(re.search("limite massimo di sms inviabili gratis in 30 giorni", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Troppi sms in 30g per questo destinatario") 

