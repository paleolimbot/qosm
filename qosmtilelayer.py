'''
Created on Dec 30, 2015

@author: dewey
'''

import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import QgsProject, QgsPluginLayer, QgsPluginLayerType, QgsCoordinateTransform, \
                        QgsCoordinateReferenceSystem, QgsRasterLayer, QgsLogger, QgsMapLayerRegistry, \
                        QgsMapRenderer, QgsBilinearRasterResampler, QgsRectangle

import openstreetmap as osm
import downloaderthread as downloader
import tilemanagement as tm
import qosmsettings


class QOSMTileLayerType(QgsPluginLayerType):

    def __init__(self, plugin, add_callback):
        QgsPluginLayerType.__init__(self, QOSMTileLayer.LAYER_TYPE)
        self.plugin = plugin
        self.add_callback = add_callback

    def createLayer(self):
        layer = QOSMTileLayer("http://a.tile.openstreetmap.org/${z}/${x}/${y}.png", "OSM Plugin layer")
        self.add_callback(layer)
        return layer     

class QOSMTileLayer(QgsPluginLayer):
    
    LAYER_TYPE = "QOSM_LAYER_TYPE"
    
    def __init__(self, layertype, layerName):
        QgsPluginLayer.__init__(self, QOSMTileLayer.LAYER_TYPE, layerName)
        self.layertype = layertype
        self.loadedtiles = set()
        self.loadedlayers = {}
        self.setValid(True)
        self.actualzoom = None
        self.specifiedzoom = None #autozoom
        self.autorefresh = False
    
    def zoom(self, widthpx, extll):
        if self.specifiedzoom is None:
            autozoom = osm.autozoom(widthpx/(extll.xMaximum()-extll.xMinimum()))
            return min(max((tm.minzoom(self.layertype), autozoom)),
                       tm.maxzoom(self.layertype))
        else:
            numtiles = len(osm.tiles(extll.xMinimum(), extll.xMaximum(), 
                          extll.yMinimum(), extll.yMaximum(), self.specifiedzoom))
            if numtiles > qosmsettings.MAX_TILES_DEFAULT:
                return None
            else:
                return self.specifiedzoom
            
    
    def cleantiles(self):
        reg = QgsMapLayerRegistry.instance()
        for tile in self.loadedtiles:
            reg.removeMapLayer(self.loadedlayers[tile])
            del self.loadedlayers[tile]
        self.loadedtiles.clear()
    
    def refreshtiles(self, canvasextent, canvascrs, widthpx, forcedownload=False, triggerrepaint=True):
        tilestoclean, tilestoload, tilefiles = self.refreshtiles_get(canvasextent, canvascrs, widthpx, forcedownload)
        self.refreshtiles_apply(tilestoclean, tilestoload, tilefiles, canvasextent)
        if triggerrepaint:
            self.triggerRepaint()
    
    def refreshtiles_get(self, canvasextent, canvascrs, widthpx, forcedownload=False):
        xform = QgsCoordinateTransform(canvascrs,
                                    QgsCoordinateReferenceSystem(4326))
        extll = xform.transform(canvasextent)
        zoom = self.zoom(widthpx, extll)
        if zoom is None:
            return list(self.loadedtiles), [], []
        
        tiles = osm.tiles(extll.xMinimum(), extll.xMaximum(), 
                          extll.yMinimum(), extll.yMaximum(), zoom)
        
        if forcedownload:
            tilestoclean = list(self.loadedtiles)
            tilestoload = tiles
        else:
            tilestoclean = self.loadedtiles.difference(set(tiles))
            tilestoload = list(set(tiles).difference(self.loadedtiles))
        
        #calculate file names and urls
        tilefiles = [tm.filename("/Users/dewey/giscache/rosm.cache/", self.layertype, tile, zoom) for tile in tilestoload]
        tileurls = [tm.tileurl(self.layertype, tile, zoom) for tile in tilestoload]
        
        #download (keep on same thread for now)
        downloader.download(tileurls, tilefiles, overwrite=forcedownload)
        return tilestoclean, tilestoload, tilefiles
    
    def refreshtiles_apply(self, tilestoclean, tilestoload, tilefiles, extent):
        reg = QgsMapLayerRegistry.instance()
        #clean
        for tile in tilestoclean:
            reg.removeMapLayer(self.loadedlayers[tile])
            del self.loadedlayers[tile]
            self.loadedtiles.remove(tile)
        
        if len(tilestoload) > 0:
            self.actualzoom = tilestoload[0][2]
        else:
            self.actualzoom = None
        
        #load
        for i in range(len(tilestoload)):
            #check file exists
            if os.path.exists(tilefiles[i]):
                auxfile = tm.auxfilename(tilefiles[i])
                if not os.path.exists(auxfile):
                    osm.writeauxfile(*tilestoload[i], filename=auxfile)
                #create layer, add to self.loadedlayers, self.loadedtiles
                layername = "qosm_%s_x%s_y%s_z%s" % ((self.layertype,) + tilestoload[i])
                layer = QgsRasterLayer(tilefiles[i], layername)
                if layer.isValid():
                    layer = reg.addMapLayer(layer, False)
                    layer.resampleFilter().setZoomedOutResampler(QgsBilinearRasterResampler())
                    layer.resampleFilter().setZoomedInResampler(QgsBilinearRasterResampler())
                    
                    self.loadedlayers[tilestoload[i]] = layer.id()
                    self.loadedtiles.add(tilestoload[i])
                else:
                    #report error?
                    pass
                
            else:
                #report error?
                pass
        
        self.setExtent(extent)
    
    def createimage(self, extent, crs, outputsize):
        render = QgsMapRenderer()
        render.setLayerSet(self.loadedlayers.values())
        render.setProjectionsEnabled(True)
        render.setDestinationCrs(crs)
        render.setExtent(extent)
        
        img = QImage(outputsize, QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent) #needed, apparently the QImage() is not empty
                    
        painter = QPainter()
        painter.begin(img)
        painter.setRenderHint(QPainter.Antialiasing)
        render.setOutputSize(img.size(), img.logicalDpiX())
        render.render(painter)
        painter.end()
        return img
    
    def draw(self, rendererContext):
        #should be done on a different thread: invoke multithreaded rendering?
        extent = rendererContext.extent()
        crs = rendererContext.coordinateTransform().destCRS()
        outputsize = QSize(rendererContext.painter().device().width(),
                        rendererContext.painter().device().height())
        
        if self.autorefresh:
            tilestoclean, tilestoload, tilefiles = self.refreshtiles_get(extent, crs, outputsize.width())
            #check if rendering stopped before applying changes to object
            if rendererContext.renderingStopped():
                return True
            self.refreshtiles_apply(tilestoclean, tilestoload, tilefiles, extent)
        
        if len(self.loadedlayers) > 0:
            img = self.createimage(extent, crs, outputsize) 
            rendererContext.painter().drawImage(0, 0, img)            
        else:
            #no tiles. debug message?
            pass

        return True
    
        
        
        