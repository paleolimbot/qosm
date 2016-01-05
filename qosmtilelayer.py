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
from qosm_dialog import QosmDialog


class QOSMTileLayerType(QgsPluginLayerType):

    def __init__(self, plugin, add_callback):
        QgsPluginLayerType.__init__(self, QOSMTileLayer.LAYER_TYPE)
        self.plugin = plugin
        self.add_callback = add_callback
        self.properties = QosmDialog(None)

    def createLayer(self):
        layer = QOSMTileLayer("osm", "OSM Plugin layer")
        self.add_callback(layer)
        return layer   
    
    def showLayerProperties(self, layer, defaults=False):
        self.properties.set_layer(layer)
        if defaults:
            self.properties.reset_defaults()
        self.properties.show()
        return True
          

class QOSMTileLayer(QgsPluginLayer):
    
    LAYER_TYPE = "QOSM_LAYER_TYPE"
    
    def __init__(self, tiletype, layerName):
        QgsPluginLayer.__init__(self, QOSMTileLayer.LAYER_TYPE, layerName)
        self.tiletype = tiletype
        self.loadedtiles = set()
        self.loadedlayers = {}
        self.actualzoom = None
        self.specifiedzoom = None #autozoom
        self.autorefresh = False
        self.refreshonce = False
        self.forcedownload = False
        
        self.setMaximumScale(20000000) #1:20,000,000
        self.setScaleBasedVisibility(True)
        self.setValid(True)
    
    def zoom(self, widthpx, extll):
        if self.specifiedzoom is None:
            autozoom = osm.autozoom(widthpx/(extll.xMaximum()-extll.xMinimum()))
            return min(max((tm.minzoom(self.tiletype), autozoom)),
                       tm.maxzoom(self.tiletype))
        else:
            numtiles = len(osm.tiles(extll.xMinimum(), extll.xMaximum(), 
                          extll.yMinimum(), extll.yMaximum(), self.specifiedzoom))
            if numtiles > qosmsettings.get(qosmsettings.MAX_TILES):
                return None
            else:
                return self.specifiedzoom
            
    
    def cleantiles(self):
        reg = QgsMapLayerRegistry.instance()
        for tile in self.loadedtiles:
            reg.removeMapLayer(self.loadedlayers[tile])
            del self.loadedlayers[tile]
        self.loadedtiles.clear()
    
    def refreshtiles(self, iface=None, rendererContext=None, forcedownload=False):
        if iface is None and rendererContext is None:
            #temporarily turn on self.autorefresh and trigger a repaint
            self.refreshonce = True
            self.forcedownload = forcedownload
            self.triggerRepaint()
        elif iface is None:
            #passing iface means refreshing happens on the main thread for debug
            self.__refreshtiles(rendererContext.extent(), 
                            rendererContext.coordinateTransform().destCRS(),
                            rendererContext.painter().device().width(), forcedownload=forcedownload)
        elif rendererContext is None:
            #should this ever need to be called from a rendererContext
            self.__refreshtiles(iface.mapCanvas().extent(), 
                              iface.mapCanvas().mapRenderer().destinationCrs(), 
                              iface.mapCanvas().width(), forcedownload=forcedownload)
        else:
            raise ValueError("Cannot specify both iface and rendererContext")
    
    def __refreshtiles(self, canvasextent, canvascrs, widthpx, forcedownload=False, triggerrepaint=True):
        tilestoclean, tilestoload, tilefiles = self.refreshtiles_get(canvasextent, canvascrs, widthpx, forcedownload)
        self.refreshtiles_apply(tilestoclean, tilestoload, tilefiles, canvasextent)
        if triggerrepaint:
            self.triggerRepaint()
    
    def refreshtiles_get(self, canvasextent, canvascrs, widthpx, forcedownload=False, cancelledcallback=None, errorhandler=None):
        xform = QgsCoordinateTransform(canvascrs,
                                    QgsCoordinateReferenceSystem(4326))
        extll = xform.transform(canvasextent)
        
        zoom = self.zoom(widthpx, extll)
        if zoom is None or self.tiletype is None:
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
        cachedir = qosmsettings.get(qosmsettings.CACHE_DIRECTORY)
        tilefiles = [tm.filename(cachedir, self.tiletype, tile, zoom) for tile in tilestoload]
        tileurls = [tm.tileurl(self.tiletype, tile, zoom) for tile in tilestoload]
        
        #download (keep on same thread for now)
        if not cancelledcallback:
            cancelledcallback = lambda: False
        downloader.download(tileurls, tilefiles, overwrite=forcedownload, 
                            errorhandler=errorhandler, 
                            cancelledcallback=cancelledcallback)
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
                layername = "qosm_%s_x%s_y%s_z%s" % ((self.tiletype,) + tilestoload[i])
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
        
        refreshonce = self.refreshonce
        forcedownload = self.forcedownload
        self.refreshonce = False
        self.forcedownload = False
        
        if self.autorefresh or refreshonce:
            tilestoclean, tilestoload, tilefiles = self.refreshtiles_get(extent, crs, outputsize.width(), 
                                                                         forcedownload=forcedownload,
                                                                         cancelledcallback=rendererContext.renderingStopped)
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
    
        
        
        