# -*- coding: utf-8 -*-

# TODO: translate to English

import math

import pycurl

from ermesms.Plugin import Plugin
from ermesms.ConnectionManager import ConnectionManager
from ermesms.CodingManager import CodingManager
from ermesms.errors.TooLongMessageError import TooLongMessageError
from ermesms.errors.ConnectionError import ConnectionError

class Sender(Plugin):
    """Classe base dei plugin che spediscono SMS via Internet."""

    codingManager = CodingManager.getInstance()
    """Istanza locale del gestore della codifica."""
    connectionManager = ConnectionManager.getInstance()
    """Istanza locale del gestore delle connessioni."""
    maxLength = 160
    """Lunghezza massima del messaggio singolo inviabile da un sito."""
    requiresRegistration = None
    """Cosa richiede questo plugin per funzionare?"""
    stop = False
    """Indicatore per interrompere l'invio"""
    perform = connectionManager.ePerform
    """Reimplementazione di curl perform"""

    def sendOne(self, number, text, dati = None, ui = None):
        """Spedisce un SMS con soli caratteri ASCII e di lunghezza massima maxLength
        con le credenziali specificate, supponendo Internet raggiungibile.
        """
        raise NotImplementedError()

    def send(self, proxy, number, text, dati = None, ui = None):
        """Spedisce un SMS (con le eventuali credenziali specificate)."""
        #Controllo pre-condizioni
        self.connectionManager.setCurlProxy(proxy)
        if self.connectionManager.isInternetReachable() == False:
            raise ConnectionError()
        if not self.isUnicodeCompliant():
            text = self.replaceNonAscii(text)
        length = len(text)
        if length > self.maxLength*99:#massima lunghezza 99 messaggi maxLength caratteri ognuno
            raise TooLongMessageError()
        texts = self.splitText(text)
        self.stop = False
        for i in texts:
            #resetta la gauge
            if ui: ui.gaugeIncrement(0)
            self.sendOne(number, i, dati, ui)

    def replaceNonAscii(sender, text):
        """Replace some non-ASCII characters with similar ASCII expressions."""
        replace_map = (
                (u"à", "a'"), (u"á", "a'"), (u"è", "e'"), (u"é", "e'"),
                (u"í", "i'"), (u"ì", "i'"), (u"ó", "o'"), (u"ò", "o'"),
                (u"ú", "u'"), (u"ù", "u'"), (u"À", "A'"), (u"È", "E'"),
                (u"É", "E'"), (u"Ì", "I'"), (u"Ò", "O'"), (u"Ù", "U'"),
                (u"ç", "c"), (u"[", "("), (u"]", ")"), (u"{", "("),
                (u"}", ")"), (u"^", ""), (u"£", "L."), (u"\\", "BkSlash"),
                (u"|", "Pipe"), (u"§", "Par."), (u"°", "o"), (u"€", "EUR"),
                (u"~", "Tilde"), (u"`", "'"), (u"¡", ""), (u"¿", ""))
        for old, new in replace_map: text = text.replace(old, new)
        return text

    def splitText(self, text):
        """Spezza il testo in messaggi da maxLength caratteri numerati."""
        textLength = len(text)
        if textLength <= self.maxLength:
            result = [text]
        else:
            result = []
            remainingText = text
            #calcola il numero di messaggi totale e il prefisso da aggiungere
            n = self.countTexts(text)
            if (n<=9):
                format = "%(i)d/%(n)d "
            elif(n <= 99):
                format = "%(i)02d/%(n)02d "
            else:
                format = "%(i)03d/%(n)03d "
            i=1
            while len(remainingText)>0:
                prefix = format % {'i':i, 'n': n}
                prefixLength = len(prefix)
                pieceLength = self.maxLength - prefixLength
                result.append(prefix + remainingText[0:pieceLength])
                remainingText = remainingText[pieceLength:]
                i+=1
        return result

    def countTexts(self, text):
        """Ritorna il numero di SMS necessari per inviare il testo passato."""
        textLength = len(text)
        if (textLength <= self.maxLength):
            return 1
        if (textLength <= (self.maxLength - 4)*9):
            return int(math.ceil(textLength/(self.maxLength - 4.0)))
        elif(textLength <= (self.maxLength - 6)*99):
            return int(math.ceil(textLength/(self.maxLength - 6.0)))
        else:
            return int(math.ceil(textLength/(self.maxLength - 8.0)))

    def newCharCount(self, text):
        if self.isUnicodeCompliant():
            textLength = len(text)
            textCount = self.countTexts(text)
        else:
            textLength = len(self.replaceNonAscii(text))
            textCount = self.countTexts(self.replaceNonAscii(text))
        if textCount == 2:
            return (textLength - self.maxLength)
        elif textCount != 1:
            prefixLength = int(math.log10(textCount-1))*2+4
            return (textLength-(self.maxLength-prefixLength)*(textCount-1))

