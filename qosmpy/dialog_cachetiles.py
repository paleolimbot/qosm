'''
Created on Jan 9, 2016

@author: dewey
'''

import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

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
        self.errors = []
        
        self.maxZoom.valueChanged["int"].connect(self.recalculate)
        self.minZoom.valueChanged["int"].connect(self.recalculate)
        
        self.button_box.accepted.connect(self.do_download)
        self.button_box.rejected.connect(self.reject)
    
    def set_extent(self):
        extent = self.iface.mapCanvas().extent()
        crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        self.extent = osm.unproject(extent, crs)
    
    def set_tiletype(self, tiletype):
        self.tiletype = tiletype
        self.statusText.setText("Ready to download.")
        self.set_progress(0, 100, False)
        self.doOverwrite.setChecked(False)
    
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
                
        self.thread = DownloaderThread(self, self.tiletype, tilelist, self.doOverwrite.isChecked())
        self.thread.finished.connect(self.download_finished)
        self.thread.progress.connect(self.set_progress)
        self.thread.error.connect(self.add_error)
        self.rejected.connect(self.thread.cancel)
        
        log("Starting thread")
        self.thread.start()
    
    @pyqtSlot(int, int)
    def set_progress(self, progress, maximum, updatetext=True):
        self.progressBar.setMaximum(maximum)
        self.progressBar.setValue(progress)
        if updatetext:
            self.statusText.setText("Downloading %s of %s tiles%s" % (progress,
                                                                   maximum, 
                                                                   self.errortext()))
    
    @pyqtSlot(unicode)
    def add_error(self, message):
        self.errors.append(message)
        stext = unicode(self.statusText.text())
        nl = stext.find("\n")
        firstline = stext[:nl+1] if nl != -1 else stext
        self.statusText.setText("%s%s" % (firstline, self.errortext()))    
    
    def errortext(self):
        if self.errors:
            out = "\n%s error(s):\n" % len(self.errors)
            numerrors = min(10, len(self.errors))
            errorstrings = [self.errors[i] for i in range(len(self.errors)-numerrors, len(self.errors))]
            out += "\n".join(errorstrings)
            return out
        else:
            return ""
    
    def download_finished(self):
        log("Thread finished")
        self.thread.finished.disconnect(self.download_finished)
        self.thread.progress.disconnect(self.set_progress)
        self.thread.error.disconnect(self.add_error)
        self.rejected.disconnect(self.thread.cancel)
                
        self.gridLayout.setEnabled(True)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
        haderrors = len(self.errors) != 0
        self.errors = []
        
        self.thread = None
        
        if not haderrors:
            self.statusText.setText("Download complete.")


class DownloaderThread(QThread):
    
    progress = pyqtSignal(int, int)
    error = pyqtSignal(unicode)
    
    def __init__(self, parent, tiletype, tilelist, overwrite):
        super(DownloaderThread, self).__init__(parent)
        self.tiletype = tiletype
        self.tilelist = tilelist
        self.overwrite = overwrite
        self.cancelled = False
    
    def isCancelled(self):
        return self.cancelled
    
    @pyqtSlot()
    def cancel(self):
        self.cancelled = True
        
    def run(self):
        log("ensuring %s tiles are downloaded" % len(self.tilelist))
        cachedir = qosmsettings.get(qosmsettings.CACHE_DIRECTORY)
        tilefiles = [tm.filename(cachedir, self.tiletype, tile[0:2], tile[2]) for tile in self.tilelist]
        tileurls = [tm.tileurl(self.tiletype, tile[0:2], tile[2]) for tile in self.tilelist]
        
        if not self.overwrite:
            #remove existing files
            indicies = []
            for i in range(len(tilefiles)):
                if os.path.exists(tilefiles[i]):
                    indicies.append(i)
            log("removing %s tiles that already exist" % len(indicies))
            for i in reversed(indicies):
                tilefiles.pop(i)
                tileurls.pop(i)
        
        downloader.download(tileurls, tilefiles, self.overwrite, errorhandler=self.emiterror, progresshandler=self.emitprogress,
                            cancelledcallback=self.isCancelled)
        
    def emitprogress(self, value, maximum):
        self.progress.emit(value, maximum)
    
    def emiterror(self, message):
        self.error.emit(message)

def tiles(extll, minzoom, maxzoom=None):
    if maxzoom is None:
        maxzoom = minzoom
    alltiles = []
    for zoom in range(minzoom, maxzoom+1):
        alltiles = alltiles + osm.tiles(extll.xMinimum(), extll.xMaximum(), 
              extll.yMinimum(), extll.yMaximum(), zoom)
    return alltiles