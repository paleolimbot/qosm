'''
Created on Dec 30, 2015

@author: dewey
'''

import os
import hashlib
import random

BUILT_IN_TILETYPES = {"osm":["http://a.tile.openstreetmap.org/${z}/${x}/${y}.png",
                             "http://b.tile.openstreetmap.org/${z}/${x}/${y}.png",
                             "http://c.tile.openstreetmap.org/${z}/${x}/${y}.png"]}

def tileurl(tiletype, tile, zoom, suffix=""):
    '''
    Would probably like to be able to pass a custom format in here. Support
    for quadkey and suffixes (like the bing token). Possible returning of random
    urls for multiple tile servers?
    '''
    if tiletype in BUILT_IN_TILETYPES:
        pattern = random.sample(BUILT_IN_TILETYPES[tiletype], 1)[0]
    else:
        pattern = tiletype
    return pattern.replace("$", "").format(z=zoom, x=tile[0], y=tile[1])+suffix

def tileext(tiletype, tile=(0,0), zoom=0):
    url = tileurl(tiletype, tile, zoom)
    return url[url.rfind("."):]

def tiletypekey(any_tile_type):
    if any_tile_type in BUILT_IN_TILETYPES:
        return any_tile_type
    else:
        m = hashlib.md5(any_tile_type)
        return m.hexdigest()

def filename(cachefolder, tiletype, tile, zoom):
    return os.path.join(cachefolder, tiletypekey(tiletype), 
                        "{z}_{x}_{y}{ext}".format(z=zoom, x=tile[0], y=tile[1], ext=tileext(tiletype)))

def auxfilename(fname):
    return fname + ".aux.xml"

def maxzoom(tiletype):
    return 21

def minzoom(tiletype):
    return 1