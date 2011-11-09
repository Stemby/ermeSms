# -*- coding: utf-8 -*-

from ermesms.Plugin import Plugin

class PriorityPlugin(Plugin):
    """Classe-base dei plugin a priorità di MoioSMS.

    Ogni istanza di PriorityPlugin ha associata una priorità (ritornata dal metodo
    getPriority). In presenza di più plugin disponibili a diversa priorità, va
    utilizzato preferenzialmente il plugin a priorità massima (ritornato dal metodo
    getBestPlugin).
    """

    def getPriority(self):
        """Ritorna un indice di priorità (intero)."""
        raise NotImplementedError()

    def getBestPlugin(cls):
        """Ritorna un'istanza del plugin disponibile a massima priorità o None se
        non esistono plugin disponibili.
        """
        result = None
        all = cls.getPlugins()
        for i in all.values():
            if result is None:
                result = i
            else:
                if i.getPriority()>result.getPriority():
                    result = i
        return result
    getBestPlugin = classmethod(getBestPlugin)
