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

class Enel(Sender):
    """Permette di spedire SMS dal sito Enel.it"""

    maxLength = 110
    """Lunghezza massima del messaggio singolo inviabile da questo sito."""

    requiresRegistration = ['Nome utente','Password']
    """Cosa richiede questo plugin?"""

    incValue = 5
    """Incremento della gauge per pagina."""

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
            c = self.connectionManager.getCurl()

            #Assegna le variabili standard
            username = dati['Nome utente']
            password = dati['Password']

            if number[:3] == "+39":
                number = number[3:]
            elif number[0]=="+":
                raise SiteCustomError(self.__class__.__name__,
                u"Questo sito permette di inviare SMS solo verso cellulari italiani.")

            #Visito la pagina iniziale
            c.setopt(pycurl.URL, "http://www.enel.it")
            self.perform(self.stop)

            if ui: ui.gaugeIncrement(self.incValue)

            #Faccio il login
            saver = StringIO()
            c.setopt(pycurl.POST, True)
            postFields = {}
            postFields["SpontaneousLogon"] = "/Index.asp"
            postFields["txtUsername"] = username
            postFields["txtPassword"] = password
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode(postFields, self.encoding))
            c.setopt(pycurl.URL, "http://www.enel.it/AuthFiles/Login.aspx")
            self.perform(self.stop, saver)

            if (re.search("Autenticazione fallita", saver.getvalue()) != None):
                raise SiteAuthError(self.__class__.__name__)

            if ui: ui.gaugeIncrement(self.incValue)

            #Visito la pagina degli SMS
            saver = StringIO()
            c.setopt(pycurl.POST, False)
            c.setopt(pycurl.REFERER, "http://www.enel.it/Index.asp")
            c.setopt(pycurl.URL, "http://servizi.enel.it/sms/")
            self.perform(self.stop, saver)

            checkCode = ""
            try:
                checkCode = re.search('<input type="hidden" name="cksmsenel" value="([A-Z0-9]+)"',saver.getvalue()).group(1)
            except AttributeError:
                raise SenderError(self.__class__.__name__)

            if ui: ui.gaugeIncrement(self.incValue)

            #Pre-invio
            saver = StringIO()
            c.setopt(pycurl.POST, True)
            postFields = {}
            postFields["message"] = text
            postFields["prefix"] = number[0:3]
            postFields["gsm"] = number[3:]
            postFields["cksmsenel"] = checkCode
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode(postFields, self.encoding))
            c.setopt(pycurl.URL,
                "http://servizi.enel.it/sms/service/scrivisms.asp?SMSstartpage=http://www.enel.it/Index.asp")
            self.perform(self.stop, saver)

            if (re.search("superato il limite massimo",
                saver.getvalue()) != None):
                raise SiteCustomError(self.__class__.__name__,
                    u"Sono esauriti gli SMS gratuiti di oggi.")

            checkCode = ""
            xFieldKey = ""
            xFieldValue = ""
            try:
                checkCode = re.search('<INPUT TYPE=hidden NAME=cksmsenel VALUE="([A-Z0-9]+)"',saver.getvalue()).group(1)
                match = re.search('<INPUT TYPE=hidden NAME=x([0-9]+) VALUE=\'([0-9]+)\'>',saver.getvalue())
                xFieldKey = match.group(1)
                xFieldValue = match.group(2)
            except AttributeError:
                raise SenderError(self.__class__.__name__)

            if ui: ui.gaugeIncrement(self.incValue)

            #Accetto il contratto
            saver = StringIO()
            c.setopt(pycurl.POST, True)
            postFields = {}
            postFields["message"] = text
            postFields["prefix"] = number[0:3]
            postFields["gsm"] = number[3:]
            postFields["accetta"] = "yes"
            postFields["x"+str(xFieldKey)] = str(xFieldValue)
            postFields["cksmsenel"] = checkCode
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode(postFields, self.encoding))

            c.setopt(pycurl.URL,
                "http://servizi.enel.it/sms/service/scrivisms.asp")
            self.perform(self.stop, saver)

            if (re.search("superato il limite massimo",
                saver.getvalue()) != None):
                raise SiteCustomError(self.__class__.__name__,
                    u"Sono esauriti gli SMS gratuiti di oggi.")
            if (re.search("inviato correttamente", saver.getvalue()) is None):
                raise SenderError(self.__class__.__name__)

        except pycurl.error, e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))

