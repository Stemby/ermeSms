# -*- coding: utf-8 -*-

from ermesms.errors.SenderError import SenderError

class SiteConnectionError(SenderError):
    """Errore per indicare un problema con la connessione ad un sito."""

    def __init__(self, site, msg = None):
        """Costruttore standard."""
        SenderError.__init__(self, site)
        self.msg = msg

    def __str__(self):
        s = u"Il sito " + self.site
        if 'Operation timed out after' in self.msg: self.msg = None
        if self.msg is None:
            s += u" non risponde.\n"
        else:
            s += u" ha risposto con l'errore:\n"+ self.msg + u"\n"
        s += (u"Per favore controlla che:\n" +
             u"1) Internet funzioni,\n" +
             u"2) il sito " + self.site + " sia raggiungibile,\n" +
             u"3) sia possibile inviare SMS da " + self.site + u".\n" +
             u"Se il problema persiste ed è possibile inviare SMS \n" +
             u"dal Web, controlla che non sia uscita una nuova \n" +
             u"versione sul sito ufficiale: https://github.com/sylarpowa/ermeSms")
        return s
