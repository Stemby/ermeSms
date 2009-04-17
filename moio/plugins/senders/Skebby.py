# -*- coding: utf-8 -*-

import re
import sys
from cStringIO import StringIO

import pycurl

from moio.plugins.Sender import Sender
from moio.plugins.CaptchaDecoder import CaptchaDecoder
from moio.ConnectionManager import ConnectionManager
from moio.errors.SiteCustomError import SiteCustomError
from moio.errors.CaptchaError import CaptchaError
from moio.errors.SiteConnectionError import SiteConnectionError
from moio.errors.SiteAuthError import SiteAuthError
from moio.errors.SenderError import SenderError

class Skebby(Sender):
    """Permette di spedire SMS dal sito skebby.it"""

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
        """Spedisce un SMS con soli caratteri ASCII e di lunghezza massima maxLength
        con le credenziali specificate, supponendo Internet raggiungibile.
        """
        try:
            #Costruisco un nuovo oggetto Curl e lo inizializzo
            c = self.connectionManager.getCurl()

            #Assegna le variabili standard
            username = dati['Nome utente']
            password = dati['Password']
            #sim = str(dati['SIM'])

            #if number[:3] == "+39":
            #    number = number[3:]
            #elif number[0]=="+":
            #    raise SiteCustomError(self.__class__.__name__,
            #    u"Questo sito permette di inviare SMS solo verso cellulari italiani.")

            #Visito la pagina iniziale
            saver = StringIO()
            c.setopt(pycurl.WRITEFUNCTION, saver.write)
            c.setopt(pycurl.URL, "http://www.skebby.it/user/login/index/")
            self.perform(self.stop)
            self.checkForErrors(saver.getvalue())

            #if "http://lavori.vodafone.it/Courtesy.html" == c.getinfo(pycurl.EFFECTIVE_URL):
            #    raise SiteCustomError(self.__class__.__name__, u"Il sito è in manutenzione, riprova più tardi.")

            if ui: ui.gaugeIncrement(self.incValue)
            
            #Sono già autenticato?
            if(re.search("benvenuto nella tua area riservata", saver.getvalue()) is None):
                #No, ammazzo i vecchi cookie e mi riautentico
                self.connectionManager.forgetCookiesFromDomain("skebby.it")
                saver = StringIO()
                c.setopt(pycurl.WRITEFUNCTION, saver.write)
                c.setopt(pycurl.URL, "http://www.skebby.it/user/login/check/")
                postFields = {}
                postFields["useForwardAfterLogin"] = "1"
                postFields["submitImage.x"] = "20"
                postFields["submitImage.y"] = "16"
                postFields["username"] = username
                postFields["password"] = password
                c.setopt(pycurl.POST, True)
                c.setopt(pycurl.POSTFIELDS, self.codingManager.urlEncode(postFields))
                self.perform(self.stop)

                self.checkForErrors(saver.getvalue())

                if (re.search("benvenuto nella tua area riservata", saver.getvalue()) is None):
                    raise SiteAuthError(self.__class__.__name__)

            if ui: ui.gaugeIncrement(self.incValue)
            
            #se Sim e se non è attiva, cambio la SIM attiva
#            if sim and (re.search('value="'+sim+'" selected >',
#                                  saver.getvalue()) is None):
#                saver = StringIO()
#                c.setopt(pycurl.WRITEFUNCTION, saver.write)
#                c.setopt(pycurl.URL, "http://www.areaprivati.vodafone.it/190/trilogy/jsp/swapSim.do?tk=9616,1&ty_sim="+sim)
#                self.perform(self.stop)
#                self.checkForErrors(saver.getvalue())

#            if ui: ui.gaugeIncrement(self.incValue)

            #Visito la pubblicità obbligatoria
#            c.setopt(pycurl.POST, False)
#            c.setopt(pycurl.WRITEFUNCTION, self.doNothing)
#            c.setopt(pycurl.URL,
#                "http://www.vodafone.it/190/trilogy/jsp/dispatcher.do?ty_key=fdt_invia_sms&tk=9616,2")
#            self.perform(self.stop)

#            self.checkForErrors(saver.getvalue())

#            if ui: ui.gaugeIncrement(self.incValue)

            #Visito il form degli SMS (anche qui obbligatoriamente...)
            c.setopt(pycurl.URL,
                "http://www.skebby.it/services/sms/send/")
            self.perform(self.stop)

            if ui: ui.gaugeIncrement(self.incValue)

            #Spedisco l'SMS
            saver = StringIO()
            c.setopt(pycurl.WRITEFUNCTION, saver.write)
            postFields = {}
            postFields["elemento[0][sSOURCE_NUMBER]"] = "b"
            postFields["elemento[0][sDEST_PREFIX]"] = "39"
            postFields["elemento[0][sDEST_NUMBER]"] = number
            postFields["elemento[0][sTEXT]"] = text
            c.setopt(pycurl.POST, True)
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode(postFields))
            c.setopt(pycurl.URL,
                "http://www.skebby.it/services/sms/send/")
            self.perform(self.stop)

            self.checkForErrors(saver.getvalue())
            print saver.getvalue()

        except pycurl.error as e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))

    def checkForErrors(self, page):
        """Solleva un'eccezione se la pagina contiene una segnalazione d'errore dal sito."""
        if(re.search("numero massimo di accessi", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Ci sono troppi utenti sul sito, riprova più tardi.")

