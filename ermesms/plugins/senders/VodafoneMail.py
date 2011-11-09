# -*- coding: utf-8 -*-

import re

import smtplib

from ermesms.plugins.Sender import Sender
from ermesms.ConnectionManager import ConnectionManager
from ermesms.errors.SiteConnectionError import SiteConnectionError

class VodafoneMail(Sender):
    """Permette di spedire SMS acquistati dal sito Aimon.it"""
   
    maxLength = 150
    """Lunghezza massima del messaggio singolo inviabile da questo sito."""
   
    requiresRegistration = ['eMail','Mittente']
    """Cosa richiede questo plugin?"""
   
    def isAvailable(self):
        """Ritorna true se questo plugin è utilizzabile."""
        return True
       
    def sendOne(self, number, text, dati = None, ui = None):
        """Spedisce un SMS con soli caratteri ASCII e di lunghezza massima maxLength
        con le credenziali specificate, supponendo Internet raggiungibile.
        """

        try:
            mail_from = dati['eMail']
            mittente = dati['Mittente']
            #Costruisco un nuovo oggetto SMTP
            sms = smtplib.SMTP()
                        
            if number[0] == "+": number = number[3:]

            #Invio di un sms
            
            mail_to = number + '@sms.vodafone.it'
            mail_message = 'From: ' + mittente + ' <' + mail_from +\
                           '>\r\nTo: <' + mail_to + '>\r\nSubject:\r\n' +\
                           'Content-Type: text/plain;\r\nX-Priority: ' +\
                           '3\r\n\r\n' + text
            sms.connect('smtp-sms.vodafone.it', port=25)
            sms.helo()
            sms.sendmail(mail_from, mail_to, mail_message)            
           
        except smtplib.SMTPException, e:
            errno, msg = e
            raise SiteConnectionError(self.__class__.__name__, self.codingManager.iso88591ToUnicode(msg))
