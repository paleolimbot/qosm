'''
Created on Jan 4, 2016

@author: dewey
'''

import os

from PyQt4.QtCore import QSettings

MAX_TILES = "max_tiles"
CACHE_DIRECTORY = "cache_directory"
CUSTOM_TILE_TYPES = "custom_tile_types"

_ALLKEYS = (MAX_TILES, CACHE_DIRECTORY)

_DEFAULTS = {MAX_TILES: 70,
             CACHE_DIRECTORY: os.path.join(os.path.dirname(__file__),
                                            "qosm.cache")}

_SETTINGS_PREFIX = "/qgis/qosm_plugin/"

def get(key):
    settings = QSettings()
    return settings.value(_SETTINGS_PREFIX + key, _defaultsetting(key))

def put(key, value):
    settings = QSettings()
    settings.setValue(_SETTINGS_PREFIX + key, value)

def reset(key=None):
    if key is None:
        for akey in _ALLKEYS:
            reset(akey)
    else:
        settings = QSettings()
        settings.remove(_SETTINGS_PREFIX + key)
    
def _defaultsetting(key):
    if key == CUSTOM_TILE_TYPES:
        return {}
    elif key in _DEFAULTS:
        return _DEFAULTS[key]
    else:
        return None
