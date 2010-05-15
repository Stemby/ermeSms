#!/bin/bash

PYTHON="@PYTHON@"
PYTHONDIR="@PYTHONDIR@"
test ${PYTHON:0:1} = "@" && PYTHON=python
test ${PYTHONDIR:0:1} = "@" && PYTHONDIR=$(dirname $0)

exec ${PYTHON} "$PYTHONDIR/moiosms.py" $*
