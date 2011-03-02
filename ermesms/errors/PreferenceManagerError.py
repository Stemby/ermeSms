# -*- coding: utf-8 -*-

class PreferenceManagerError(Exception):
    """Indica che il PreferenceManager ha un errore generico."""


    description = u""

    def __init__(self, description):
        Exception.__init__(self)
        self.description = description

    def __str__(self):
        return self.description
