'''
Created on Dec 30, 2015

@author: dewey
'''

import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import QgsProject, QgsPluginLayer, QgsPluginLayerType, QgsCoordinateTransform, \
                        QgsCoordinateReferenceSystem, QgsRasterLayer, QgsLogger, QgsMapLayerRegistry, \
                        QgsMapLayerRenderer, QgsMapRenderer

import openstreetmap as osm
import downloaderthread as downloader
import tilemanagement as tm


class QOSMTileLayerType(QgsPluginLayerType):

    def __init__(self):
        QgsPluginLayerType.__init__(self, QOSMTileLayer.LAYER_TYPE)

    def createLayer(self):
        return QOSMTileLayer()

class MultiRasterRenderer(QgsMapLayerRenderer):
    
    def __init__(self, layer, context, rasterlayers):
        QgsMapLayerRenderer.__init__(self, layer.id())
        self.context = context
        self.rasterlayers = rasterlayers
        self.img = QImage(QSize(context.painter().device().width(),
                                context.painter().device().height()),
                          QImage.Format_ARGB32_Premultiplied)
    
    def render(self):
        rendererContext = self.context
        painter = QPainter(self.img)
        painter.setRenderHint(QPainter.Antialiasing)
         
        render = QgsMapRenderer()
        render.setLayerSet([layer.id() for layer in self.rasterlayers])
        
        fout = open("/Users/dewey/Desktop/outputdump.txt", "w")
        for raster in self.rasterlayers:
            fout.write("id: " + raster.id() + "\n")
        fout.close()
        
        render.setExtent(rendererContext.extent())
        render.setOutputSize(self.img.size(), self.img.logicalDpiX())
        render.render(painter)
        painter.end()
        
        self.img.save("/Users/dewey/Desktop/output.jpg")
         
        rendererContext.painter().drawImage(0, 0, self.img)
            
        return True
        
        

class QOSMTileLayer(QgsPluginLayer):
    
    LAYER_TYPE = "QOSM_LAYER_TYPE"
    
    def __init__(self, layerType, layerName):
        QgsPluginLayer.__init__(self, QOSMTileLayer.LAYER_TYPE, layerName)
        self.dlthread = None
        self.loadedtiles = set()
        self.loadedlayers = {}
        self.setValid(True)
        self.treegroup = QgsProject.instance().layerTreeRoot().addGroup("uniquegroupname")
    
    def refreshtiles(self, canvasextent, canvascrs, widthpx):
        xform = QgsCoordinateTransform(canvascrs,
                                    QgsCoordinateReferenceSystem(4326))
        extll = xform.transform(canvasextent)
        zoom = osm.autozoom(widthpx/(extll.xMaximum()-extll.xMinimum()))
        tiles = osm.tiles(extll.xMinimum(), extll.xMaximum(), 
                          extll.yMinimum(), extll.yMaximum(), zoom)
        
        reg = QgsMapLayerRegistry.instance()
        
        tilestoclean = self.loadedtiles.difference(set(tiles))
        for tile in tilestoclean:
            layer = self.loadedlayers[tile]
            reg.removeMapLayer(layer)
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
                layer = QgsRasterLayer(tilefiles[i], "dummyname")
                if layer.isValid():
                    layer = reg.addMapLayer(layer, False)
                    self.loadedlayers[tilestoload[i]] = layer
                    self.loadedtiles.add(tilestoload[i])
                
            else:
                #report error?
                pass
        
        self.setExtent(canvasextent)
    
    def createMapRenderer(self, context):
        return MultiRasterRenderer(self, context, self.loadedlayers.values())
        
        
        