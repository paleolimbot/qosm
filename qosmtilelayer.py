'''
Created on Dec 30, 2015

@author: dewey
'''

import os, sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import QgsProject, QgsPluginLayer, QgsPluginLayerType, QgsCoordinateTransform, \
                        QgsCoordinateReferenceSystem, QgsRasterLayer, QgsLogger, QgsMapLayerRegistry, \
                        QgsMapRenderer

import openstreetmap as osm
import downloaderthread as downloader
import tilemanagement as tm


class QOSMTileLayerType(QgsPluginLayerType):

    def __init__(self, plugin, add_callback):
        QgsPluginLayerType.__init__(self, QOSMTileLayer.LAYER_TYPE)
        self.plugin = plugin
        self.add_callback = add_callback

    def createLayer(self):
        layer = QOSMTileLayer("osm", "OSM Plugin layer")
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
    
    def cleantiles(self):
        reg = QgsMapLayerRegistry.instance()
        for tile in self.loadedtiles:
            reg.removeMapLayer(self.loadedlayers[tile])
            del self.loadedlayers[tile]
        self.loadedtiles.clear()
    
    def refreshtiles(self, canvasextent, canvascrs, widthpx, triggerrepaint=False):
        xform = QgsCoordinateTransform(canvascrs,
                                    QgsCoordinateReferenceSystem(4326))
        extll = xform.transform(canvasextent)
        zoom = osm.autozoom(widthpx/(extll.xMaximum()-extll.xMinimum()))
        tiles = osm.tiles(extll.xMinimum(), extll.xMaximum(), 
                          extll.yMinimum(), extll.yMaximum(), zoom)
        
        reg = QgsMapLayerRegistry.instance()
        
        tilestoclean = self.loadedtiles.difference(set(tiles))
        for tile in tilestoclean:
            reg.removeMapLayer(self.loadedlayers[tile])
            del self.loadedlayers[tile]
            self.loadedtiles.remove(tile)
        
        tilestoload = list(set(tiles).difference(self.loadedtiles))
        
        #calculate file names and urls
        tilefiles = [tm.filename("/Users/dewey/giscache/rosm.cache/", "osm", tile, zoom) for tile in tilestoload]
        tileurls = [tm.tileurl("osm", tile, zoom) for tile in tilestoload]
        
        #download (keep on same thread for now)
        downloader.download(tileurls, tilefiles)
        
        #go through by tile and write aux information and load if necessary
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
                    self.loadedlayers[tilestoload[i]] = layer.id()
                    self.loadedtiles.add(tilestoload[i])
                else:
                    #report error?
                    pass
                
            else:
                #report error?
                pass
        
        self.setExtent(canvasextent)
        if triggerrepaint:
            self.triggerRepaint()
    
    def draw(self, rendererContext):
        #should be done on a different thread: invoke multithreaded rendering?
        self.refreshtiles(rendererContext.extent(), 
                   rendererContext.coordinateTransform().destCRS(),
                   rendererContext.painter().device().width(), triggerrepaint=False)
        
        
        if len(self.loadedlayers) > 0:
             
            render = QgsMapRenderer()
            render.setLayerSet(self.loadedlayers.values())
            render.setProjectionsEnabled(True)
            render.setDestinationCrs(rendererContext.coordinateTransform().destCRS())
            render.setExtent(rendererContext.extent())
            
            img = QImage(QSize(rendererContext.painter().device().width(),
                        rendererContext.painter().device().height()),
                  QImage.Format_ARGB32_Premultiplied)
            img.fill(Qt.transparent) #needed, apparently the QImage() is not empty
                        
            painter = QPainter()
            painter.begin(img)
            painter.setRenderHint(QPainter.Antialiasing)
            render.setOutputSize(img.size(), img.logicalDpiX())
            render.render(painter)
            painter.end()
             
            rendererContext.painter().drawImage(0, 0, img)            
        else:
            #no tiles. debug message?
            pass

        return True
    
        
        
        