# -*- coding: utf-8 -*-

import re
import sys
from cStringIO import StringIO

import pycurl

from moio.plugins.Sender import Sender
from moio.ConnectionManager import ConnectionManager
from moio.plugins.CaptchaDecoder import CaptchaDecoder
from moio.errors.SiteCustomError import SiteCustomError
from moio.errors.CaptchaError import CaptchaError
from moio.errors.SiteConnectionError import SiteConnectionError
from moio.errors.SiteAuthError import SiteAuthError
from moio.errors.SenderError import SenderError

class Tim(Sender):
    """Permette di spedire SMS dal sito di tim.it"""

    maxLength = 160
    """Lunghezza massima del messaggio singolo inviabile da questo sito."""

    requiresRegistration = ['Nome utente','Password']
    """Cosa richiede questo plugin?"""

    incValue = 4
    """Incremento della gauge per pagina."""

    def isAvailable(self):
        """Ritorna true se questo plugin è utilizzabile."""
        #Deve essere disponibile un qualunque CaptchaDecoder
        return CaptchaDecoder.getBestPlugin() is not None

    def sendOne(self, number, text, dati = None, ui = None):
        """Spedisce un SMS con soli caratteri ASCII e di lunghezza massima
        maxLength con le credenziali specificate, supponendo Internet
        raggiungibile."""

        try:
            #Costruisco un nuovo oggetto Curl e lo inizializzo
            c = self.connectionManager.getCurl()

            if number[:3] == "+39":
                number = number[3:]
            elif number[0]=="+":
                raise SiteCustomError(self.__class__.__name__,
                u"Questo sito permette di inviare SMS solo verso cellulari italiani.")

            #Assegna le variabili standard
            username = dati['Nome utente']
            password = dati['Password']

            c.setopt(pycurl.URL, "http://www.tim.it")
            self.perform(self.stop)

            if ui: ui.gaugeIncrement(self.incValue)

            #Faccio il login
            saver = StringIO()
            c.setopt(pycurl.POST, True)
            postFields = {}
            postFields["urlOk"] = "https%3A%2F%2Fwww.tim.it%2F119%2Fconsumerdispatcher"
            postFields["portale"] = "timPortale"
            postFields["login"] = username
            postFields["password"] = password
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode(postFields))
            c.setopt(pycurl.URL,
                "https://www.tim.it/authfe/login.do")
            self.perform(self.stop, saver)

            if (re.search(u'loginerror.do', saver.getvalue()) is not None):
                raise SiteAuthError(self.__class__.__name__)

            if ui: ui.gaugeIncrement(self.incValue)

            saver = StringIO()
            captchaBroken = False
            while captchaBroken == False:
                saver = StringIO()
                c.setopt(pycurl.URL,
                    "https://www.tim.it/smsdaweb/smsdaweb.do")
                self.perform(self.stop, saver)

                if (re.search(
                    "Oggi hai raggiunto il numero massimo di SMS gratis a tua disposizione.",
                    saver.getvalue()) != None):
                    raise SiteCustomError(self.__class__.__name__,
                        u"Sono esauriti gli SMS gratuiti di oggi.")

                try:
                    savedPage = saver.getvalue()
                    idimage = re.search('src="/smsdaweb/imagecode.jpg\?([0-9\.]+)"',savedPage).group(1)
                except AttributeError:
                    raise SenderError(self.__class__.__name__)

                postFields = {}
                postFields["msg"] = text
                postFields["tel"] = number
                try:
                    saver = StringIO()
                    c.setopt(pycurl.POST, False)
                    c.setopt(pycurl.URL, "https://www.tim.it/smsdaweb/imagecode.jpg?"+idimage)
                    self.perform(self.stop, saver)
                    postFields["imagecode"] = CaptchaDecoder.getBestPlugin().decodeCaptcha(saver, self.__class__.__name__)
                    c.setopt(pycurl.POST, True)
                except CaptchaError:
                    raise SenderError(self.__class__.__name__)

                if not postFields["imagecode"]:
                    raise SiteCustomError(self.__class__.__name__,
                                    u"Captcha non inserito. Invio interrotto.")

                if ui: ui.gaugeIncrement(self.incValue)

                c.setopt(pycurl.POSTFIELDS,
                    self.codingManager.urlEncode(postFields))
                c.setopt(pycurl.URL,
                    "https://www.tim.it/smsdaweb/inviasms.do")
                saver = StringIO()
                self.perform(self.stop, saver)

                if re.search("Il testo inserito non corrisponde", saver.getvalue()) is None:
                    captchaBroken = True
                elif ui: ui.gaugeIncrement(-self.incValue)

            if re.search("Servizio non disponibile", saver.getvalue()) is not None:
                raise SiteCustomError(self, u"Tim dice che il servizio non è disponibile. "+
                    u"Controlla il numero e riprova più tardi...")

            if re.search("i seguenti destinatari non sono corretti", saver.getvalue()) is not None:
                raise SiteCustomError(self, "Puoi inviare SMS solo verso i cellulari Tim.")

            if (re.search("inviato correttamente.", saver.getvalue()) is None):
                raise SenderError(self.__class__.__name__)

        except pycurl.error as e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))
