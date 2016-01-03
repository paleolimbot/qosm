'''
Created on Dec 30, 2015

@author: dewey
'''

import os, sys

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

class MtrExampleController(QObject):
    """
    Helper class that deals with QWebPage.
    The object lives in GUI thread, its request() slot is asynchronously called from worker thread.
    """

    # signal that reports to the worker thread that the image is ready
    finished = pyqtSignal()

    def __init__(self, parent, baselayer, context):
        QObject.__init__(self, parent)

        self.extent = context.extent()
        self.crs = context.coordinateTransform().destCRS()
        self.layerids = [layer.id() for layer in baselayer.loadedlayers.values()]
        self.img = QImage(QSize(self.context.painter().device().width(),
                                    self.context.painter().device().height()),
                              QImage.Format_ARGB32_Premultiplied)


    @pyqtSlot()
    def request(self):
        sys.stderr.write("[GUI THREAD] Processing request\n")
        self.cancelled = False
        #url = QUrl("http://qgis.org/")
        url = QUrl(os.path.join(os.path.dirname(__file__), "testpage.html"))
        self.page.mainFrame().load(url)

    def pageFinished(self):
        sys.stderr.write("[GUI THREAD] Request finished\n")
        if not self.cancelled:
            painter = QPainter(self.img)
            self.page.mainFrame().render(painter)
            painter.end()
        else:
            self.img.fill(Qt.gray)

        self.finished.emit()



class MultiRasterRenderer(QgsMapLayerRenderer):
    
    def __init__(self, layer, context):
        QgsMapLayerRenderer.__init__(self, layer.id())
        self.layer = layer
        self.context = context
    
    def render(self):
        fout = open("/Users/dewey/Desktop/outputdump.txt", "w")
        rendererContext = self.context
        if len(self.layer.loadedlayers) > 0:
            img = QImage(QSize(self.context.painter().device().width(),
                                    self.context.painter().device().height()),
                              QImage.Format_ARGB32_Premultiplied)
            painter = QPainter()
            painter.begin(img)
            painter.setRenderHint(QPainter.Antialiasing)
             
            render = QgsMapRenderer()
            render.setLayerSet([layer.id() for layer in self.layer.loadedlayers.values()])
            render.setProjectionsEnabled(True)
            render.setDestinationCrs(rendererContext.coordinateTransform().destCRS())
            
            
            fout.write("Context extent: " + rendererContext.extent().toString() + "\n")
            
            
            if render.setExtent(rendererContext.extent()):
                render.setOutputSize(img.size(), img.logicalDpiX())
                render.render(painter)
                painter.end()
                
                img.save("/Users/dewey/Desktop/output.jpg")
                 
                rendererContext.painter().drawImage(0, 0, img)
                
                fout.write("Render extent: " + render.extent().toString() + "\n")
            else:
                fout.write("render.setExtent() returned false\n")
        else:
            fout.write("No tiles to load, skipping rendering")
                
        fout.close()
        return True
        
        

class QOSMTileLayer(QgsPluginLayer):
    
    LAYER_TYPE = "QOSM_LAYER_TYPE"
    
    def __init__(self, layertype, layerName):
        QgsPluginLayer.__init__(self, QOSMTileLayer.LAYER_TYPE, layerName)
        self.layertype = layertype
        self.loadedtiles = set()
        self.loadedlayers = {}
        self.setValid(True)
    
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
    
        
        
        