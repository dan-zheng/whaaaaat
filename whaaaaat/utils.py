# -*- coding: utf-8 -*-
from __future__ import print_function
import json
import sys

from pygments import highlight, lexers, formatters

__version__ = '0.1.2'

PY3 = sys.version_info[0] >= 3


def format_json(data, sort_keys=True):
    return json.dumps(data, sort_keys=sort_keys, indent=4)


def colorize_json(data):
    if PY3:
        if isinstance(data, bytes):
            data = data.decode('UTF-8')
    else:
        if not isinstance(data, unicode):
            data = unicode(data, 'UTF-8')
    colorful_json = highlight(data,
                              lexers.JsonLexer(),
                              formatters.TerminalFormatter())
    return colorful_json


def print_json(data, sort_keys=True):
    print(colorize_json(format_json(data, sort_keys=sort_keys)))
