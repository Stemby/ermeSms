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

    def sendOne(self, number, text, data=None, ui=None):
        """Send an SMS message with maximum length maxLength using the specified
        credentials, supposing Internet reachable."""
        raise NotImplementedError()

    def send(self, proxy, number, text, data=None, ui=None):
        """Send an SMS message (with any specified credentials)."""
        #Controllo pre-condizioni
        self.connectionManager.setCurlProxy(proxy)
        if self.connectionManager.isInternetReachable() == False:
            raise ConnectionError()
        text = self.replaceSpecialChars(text)
        length = len(text)
        if length > self.maxLength*99:#massima lunghezza 99 messaggi maxLength caratteri ognuno
            raise TooLongMessageError()
        texts = self.splitText(text)
        self.stop = False
        for i in texts:
            #resetta la gauge
            if ui: ui.gaugeIncrement(0)
            self.sendOne(number, i, data, ui)

    def replaceSpecialChars(self, text):
        """Replace non-recognized characters with similar expressions."""
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
        textLength = len(self.replaceSpecialChars(text))
        textCount = self.countTexts(self.replaceSpecialChars(text))
        if textCount == 2:
            return (textLength - self.maxLength)
        elif textCount != 1:
            prefixLength = int(math.log10(textCount-1))*2+4
            return (textLength-(self.maxLength-prefixLength)*(textCount-1))

