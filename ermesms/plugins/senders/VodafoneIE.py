# -*- coding: utf-8 -*-
import re
import sys
from cStringIO import StringIO

import pycurl
import time

from ermesms.plugins.Sender import Sender
from ermesms.ConnectionManager import ConnectionManager
from ermesms.errors.SiteCustomError import SiteCustomError
from ermesms.errors.SiteConnectionError import SiteConnectionError
from ermesms.errors.SiteAuthError import SiteAuthError
from ermesms.errors.SenderError import SenderError

class VodafoneIE(Sender):
    """Permette di spedire 600 SMS dal sito vodafone.ie"""

    maxLength = 160
    """Lunghezza massima del messaggio singolo inviabile da questo sito."""

    requiresRegistration = ['Nome utente','Password']
    """Cosa richiede questo plugin?"""

    incValue = 4
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

            #Assegna le variabili standard
            username = dati['Nome utente']
            password = dati['Password']

            if number[0]=="+":
                number = '00'+number[1:]
            elif number[:2]!= '00':
                number = '0039'+number

            #Visito la pagina iniziale
            saver = StringIO()
            c.setopt(pycurl.URL, "https://www.vodafone.ie/index.jsp")
            self.perform(self.stop, saver)
            self.checkForErrors(saver.getvalue())

            if ui: ui.gaugeIncrement(self.incValue)                      

            if re.search('vodafone.ie/myv/services/login/Login.shtml\?ts=', saver.getvalue()) is not None:
                try:          
                    ts = re.search('(?<=(vodafone.ie/myv/services/login/Login.shtml\?ts=))[^"]', saver.getvalue()).group(0)
                except AttributeError:
                    raise SenderError(self.__class__.__name__)

                #Faccio Login
                saver = StringIO()
                c.setopt(pycurl.URL, "https://www.vodafone.ie/myv/services/login/Login.shtml?ts="+ts)
                postFields = {}
                postFields["acc-password-txt"] = 'Password'            
                postFields["username"] = username
                postFields["password"] = password
                c.setopt(pycurl.POST, True)
                c.setopt(pycurl.POSTFIELDS, self.codingManager.urlEncode(postFields))
                self.perform(self.stop, saver)
                self.checkForErrors(saver.getvalue())

            if ui: ui.gaugeIncrement(self.incValue)            

            #Visito il form degli SMS
            saver = StringIO()
            c.setopt(pycurl.POST, False)
            c.setopt(pycurl.URL,
                "https://www.vodafone.ie/myv/messaging/webtext/index.jsp")
            self.perform(self.stop, saver)

            try:          
                token = re.search('(?<=(TOKEN" value="))[^"]+', saver.getvalue()).group(0)
            except AttributeError:
                raise SenderError(self.__class__.__name__)

            if ui: ui.gaugeIncrement(self.incValue)

            time.sleep(3)

            #Spedisco l'SMS
            saver = StringIO()
            c.setopt(pycurl.REFERER,
                     'https://www.vodafone.ie/myv/messaging/webtext/index.jsp')
            postFields = {}       
            postFields["org.apache.struts.taglib.html.TOKEN"] = token
            postFields["message"] = text
            postFields["recipients[0]"] = number
            postFields["recipients[1]"] = ''
            postFields["recipients[2]"] = ''
            postFields["recipients[3]"] = ''
            postFields["recipients[4]"] = ''            
            postFields["futuredate"] = 'false'
            postFields["futuretime"] = 'false'
            c.setopt(pycurl.POST, True)
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode(postFields))
            c.setopt(pycurl.URL,
                "https://www.vodafone.ie/myv/messaging/webtext/Process.shtml")
            self.perform(self.stop, saver)
            self.checkForErrors(saver.getvalue())
            
            if (re.search("Message sent!", saver.getvalue()) is None):
                raise SenderError(self.__class__.__name__)

        except pycurl.error, e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))

    def checkForErrors(self, page):
        """Solleva un'eccezione se la pagina contiene una segnalazione d'errore dal sito."""
        if(re.search("Please check your details", page) is not None):
            raise SiteAuthError(self.__class__.__name__)
        if(re.search("Current customers may need to reactivate their mobiles by Topping Up your Call Credit", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Devi ricaricare la sim per tornare ad inviare SMS gratis")
        if(re.search("One or more Numbers is required", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Numero del destinatario mancante")
        if(re.search("Message is required", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Testo del messaggio mancante")
        if(re.search("We're sorry, an error has occurred", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Errore del server")
