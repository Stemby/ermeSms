# -*- coding: utf-8 -*-

from ConfigParser import ConfigParser

class CaseSensitiveConfigParser(ConfigParser):
    """Versione case sensitive del ConfigParser."""

    def optionxform(self, optionstr):
        """Evita l'applicazione del metodo lower() sulle opzioni."""
        return optionstr
