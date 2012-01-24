# -*- coding: utf-8 -*-

# TODO: translate to English

from ermesms.lib.singletonmixin import Singleton

class Plugin(Singleton):
    """Classe-base dei plugin di ermeSms.

    Questa classe permette di creare ed utilizzare in ermeSms i "plugin":
    moduli che aggiungono funzionalità al programma (come interfacce utente
    o classi per l'invio degli SMS).
    Ogni plugin, a seconda di arbitrarie condizioni verificate a runtime,
    può essere disponibile o meno (vedi metodo isAvaliable).
    """

    def isAvailable(self):
        """Ritorna true se questo plugin è utilizzabile."""
        raise NotImplementedError()

    def getPlugins(cls):
        """Ritorna un'istanza di ogni plugin disponibile in un dizionario
        indicizzato per nome.
        """
        result = {}
        classes = cls.__subclasses__()
        for i in classes:
            obj = i.getInstance()
            if obj.isAvailable():
                result[i.__name__] = obj
        return result
    getPlugins = classmethod(getPlugins)

