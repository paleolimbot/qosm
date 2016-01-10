'''
Created on Jan 10, 2016

@author: dewey
'''


import os
import shutil

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import qosmsettings as s
from qosmlogging import log, FILE, PREVIOUS_FILE

from ui_qosm_settings_dialog import Ui_qosmDialogSettings
from PyQt4.Qt import QMessageBox

class DialogSettings(QDialog, Ui_qosmDialogSettings):
    
    def __init__(self, parent):
        """Constructor."""
        super(DialogSettings, self).__init__(parent)
        self.setupUi(self)
        self.customtypes = []
        self.cachesizethread = None
        
        self.button_box.button(QDialogButtonBox.Apply).released.connect(self.apply)
        self.button_box.button(QDialogButtonBox.Reset).released.connect(self.sync_dialog)
        self.button_box.button(QDialogButtonBox.RestoreDefaults).released.connect(self.reset_defaults)
    
    def reset_defaults(self):
        if QMessageBox.Ok == QMessageBox.question(self, "Question", 
                            "Reset original settings? This cannot be undone.",
                                        QMessageBox.Ok | QMessageBox.Cancel):
            s.reset()
            self.sync_dialog()
        
    def sync_dialog(self):
        self.autoDownload.setChecked(s.get(s.AUTODOWNLOAD))
        self.generalMaxTiles.setValue(s.get(s.MAX_TILES))
        self.generalCacheLocation.setText(s.get(s.CACHE_DIRECTORY))
        self.logWhichLog.setCurrentIndex(0)
        self.reload_customtypes()
        self.calculate_cachesize()
        self.on_logWhichLog_currentIndexChanged("Current session")
    
    def on_generalBrowse_released(self):
        dirtext = self.generalCacheLocation.text()
        if (dirtext != s._defaultsetting(s.CACHE_DIRECTORY)) and \
            (os.path.isdir(dirtext)):
            previousDir = dirtext
        else:
            previousDir = unicode(QDir.homePath())
        directory = QFileDialog.getExistingDirectory(self, "Choose Directory",
                                    previousDir)
        if directory:
            self.generalCacheLocation.setText(directory)
        
    
    def on_generalClearCache_released(self):
        QMessageBox.information(self, "fish", "fish")
        if self.generalCacheLocation.text() == s.get(s.CACHE_DIRECTORY):
            if QMessageBox.Ok == QMessageBox.question(self, "Question", 
                                "Clear entire cache directory? This cannot be undone.",
                                            QMessageBox.Ok | QMessageBox.Cancel):
                try:
                    shutil.rmtree(s.get(s.CACHE_DIRECTORY))
                    os.mkdir(s.get(s.CACHE_DIRECTORY))
                    self.calculate_cachesize()
                except Exception as e:
                    log("Error clearing cache directory: %s" % e)
                    QMessageBox.information(self, "Error", "Error cleaning directory: %s" % e)
        else:
            QMessageBox.information(self, "Error", 
                        "Apply changes to cache directory before clearing.")
        
    def reload_customtypes(self):
        customtypes = s.get(s.CUSTOM_TILE_TYPES)
        self.tiletypesList.clear()
        self.customtypes = []
        for pattern, label in customtypes.items():
            self.customtypes.append([pattern, pattern, label])
            self.tiletypesList.addItem(label)
        for i in range(self.tiletypesList.count()):
            item = self.tiletypesList.item(i)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.tiletypesPattern.setText("")
    
    def apply_customtypes(self):
        customtypes = s.get(s.CUSTOM_TILE_TYPES)
        customtypes.clear()
        for originalpattern, pattern, label in self.customtypes:
            if originalpattern != pattern:
                del customtypes[originalpattern]
            customtypes[pattern] = label
        s.put(s.CUSTOM_TILE_TYPES, customtypes)
    
    def on_tiletypesList_itemSelectionChanged(self):
        selectedIndicies = [mi.row() for mi in self.tiletypesList.selectedIndexes()]
        if selectedIndicies and (selectedIndicies[0] < len(self.customtypes)):
            self.tiletypesPattern.setText(self.customtypes[selectedIndicies[0]][1])
            self.tiletypeRemove.setEnabled(True)
        else:
            self.tiletypesPattern.setText("")
            self.tiletypeRemove.setEnabled(False)
        self.tiletypeChange.setEnabled(False)
    
    def on_tiletypesList_itemChanged(self, item):
        row = self.tiletypesList.row(item)
        oldtext = self.customtypes[row][2]
        newtext = unicode(item.text())
        newtext = newtext.strip()
        if oldtext != newtext:
            if len(newtext) == 0:
                item.setText(oldtext)
                QMessageBox.information(self, "QOSM Error", "Invalid name")
                return
            self.customtypes[row][2] = newtext
    
    def on_tiletypesPattern_textChanged(self, newText):
        sellist = [mi.row() for mi in self.tiletypesList.selectedIndexes()]
        if sellist and (sellist[0] < len(self.customtypes)):
            row = sellist[0]
            oldText = self.customtypes[row][1]
            self.tiletypeChange.setEnabled(oldText != newText)
    
    def on_tiletypeChange_released(self):
        urlpattern = unicode(self.tiletypesPattern.text())
        urlpattern = urlpattern.strip()
        if self.valid_urlpattern(urlpattern):
            row = [mi.row() for mi in self.tiletypesList.selectedIndexes()][0]
            self.customtypes[row][1] = urlpattern
            self.tiletypesPattern.clearFocus()
            self.tiletypeChange.setEnabled(False)
        else:
            QMessageBox.information(self, "QOSM Error", 
                "Invalid URL pattern (must contain ${x}, ${y} and ${z} or ${quadkey}")
    
    def valid_urlpattern(self, urlpattern):
        return ("://" in urlpattern) and \
            ((("${x}" in urlpattern) and 
              ("${y}" in urlpattern) and 
              ("${z}" in urlpattern)) or ("${quadkey}" in urlpattern))    
    
    def on_tiletypeRemove_released(self):
        if QMessageBox.Ok == QMessageBox.question(self, "Question", "Really remove from list?",
                                QMessageBox.Ok | QMessageBox.Cancel):
            row = [mi.row() for mi in self.tiletypesList.selectedIndexes()][0]
            del self.customtypes[row]
            self.tiletypesList.takeItem(row)
    
    def on_logWhichLog_currentIndexChanged(self, text):
        if text == "Current session":
            fname = FILE
        elif text == "Previous session":
            fname = PREVIOUS_FILE
        else:
            self.logText.setPlainText("")
            return
        
        try:
            f = open(fname, "r")
            self.logText.setPlainText(f.read())
            f.close()
        except IOError as e:
            log("could not load log into settings dialog: %s" % e)
            self.logText.setPlainText("")
        
    
    def calculate_cachesize(self):
        if self.cachesizethread is None:
            self.generalCacheSize.setText("calculating...")
            cachedir = s.get(s.CACHE_DIRECTORY)
            self.cachesizethread = DirsizeThread(self, cachedir)
            self.cachesizethread.finished.connect(self.cachesize_finished)
            self.cachesizethread.start()
        else:
            log("not starting second cachesize thread")
    
    def cachesize_finished(self):
        self.cachesizethread.finished.disconnect(self.cachesize_finished)
        mb = self.cachesizethread.totalsize / 1048576.0
        self.generalCacheSize.setText("%s tiles (%0.2f MiB)" % (self.cachesizethread.totalfiles, mb))
        self.cachesizethread = None
        
    def apply(self):
        #validate
        newcachedir = unicode(self.generalCacheLocation.text())
        newcachedir = newcachedir.strip()
        if newcachedir.endswith(os.path.sep):
            newcachedir = newcachedir[:-1]
        if not os.path.isdir(newcachedir):
            QMessageBox.information(self, "QOSM Error", 
                "'%s' is not a directory" % newcachedir)
            return False
        if (not len(os.listdir(newcachedir)) == 0) and \
           ((newcachedir != s._defaultsetting(s.CACHE_DIRECTORY)) and
            (newcachedir != s.get(s.CACHE_DIRECTORY))):
            if QMessageBox.Ok != QMessageBox.question(self, "Question", 
                                        "Use non-emtpy directory for cache?",
                                        QMessageBox.Ok | QMessageBox.Cancel):
                return False
        
        if newcachedir == s._defaultsetting(s.CACHE_DIRECTORY):
            s.reset(s.CACHE_DIRECTORY)
            self.generalCacheLocation.setText(s.get(s.CACHE_DIRECTORY))
        else:
            s.put(s.CACHE_DIRECTORY, newcachedir)
            self.generalCacheLocation.setText(newcachedir)
        
        if self.generalMaxTiles.value() == s._defaultsetting(s.MAX_TILES):
            s.reset(s.MAX_TILES)
        else:
            s.put(s.MAX_TILES, self.generalMaxTiles.value())
        s.put(s.AUTODOWNLOAD, self.autoDownload.isChecked())
        self.apply_customtypes()
        
        self.calculate_cachesize()
        return True
    
    def accept(self):
        if self.apply():
            QDialog.accept(self)

class DirsizeThread(QThread):
    
    def __init__(self, parent, cachedir):
        super(DirsizeThread, self).__init__(parent)   
        self.cachedir = cachedir
    
    def run(self):
        totalsize = 0
        totalfiles = 0
        for root, dirs, files in os.walk(self.cachedir):
            for fname in files:
                totalsize += os.path.getsize(os.path.join(root, fname))
                if not fname.endswith(".aux.xml"):
                    totalfiles += 1
        self.totalsize = totalsize
        self.totalfiles = totalfiles