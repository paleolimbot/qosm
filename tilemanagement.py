'''
Created on Dec 30, 2015

@author: dewey
'''

import os

def tileurl(tiletype, tile, zoom, suffix=""):
    '''
    Would probably like to be able to pass a custom format in here. Support
    for quadkey and suffixes (like the bing token). Possible returning of random
    urls for multiple tile servers?
    '''
    return "http://a.tile.openstreetmap.org/${z}/${x}/${y}.png".replace("$", "").format(z=zoom, x=tile[0], y=tile[1])+suffix

def tileext(tiletype, tile=(0,0), zoom=0):
    url = tileurl(tiletype, tile, zoom)
    return url[url.rfind("."):]

def filename(cachefolder, tiletype, tile, zoom):
    return os.path.join(cachefolder, tiletype, "{z}_{x}_{y}{ext}".format(z=zoom, x=tile[0], y=tile[1], ext=tileext(tiletype)))

def auxfilename(fname):
    return fname + ".aux.xml"

def maxzoom(tiletype):
    return 21

def minzoom(tiletype):
    return 1