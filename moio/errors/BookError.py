#!/usr/bin/python
# -*- coding: utf8 -*-
# created by Francesco Marella <francesco.marella@gmail.com> on Wed Sep 24

class BookError:
    """Errore nel Book"""

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message
