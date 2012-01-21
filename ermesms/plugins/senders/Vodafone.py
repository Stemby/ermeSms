# -*- coding: utf-8 -*-

# TODO: unicode management
# TODO: translate to English
# NOTE: some strings are in Italian because this is an Italian Website

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

class Vodafone(Sender):
    """Permette di spedire SMS dal sito 190.it"""

    maxLength = 160
    """Lunghezza massima del messaggio singolo inviabile da questo sito."""

    requiresRegistration = ['Nome utente','Password','SIM']
    """Cosa richiede questo plugin?"""

    incValue = 7
    """Incremento della gauge per pagina."""

    def isAvailable(self):
        """Return True if this plugin is usable."""
        # A CaptchaDecoder must be available
        return CaptchaDecoder.getBestPlugin() is not None

    def isUnicodeCompliant(self):
        """Return True if the Web service is compatible with Unicode
        characters."""
        #return True # FIXME: it doesn't work... see:
                     #        ermesms.CodingManager.urlEncode(self, dictionary)
        return False

    def sendOne(self, number, text, data=None, ui=None):
        """Send an SMS message with only ASCII characters and maximum length
        maxLength using the specified credentials, supposing Internet
        reachable.
        """ # FIXME: why only ASCII?
        try:
            # Create a new cURL object and initialize it
            c = self.connectionManager.getCurl()

            # Set the standard variables
            username = data['Nome utente']
            password = data['Password']
            sim = str(data['SIM'])

            if number[:3] == "+39":
                number = number[3:]
            elif number[0]=="+":
                raise SiteCustomError(self.__class__.__name__,
                "With this website you can send SMS messages only to Italian "
                "mobile phones.")

            # Visit the starting page
            saver = StringIO()
            c.setopt(pycurl.URL, "http://www.vodafone.it/190/trilogy/jsp/home.do")
            self.perform(self.stop, saver)
            self.checkForErrors(saver.getvalue())
            self.checkManteinance(c.getinfo(pycurl.EFFECTIVE_URL))

            if ui: ui.gaugeIncrement(self.incValue)

            # Am I already logged in?
            if(re.search("Ciao ", saver.getvalue()) is None):
                # No; kill old cookies and log in
                self.connectionManager.forgetCookiesFromDomain("190.it")
                self.connectionManager.forgetCookiesFromDomain("vodafone.it")
                saver = StringIO()
                c.setopt(pycurl.URL, "https://www.vodafone.it/190/trilogy/jsp/login.do")
                postFields = {}
                postFields["username"] = username
                postFields["password"] = password
                c.setopt(pycurl.POST, True)
                c.setopt(pycurl.POSTFIELDS, self.codingManager.urlEncode(postFields))
                self.perform(self.stop, saver)

                self.checkForErrors(saver.getvalue())
                self.checkManteinance(c.getinfo(pycurl.EFFECTIVE_URL))

                if (re.search("Ciao ", saver.getvalue()) is None):
                    raise SiteAuthError(self.__class__.__name__)

            if ui: ui.gaugeIncrement(self.incValue)

            #se Sim e se non è attiva, cambio la SIM attiva
            if sim and (re.search('value="'+sim+'" selected >',
                                  saver.getvalue()) is None):
                saver = StringIO()
                c.setopt(pycurl.URL, "http://www.areaprivati.vodafone.it/190/trilogy/jsp/swapSim.do?tk=9616,1&ty_sim="+sim)
                self.perform(self.stop, saver)
                self.checkForErrors(saver.getvalue())
                self.checkManteinance(c.getinfo(pycurl.EFFECTIVE_URL))

            if ui: ui.gaugeIncrement(self.incValue)

            # Visit the obligatory advertising
            c.setopt(pycurl.POST, False)
            c.setopt(pycurl.URL,
                "http://www.vodafone.it/190/trilogy/jsp/dispatcher.do?ty_key=fdt_invia_sms&tk=9616,2")
            self.perform(self.stop)

            self.checkForErrors(saver.getvalue())
            self.checkManteinance(c.getinfo(pycurl.EFFECTIVE_URL))

            if ui: ui.gaugeIncrement(self.incValue)

            # Visit the SMS form
            c.setopt(pycurl.URL,
                "http://www.areaprivati.vodafone.it/190/trilogy/jsp/dispatcher.do?ty_key=fsms_hp&ipage=next")
            self.perform(self.stop)

            if ui: ui.gaugeIncrement(self.incValue)

            # Send the SMS message
            saver = StringIO()
            postFields = {}
            postFields["pageTypeId"] = "9604"
            postFields["programId"] = "10384"
            postFields["chanelId"] = "-18126"
            postFields["receiverNumber"] = number
            postFields["message"] = text
            c.setopt(pycurl.POST, True)
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode(postFields))
            c.setopt(pycurl.URL,
                "http://www.areaprivati.vodafone.it/190/fsms/prepare.do")
            self.perform(self.stop, saver)

            self.checkForErrors(saver.getvalue())
            self.checkManteinance(c.getinfo(pycurl.EFFECTIVE_URL))

            if (re.search(
                "Ti ricordiamo che puoi inviare SMS via Web solo a numeri di cellulare Vodafone",
                  saver.getvalue()) is not None or
                re.search(
                "Il numero di telefono del destinatario del messaggio non e' valido",
                saver.getvalue()) is not None):
                raise SiteCustomError(self.__class__.__name__,
                        u"Questo sito permette di inviare " +
                        u"SMS solo ai cellulari Vodafone.")
            if (re.search("box_sup_limitesms.gif", saver.getvalue()) is not None):
                raise SiteCustomError(self.__class__.__name__,
                                       u"Hai esaurito gli SMS gratis di oggi.")

            captchaBroken = False
            while captchaBroken == False:

                postFields = {}
                if re.search("generateimg.do", saver.getvalue()) is not None:
                    try:
                        saver = StringIO()
                        c.setopt(pycurl.POST, False)
                        c.setopt(pycurl.URL, "http://www.areaprivati.vodafone.it/190/fsms/generateimg.do")
                        self.perform(self.stop, saver)

                        self.checkForErrors(saver.getvalue())
                        self.checkManteinance(c.getinfo(pycurl.EFFECTIVE_URL))
                        postFields["verifyCode"] = CaptchaDecoder.getBestPlugin().decodeCaptcha(saver, self.__class__.__name__)
                        c.setopt(pycurl.POST, True)
                    except CaptchaError:
                        raise SenderError(self.__class__.__name__)
                    if not postFields["verifyCode"]:
                        raise SiteCustomError(self.__class__.__name__,
                                    u"Captcha non inserito. Invio interrotto.")

                if ui: ui.gaugeIncrement(self.incValue)
                postFields["pageTypeId"] = "9604"
                postFields["programId"] = "10384"
                postFields["chanelId"] = "-18126"
                postFields["receiverNumber"] = number
                postFields["message"] = text

                c.setopt(pycurl.POST, True)
                c.setopt(pycurl.POSTFIELDS,
                    self.codingManager.urlEncode(postFields))

                #Confermo l'invio
                saver = StringIO()
                c.setopt(pycurl.URL,
                    "http://www.areaprivati.vodafone.it/190/fsms/send.do")
                self.perform(self.stop, saver)

                if (re.search("generateimg.do", saver.getvalue()) is None):
                    captchaBroken = True
                elif ui: ui.gaugeIncrement(-self.incValue)

            if (re.search("Hai superato il limite giornaliero di SMS",
                saver.getvalue()) is not None):
                raise SiteCustomError(self.__class__.__name__,
                    u"Sono esauriti gli SMS gratuiti di oggi.")

            self.checkForErrors(saver.getvalue())
            self.checkManteinance(c.getinfo(pycurl.EFFECTIVE_URL))
            if (re.search("elaborata correttamente", saver.getvalue()) is None):
                raise SenderError(self.__class__.__name__)

        except pycurl.error, e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))

    def checkForErrors(self, page):
        """Solleva un'eccezione se la pagina contiene una segnalazione d'errore dal sito."""
        if(re.search("numero massimo di accessi", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Ci sono troppi utenti sul sito, riprova più tardi.")
        if(re.search("a causa di attivit&agrave; di manutezione sul sito", page) is not None):
            raise SiteCustomError(self.__class__.__name__, u"Il sito è in manutenzione, riprova più tardi.")

    def checkManteinance(self, url):
        if "courtesy" in url:
            raise SiteCustomError(self.__class__.__name__, u"Il sito è in manutenzione, riprova più tardi.")
