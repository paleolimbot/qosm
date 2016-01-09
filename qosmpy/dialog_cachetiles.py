'''
Created on Jan 9, 2016

@author: dewey
'''

import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import QgsCoordinateTransform, QgsCoordinateReferenceSystem

import qosmsettings
import tilemanagement as tm
import openstreetmap as osm
import downloaderthread as downloader
from qosmlogging import log

from ui_qosm_cachetiles_dialog import Ui_qosmDialogCacheTiles

class DialogCachetiles(QDialog, Ui_qosmDialogCacheTiles):
    
    def __init__(self, parent, iface):
        """Constructor."""
        super(DialogCachetiles, self).__init__(parent)
        self.setupUi(self)
        self.extent = None
        self.tiletype = None
        self.iface = iface
        self.thread = None
        
        self.maxZoom.valueChanged["int"].connect(self.recalculate)
        self.minZoom.valueChanged["int"].connect(self.recalculate)
        
        self.button_box.accepted.connect(self.do_download)
        self.button_box.rejected.connect(self.reject)
    
    def set_extent(self):
        extent = self.iface.mapCanvas().extent()
        crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        xform = QgsCoordinateTransform(crs,
                                    QgsCoordinateReferenceSystem(4326))
        self.extent = xform.transform(extent)
    
    def set_tiletype(self, tiletype):
        self.tiletype = tiletype
    
    def autoset_minmax(self):

        extll = self.extent
        
        minzoom = 1
        while len(tiles(extll, minzoom)) == 1:
            minzoom += 1
        
        maxzoom = minzoom + 1
        while (maxzoom <= 21) and  len(tiles(extll, minzoom, maxzoom)) < 350: #about 10 mb
            maxzoom += 1
        
        self.minZoom.setValue(minzoom)
        self.maxZoom.setValue(maxzoom)
        self.recalculate()
        
    def recalculate(self, arg=None):
        minzoom = self.minZoom.value()
        maxzoom = self.maxZoom.value()
        if maxzoom < minzoom:
            self.maxZoom.setValue(minzoom)
            maxzoom = minzoom
        if minzoom > maxzoom:
            self.minZoom.setValue(maxzoom)
            minzoom = maxzoom
        
        numtiles = len(tiles(self.extent, minzoom, maxzoom))
        mb = 0.015 * numtiles #approximating heavily
        tiletext = "tile" if numtiles == 1 else "tiles"
        self.numtilestext.setText("%s %s (%0.2f MiB)" % (numtiles, tiletext, mb))
    
    def do_download(self):
        if not self.thread is None: #don't start another thread if is already downloading
            return
        self.gridLayout.setEnabled(False)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        
        minzoom = self.minZoom.value()
        maxzoom = self.maxZoom.value()
        tilelist = tiles(self.extent, minzoom, maxzoom)
                
        self.thread = DownloaderThread(self, self.tiletype, tilelist)
        self.thread.finished.connect(self.download_finished)
        self.thread.progress.connect(self.set_progress)
        self.rejected.connect(self.thread.cancel)
        
        log("Starting thread")
        self.thread.start()
    
    @pyqtSlot(int, int)
    def set_progress(self, progress, maximum):
        self.progressBar.setMaximum(maximum)
        self.progressBar.setValue(progress)
    
    def download_finished(self):
        log("Thread finished")
        self.thread.finished.disconnect(self.download_finished)
        self.thread.progress.disconnect(self.set_progress)
        self.rejected.disconnect(self.thread.cancel)
                
        self.gridLayout.setEnabled(True)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
        self.set_progress(0, 100)
        
        if not self.thread.cancelled:
            self.thread = None
            self.accept()
        else:
            self.thread = None

class DownloaderThread(QThread):
    
    progress = pyqtSignal(int, int)
    
    def __init__(self, parent, tiletype, tilelist):
        super(DownloaderThread, self).__init__(parent)
        self.tiletype = tiletype
        self.tilelist = tilelist
        self.cancelled = False
    
    def isCancelled(self):
        return self.cancelled
    
    @pyqtSlot()
    def cancel(self):
        self.cancelled = True
        
    def run(self):
        log("ensuring %s tiles are loaded" % len(self.tilelist))
        cachedir = qosmsettings.get(qosmsettings.CACHE_DIRECTORY)
        tilefiles = [tm.filename(cachedir, self.tiletype, tile[0:2], tile[2]) for tile in self.tilelist]
        tileurls = [tm.tileurl(self.tiletype, tile[0:2], tile[2]) for tile in self.tilelist]
        
        #remove existing files
        indicies = []
        for i in range(len(tilefiles)):
            if os.path.exists(tilefiles[i]):
                indicies.append(i)
        log("removing %s tiles that already exist" % len(indicies))
        for i in indicies:
            tilefiles.pop(i)
            tileurls.pop(i)
        
        downloader.download(tileurls, tilefiles, errorhandler=log, progresshandler=self.emitprogress,
                            cancelledcallback=self.isCancelled)
        
    def emitprogress(self, value, maximum):
        self.progress.emit(value, maximum)
    

def tiles(extll, minzoom, maxzoom=None):
    if maxzoom is None:
        maxzoom = minzoom
    alltiles = []
    for zoom in range(minzoom, maxzoom+1):
        alltiles = alltiles + osm.tiles(extll.xMinimum(), extll.xMaximum(), 
              extll.yMinimum(), extll.yMaximum(), zoom)
    return alltiles