from __future__ import division
import math

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from geolib.geom2d import Bounds
from qpynygeolib.maplayers import LayerFactory
from .tiles import TiledBitmapLayer

def nwcorner(tilex, tiley, zoom):
    n = 2.0 ** zoom
    lon_deg = tilex / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * tiley / n)))
    lat_deg = math.degrees(lat_rad)
    return (lon_deg, lat_deg)

def extent(tilex, tiley, zoom):
    topleft= nwcorner(tilex, tiley, zoom)
    bottomright = nwcorner(tilex+1, tiley+1, zoom)
    return {"top":topleft[1],
            "bottom":bottomright[1],
            "left":topleft[0],
            "right":bottomright[0]}

def tile(lon, lat, zoom):
        maxTile = 2 ** zoom - 1
        n = 2.0 ** zoom
        xtile = int((lon + 180.0) / 360.0 * n)
        if lat >= 90:
            ytile = 0
        elif lat <= -90:
            ytile = maxTile
        else:
            lat_rad = math.radians(lat)
            ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
        if xtile > maxTile:
            xtile = maxTile
        elif xtile < 0:
            xtile = 0   
        return (xtile, ytile)

def tiles(minlon, maxlon, minlat, maxlat, zoom):
    tile1 = tile(minlon, maxlat, zoom)
    tile2 = tile(maxlon, minlat, zoom)
    tilesout = []
    for tilex in range(tile1[0], tile2[0]+1):
        for tiley in range(tile1[1], tile2[1]+1):
            tilesout.append((tilex, tiley))
    return tilesout


def tileurl(tiletype, tile, zoom):
    return "http://a.tile.openstreetmap.org/${z}/${x}/${y}.png".replace("$", "").format(z=zoom, x=tile[0], y=tile[1])
    
    
'''
s = QSettings()
oldValidation = s.value( "/Projections/defaultBehaviour", "useGlobal" ).toString()
s.setValue( "/Projections/defaultBehaviour", "useGlobal" )

ext = QgsRectangle(QgsPoint(-62.05078125, 45.70617928533084), QgsPoint(-61.875, 45.583289756006316))
tocrs = QgsCoordinateReferenceSystem(3857)
currentcrs = QgsCoordinateReferenceSystem(4326)
xform = QgsCoordinateTransform(currentcrs, tocrs)
extProj = xform.transform(ext)
rlayer = QgsRasterLayer("/Users/dewey/d/qgisplugins/qosm/11_671_731.png", "testname")
rlayer.setCrs(tocrs)


s.setValue( "/Projections/defaultBehaviour", oldValidation )



'''

class OpenStreetMapLayer(SlippyTileLayer):
    
    URL_SERVERS = ["http://a.tile.openstreetmap.org",
                    "http://b.tile.openstreetmap.org",
                    "http://c.tile.openstreetmap.org"]
    
    def __init__(self, layerId, cacheDir=None, zIndex=0):
        super(OpenStreetMapLayer, self).__init__(layerId, "openstreetmap", cacheDir, zIndex)
    
    def type(self):
        return "MapFrameLayer|BitmapLayer|TiledBitmapLayer|SlippyTileLayer|OpenStreetMapLayer"
    
    def tileUrls(self, tile):
        endString = "/%i/%i/%i.png" % (tile[2], tile[0], tile[1])
        return [server + endString for server in OpenStreetMapLayer.URL_SERVERS]

class MapQuestLayer(SlippyTileLayer):
    
    URL_SERVERS = ["http://otile1.mqcdn.com",
                   "http://otile2.mqcdn.com",
                   "http://otile3.mqcdn.com",
                   "http://otile4.mqcdn.com"]
    
    def __init__(self, layerId, cacheDir=None, zIndex=0):
        super(MapQuestLayer, self).__init__(layerId, "mapquest", cacheDir, zIndex)
    
    def type(self):
        return "MapFrameLayer|BitmapLayer|TiledBitmapLayer|SlippyTileLayer|MapQuestLayer"
    
    def tileUrls(self, tile):
        endString = "/tiles/1.0.0/osm/%i/%i/%i.jpg" % (tile[2], tile[0], tile[1])
        return [server + endString for server in MapQuestLayer.URL_SERVERS]
    
    def fileName(self, tile):
        return "%s_%i_%i_%i.jpg" % (self.tileType(), tile[2], tile[0], tile[1])
    
    def maxZoom(self):
        return 19
   
class MapQuestOpenAerialLayer(SlippyTileLayer):
    
    def __init__(self, layerId, cacheDir=None, zIndex=0):
        super(MapQuestOpenAerialLayer, self).__init__(layerId, "mapquestopenaerial", cacheDir, zIndex)
    
    def type(self):
        return "MapFrameLayer|BitmapLayer|TiledBitmapLayer|SlippyTileLayer|MapQuestOpenAerialLayer"
    
    def fileName(self, tile):
        return "%s_%i_%i_%i.jpg" % (self.tileType(), tile[2], tile[0], tile[1])
    
    def tileUrls(self, tile):
        endString = "/tiles/1.0.0/sat/%i/%i/%i.jpg" % (tile[2], tile[0], tile[1])
        return [server + endString for server in MapQuestLayer.URL_SERVERS]
    
    def maxZoom(self):
        return 12
    

    