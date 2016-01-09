'''
Created on Dec 30, 2015

@author: dewey
'''

import os
import hashlib
import random

BUILT_IN_TILETYPES = {"osm":["http://a.tile.openstreetmap.org/${z}/${x}/${y}.png",
                             "http://b.tile.openstreetmap.org/${z}/${x}/${y}.png",
                             "http://c.tile.openstreetmap.org/${z}/${x}/${y}.png"],
                      "stamenbw": ["http://a.tile.stamen.com/toner/${z}/${x}/${y}.png",
                                   "http://b.tile.stamen.com/toner/${z}/${x}/${y}.png"
                                   "http://c.tile.stamen.com/toner/${z}/${x}/${y}.png"],
                      "thunderforestlandscape": ["http://a.tile.thunderforest.com/landscape/${z}/${x}/${y}.png",
                                                "http://b.tile.thunderforest.com/landscape/${z}/${x}/${y}.png",
                                                "http://c.tile.thunderforest.com/landscape/${z}/${x}/${y}.png"],
                      "thunderforestoutdoors": ["http://a.tile.thunderforest.com/outdoors/${z}/${x}/${y}.png",
                                                "http://b.tile.thunderforest.com/outdoors/${z}/${x}/${y}.png",
                                                "http://c.tile.thunderforest.com/outdoors/${z}/${x}/${y}.png"],
                      "hillshade":["http://c.tiles.wmflabs.org/hillshading/${z}/${x}/${y}.png",],
                      "stamenwatercolor":["http://a.tile.stamen.com/watercolor/${z}/${x}/${y}.jpg",
                                          "http://b.tile.stamen.com/watercolor/${z}/${x}/${y}.jpg",
                                          "http://c.tile.stamen.com/watercolor/${z}/${x}/${y}.jpg"],
                      "mapquestsat":["http://otile1.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg",
                                     "http://otile2.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg",
                                     "http://otile3.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg",
                                     "http://otile4.mqcdn.com/tiles/1.0.0/sat/${z}/${x}/${y}.jpg"]}

BUILT_IN_MAXZOOM = {"osm":19,
                  "stamenbw": 19,
                  "thunderforestlandscape": 19,
                  "thunderforestoutdoors": 19,
                  "hillshade": 14, #can be less in some areas
                  "stamenwatercolor":15,
                  "mapquestsat":11} #only 8 in rosm?

BUILT_IN_LABELS = {"osm":"Open Street Map",
                  "stamenbw": "Stamen (Black & White)",
                  "thunderforestlandscape": "Thunderforest Landscape",
                  "thunderforestoutdoors": "Thunderforest Outdoors",
                  "hillshade": "Hillshading", #can be less in some areas
                  "stamenwatercolor":"Stamen (Watercolor)",
                  "mapquestsat":"Mapquest Satellite"} #only 8 in rosm?

def tileurl(tiletype, tile, zoom, suffix=""):
    '''
    Would probably like to be able to pass a custom format in here. Support
    for quadkey and suffixes (like the bing token). Possible returning of random
    urls for multiple tile servers?
    '''
    if tiletype in BUILT_IN_TILETYPES:
        pattern = BUILT_IN_TILETYPES[tiletype]
        if isinstance(pattern, list):
            pattern = random.sample(pattern, 1)[0]
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

def tilesize(tiletype):
    return (256, 256)

def filename(cachefolder, tiletype, tile, zoom):
    return os.path.join(cachefolder, tiletypekey(tiletype), 
                        "{z}_{x}_{y}{ext}".format(z=zoom, x=tile[0], y=tile[1], ext=tileext(tiletype)))

def auxfilename(fname):
    return fname + ".aux.xml"

def maxzoom(tiletype):
    if tiletype in BUILT_IN_MAXZOOM:
        return BUILT_IN_MAXZOOM[tiletype]
    else:
        return 20

def minzoom(tiletype):
    return 1