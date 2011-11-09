# -*- coding: utf-8 -*-

class NotFoundError(Exception):
    """Indica che il nome o il numero in rubrica non è stato trovato."""


    name = ""

    def __init__(self, name):
        Exception.__init__(self)
        self.name = name

    def __str__(self):
        return self.name + u" non è in rubrica."
