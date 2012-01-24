# -*- coding: utf-8 -*-

# TODO: translate to English

import re
import sys
from cStringIO import StringIO

import pycurl

from ermesms.plugins.Sender import Sender
from ermesms.ConnectionManager import ConnectionManager
from ermesms.errors.SiteCustomError import SiteCustomError
from ermesms.errors.SiteConnectionError import SiteConnectionError
from ermesms.errors.SiteAuthError import SiteAuthError
from ermesms.errors.SenderError import SenderError

class YesMMS(Sender):
    """Permette di spedire SMS dal sito www.yesmms.com"""

    maxLength = 500
    """Lunghezza massima del messaggio singolo inviabile da questo sito."""

    requiresRegistration = ['Nome utente','Password']
    """Cosa richiede questo plugin?"""

    incValue = 4
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
            #Costruisco un nuovo oggetto Curl e lo inizializzo
            c = self.connectionManager.getCurl()

            if not number[0] == "+": number = '+39' + number

            #Assegna le variabili standard
            username = dati['Nome utente']
            password = dati['Password']

            #Visito la pagina iniziale
            saver = StringIO()
            c.setopt(pycurl.POST, True)
            postFields = {}
            postFields["B1"] = 'logon'
            postFields["action"] = 'login'
            postFields["nick"] = username
            postFields["password"] = password
            c.setopt(pycurl.POSTFIELDS, self.codingManager.urlEncode(
                postFields, self.encoding))
            c.setopt(pycurl.URL, "http://www.yesmms.com/cgi-bin/yesmms/yesstart.cgi")
            self.perform(self.stop, saver)

            if (re.search("Wrong Password", saver.getvalue()) is not None):
                raise SiteAuthError(self.__class__.__name__)
            if (re.search("Login again at", saver.getvalue()) is not None):
                raise SiteCustomError(self.__class__.__name__, u"Errore di Login")
            if (re.search("did not logout correctly", saver.getvalue()) is not None):
                raise SiteCustomError(self.__class__.__name__, u"Utente gia' loggato, riprova tra 30 minuti")

            try:
                session = re.search('(?<=(session" value="))[^"]+', saver.getvalue()).group(0)
                time = re.search('(?<=(nowtime" value="))[^"]+', saver.getvalue()).group(0)                
            except AttributeError:
                raise SenderError(self.__class__.__name__)

            if ui: ui.gaugeIncrement(self.incValue)

            #Visito la pagina intermedia
            saver = StringIO()
            c.setopt(pycurl.POST, True)
            postFields = {}
            postFields["session"] = session
            postFields["nowtime"] = time
            postFields["country"] = '212'
            postFields["lang"] = 'it'
            postFields["submit"] = 'continue'
            c.setopt(pycurl.POSTFIELDS, self.codingManager.urlEncode(
                postFields, self.encoding))
            c.setopt(pycurl.URL, "http://www.yesmms.com/cgi-bin/yesmms/yesintro.cgi")
            self.perform(self.stop, saver)

            if ui: ui.gaugeIncrement(self.incValue)

            #Visito la una pagina degli sms
            saver = StringIO()
            c.setopt(pycurl.POST, True)
            postFields = {}
            postFields["session"] = session
            postFields["lang"] = 'it'
            c.setopt(pycurl.POSTFIELDS, self.codingManager.urlEncode(
                postFields, self.encoding))
            c.setopt(pycurl.URL, "http://www.yesmms.com/cgi-bin/yesmms/yeslogin.cgi")
            self.perform(self.stop, saver)

            if ui: ui.gaugeIncrement(self.incValue)

            #Spedisco l'SMS
            saver = StringIO()
            postFields = {}
            postFields["number_friend"] = 'NO'
            postFields["number"] = number
            postFields["message"] = text
            postFields["session"] = session
            postFields["action"] = 'send'
            c.setopt(pycurl.POST, True)
            c.setopt(pycurl.POSTFIELDS,
            self.codingManager.urlEncode(postFields, self.encoding))

            c.setopt(pycurl.URL,"http://www.yesmms.com/cgi-bin/yesmms/yesmms.cgi")
            self.perform(self.stop, saver)

            #Eseguo il logout
            postFields = {}
            postFields["session"] = session
            c.setopt(pycurl.POST, True)
            c.setopt(pycurl.POSTFIELDS,
            self.codingManager.urlEncode(postFields, self.encoding))
            c.setopt(pycurl.URL,"http://www.yesmms.com/cgi-bin/yesmms/yeslogout.cgi")
            self.perform(self.stop)

            if (re.search("SMS sent", saver.getvalue()) is None):
                if (re.search("The message contains bad", saver.getvalue()) is not None):
                    raise SiteCustomError(self.__class__.__name__, u"Il messaggio contiene parole proibite")                
                elif (re.search("You already sent a", saver.getvalue()) is not None):
                    raise SiteCustomError(self.__class__.__name__, u"Hai gia' inviato un SMS a questo numero")
                elif (re.search("You need at least", saver.getvalue()) is not None):
                    raise SiteCustomError(self.__class__.__name__, u"Hai esaurito i crediti disponibili")
                elif (re.search("not been sent", saver.getvalue()) is not None):
                    raise SiteCustomError(self.__class__.__name__, u"Messaggio non inviato")
                elif (re.search("The max. number of FREE SMS per hour has been reached", saver.getvalue()) is not None):
                    raise SiteCustomError(self.__class__.__name__, u"Limite orario di sms raggiunto, riprova piu' tardi")                
                else: raise SenderError(self.__class__.__name__)

        except pycurl.error, e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))

