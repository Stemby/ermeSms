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
from ermesms.plugins.captchadecoders.AskUserCaptchaDecoder import AskUserCaptchaDecoder
from ermesms.errors.CaptchaError import CaptchaError

class Rossoalice(Sender):
    """Permette di spedire SMS dal sito rossoalice.it"""

    maxLength = 150
    """Lunghezza massima del messaggio singolo inviabile da questo sito."""

    requiresRegistration = ['Nome utente','Password']
    """Cosa richiede questo plugin?"""

    incValue = 5
    """Incremento della gauge per pagina."""

    def __init__(self):
        self.encoding = 'FIXME'

    def isAvailable(self):
        """Ritorna true se questo plugin è utilizzabile."""
        return AskUserCaptchaDecoder.getInstance().isAvailable()

    def sendOne(self, number, text, dati = None, ui = None):
        """Spedisce un SMS con soli caratteri ASCII e di lunghezza massima maxLength
        con le credenziali specificate, supponendo Internet raggiungibile.
        """
        try:
            c = self.connectionManager.getCurl()

            #Assegna le variabili standard
            username = dati['Nome utente']
            password = dati['Password']

            #Ammazzo i vecchi cookie
            self.connectionManager.forgetCookiesFromDomain("alice.it")

            #Faccio il login
            saver = StringIO()
            c.setopt(pycurl.POST, True)
            postFields = {}
            postFields["URL_OK"] = "http://portale.rossoalice.alice.it/ps/HomePS.do?area=posta&settore=sms"
            postFields["URL_KO"] = "http://portale.rossoalice.alice.it/ps/ManageCodError.do?channel=mail_ra&area=posta&settore=sms"
            postFields["usr"] = username
            postFields["channel"] = "mail_ra"
            postFields["login"] = username + "@alice.it"
            postFields["password"] = password
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode(postFields, self.encoding))
            c.setopt(pycurl.URL,
                "http://authsrs.alice.it/aap/validatecredential")
            self.perform(self.stop, saver)
            if ((re.search(u'non sono corretti', saver.getvalue()) is not None) or
               (re.search(u"utenza inserita al momento non ", saver.getvalue()) is not None) or
               (re.search(u"Riprova pi&ugrave; tardi ad accedere ad Alice Mail e servizi.", saver.getvalue()) is not None)):
                raise SiteAuthError(self.__class__.__name__)
            if ui: ui.gaugeIncrement(self.incValue)

            c.setopt(pycurl.URL, "http://auth.rossoalice.alice.it/aap/serviceforwarder?sf_dest=click_to_send_sms&ID_Value=&ID_Field=mobilphone")
            self.perform(self.stop)

            saver = StringIO()
            c.setopt(pycurl.URL, "http://webloginmobile.rossoalice.alice.it/alice/jsp/SMS/composer.jsp?ID_Field=0&ID_Value=0&id_clickto=0&dummy=dummy")
            self.perform(self.stop, saver)

            #Patch di Laurento Frittella
            if (re.search("L'invio dell'SMS ad ogni destinatario ha un costo di", saver.getvalue()) is not None):
                raise SiteCustomError(self.__class__.__name__, u"Sono esauriti gli SMS gratuiti di oggi.")

            if ui: ui.gaugeIncrement(self.incValue)

            #Spedisco l'SMS
            postFields = {}
            postFields["DEST"] = number
            postFields["TYPE"] = "smsp"
            postFields["SHORT_MESSAGE2"] = text
            postFields["SHORT_MESSAGE"] = text
            postFields["INVIA_SUBITO"] = "true"

            c.setopt(pycurl.URL, "http://webloginmobile.rossoalice.alice.it/alice/jsp/SMS/CheckDest.jsp")
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode(postFields, self.encoding))
            self.perform(self.stop)

            c.setopt(pycurl.URL, "http://webloginmobile.rossoalice.alice.it/alice/jsp/SMS/inviaSms.jsp")
            c.setopt(pycurl.POSTFIELDS,
                self.codingManager.urlEncode(postFields, self.encoding))
            self.perform(self.stop)

            if ui: ui.gaugeIncrement(self.incValue)

            saver = StringIO()
            c.setopt(pycurl.POST, False)
            c.setopt(pycurl.REFERER, "http://webloginmobile.rossoalice.alice.it/alice/jsp/SMS/inviaSms.jsp")
            c.setopt(pycurl.URL, "http://webloginmobile.rossoalice.alice.it/alice/jsp/EwsJCaptcha.jpg")
            self.perform(self.stop, saver)
            if saver.getvalue() == "":
                raise SiteCustomError(self.__class__.__name__, u"Il sito non è disponibile, riprova più tardi.")

            if ui: ui.gaugeIncrement(self.incValue)

            postFields = {}
            postFields["DEST"] = number
            postFields["TYPE"] = "smsp"
            postFields["SHORT_MESSAGE2"] = text
            postFields["SHORT_MESSAGE"] = text
            postFields["INVIA_SUBITO"] = "true"
            try:
                postFields["captchafield"]=AskUserCaptchaDecoder.getInstance().decodeCaptcha(saver, self.__class__.__name__)
            except CaptchaError: print "An error occurred while trying to decode captcha"
            c.setopt(pycurl.POST, True)
            c.setopt(pycurl.POSTFIELDS,
                  self.codingManager.urlEncode(postFields, self.encoding))
            saver = StringIO()
            c.setopt(pycurl.URL, "http://webloginmobile.rossoalice.alice.it/alice/jsp/SMS/inviaSms.jsp")
            self.perform(self.stop, saver)
            if (re.search("Attenzione!&nbsp;I&nbsp;caratteri&nbsp;inseriti&nbsp;non&nbsp;sono&nbsp;corretti.",
                saver.getvalue()) is not None):
                raise SiteCustomError(self.__class__.__name__, u"I caratteri inseriti non sono corretti.")

            if (re.search(
                "&Egrave; possibile inviare gratuitamente fino a 10 SMS al giorno",
                saver.getvalue()) is not None):
                raise SiteCustomError(self.__class__.__name__,
                    u"Sono esauriti gli SMS gratuiti di oggi.")

            if (re.search("inviato con successo", saver.getvalue()) is None):
                raise SenderError(self.__class__.__name__)

        except pycurl.error, e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))

