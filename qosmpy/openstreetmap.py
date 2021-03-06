from __future__ import division
import math

from qgis.core import QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsRectangle, QgsPoint

__PROJECTOR = QgsCoordinateTransform(QgsCoordinateReferenceSystem(4326), 
                                     QgsCoordinateReferenceSystem(3857))

def unproject(extent, crs):
    xform = QgsCoordinateTransform(crs, QgsCoordinateReferenceSystem(4326))
    return xform.transformBoundingBox(extent)

def quadkey(tilex, tiley, zoom):
    nzoom = 2 ** zoom
    out = ""
    keymap = [["0", "1"],["2", "3"]]
    decx = float(tilex)/float(nzoom)
    decy = float(tiley)/float(nzoom)
    for i in range(1,zoom+1):
        x = int(decx*(2**i)) - int(decx*(2**(i-1)))*2
        y = int(decy*(2**i)) - int(decy*(2**(i-1)))*2
        out += keymap[y][x]
    return out

def nwcorner(tilex, tiley, zoom):
    n = 2.0 ** zoom
    lon_deg = tilex / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * tiley / n)))
    lat_deg = math.degrees(lat_rad)
    return (lon_deg, lat_deg)

def params(tilex, tiley, zoom, imagesize=(256, 256)):
    topleft= nwcorner(tilex, tiley, zoom)
    bottomright = nwcorner(tilex+1, tiley+1, zoom)
    ext = __PROJECTOR.transform(QgsRectangle(QgsPoint(*topleft), 
                                             QgsPoint(*bottomright)))
    
    return {"toplat":topleft[1],
            "bottomlat":bottomright[1],
            "leftlon":topleft[0],
            "rightlon":bottomright[0],
            "xmin":ext.xMinimum(),
            "xmax":ext.xMaximum(),
            "ymin":ext.yMinimum(),
            "ymax":ext.yMaximum(),
            "height":ext.height(),
            "width":ext.width(),
            "perpixelx":(ext.width()/float(imagesize[0])),
            "perpixely":(-ext.height()/float(imagesize[1]))} #negative built in

def tile(lon, lat, zoom):
        maxTile = 2 ** zoom - 1
        n = 2.0 ** zoom
        xtile = int((lon + 180.0) / 360.0 * n)
        if lat >= 85.0511287798066:
            ytile = 0
        elif lat <= -85.0511287798066:
            ytile = maxTile
        else:
            lat_rad = math.radians(lat)
            ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
        if xtile > maxTile:
            xtile = maxTile
        elif xtile < 0:
            xtile = 0   
        return (xtile, ytile, zoom)

def tiles(minlon, maxlon, minlat, maxlat, zoom):
    tile1 = tile(minlon, maxlat, zoom)
    tile2 = tile(maxlon, minlat, zoom)
    tilesout = []
    for tilex in range(tile1[0], tile2[0]+1):
        for tiley in range(tile1[1], tile2[1]+1):
            tilesout.append((tilex, tiley, zoom))
    return tilesout

def autozoom(pxPerDegreeWidth):
    zoom = math.log((360.0 / 256.0) * pxPerDegreeWidth) / math.log(2.0)
    return int(round(zoom))
    
def writeauxfile(tilex, tiley, zoom, filename, imagesize=(256, 256)):
    pars = params(tilex, tiley, zoom, imagesize)
    fout = open(filename, "w")
    fout.write('<PAMDataset>\n  <SRS>PROJCS["WGS 84 / Pseudo-Mercator",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Mercator_1SP"],PARAMETER["central_meridian",0],PARAMETER["scale_factor",1],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["X",EAST],AXIS["Y",NORTH],EXTENSION["PROJ4","+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext  +no_defs"],AUTHORITY["EPSG","3857"]]</SRS>\n')
    fout.write('  <GeoTransform>{xmin}, {perpixelx}, 0.0, {ymax}, 0.0, {perpixely}</GeoTransform>\n'.format(**pars))
    fout.write('</PAMDataset>')
    fout.close()
