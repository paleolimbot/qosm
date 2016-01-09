# -*- coding: utf-8 -*-
"""
/***************************************************************************
 qosmDialog
                                 A QGIS plugin
 Open Street Map tiles in QGIS
                             -------------------
        begin                : 2015-12-08
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Dewey Dunnington / Fish & Whistle
        email                : dewey@fishandwhistle.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import QgsMapLayerRegistry

import tilemanagement as tm
import qosmsettings

from ui_qosm_dialog_base import Ui_qosmDialogBase
from dialog_cachetiles import DialogCachetiles

class QosmDialog(QDialog, Ui_qosmDialogBase):
    
    def __init__(self, iface):
        """Constructor."""
        super(QosmDialog, self).__init__(None)
        self.setupUi(self)
        self.refresh_types()
        self.newlayer = False
        
        self.cachedialog = DialogCachetiles(self, iface)
    
    def on_downloadTileCache_released(self):
        current = self.maptypeSpinner.itemData(self.maptypeSpinner.currentIndex())
        self.cachedialog.set_tiletype(current)
        self.cachedialog.set_extent()
        self.cachedialog.autoset_minmax()
        self.cachedialog.show()
    
    def on_addCustomType_released(self):
        #validate url
        urlpattern = unicode(self.customUrl.text())
        if self.valid_urlpattern(urlpattern):
            urlpattern = urlpattern.strip()
            currenttype = self.get_type(urlpattern)
            if not currenttype is None:
                self.set_selected_type(currenttype)
                self.customUrl.setText("")
                self.customUrl.clearFocus()
            else:
                #ask for name
                name, ok = QInputDialog.getText(self, "Enter name", "Enter name for custom tile type:")
                if ok:
                    name = name.strip()
                    if len(name) > 0:
                        self.add_custom_type(urlpattern, name)
                        self.refresh_types()
                        self.set_selected_type(urlpattern)
        else:
            QMessageBox.information(self, "QOSM Error", 
                "Invalid URL pattern (must contain ${x}, ${y} and ${z} or ${quadkey}")
    
    def valid_urlpattern(self, urlpattern):
        return ("://" in urlpattern) and \
            ((("${x}" in urlpattern) and 
              ("${y}" in urlpattern) and 
              ("${z}" in urlpattern)) or ("${quadkey}" in urlpattern))
    
    def add_custom_type(self, urlpattern, label):
        customtypes = qosmsettings.get(qosmsettings.CUSTOM_TILE_TYPES)
        customtypes[urlpattern] = label
        qosmsettings.put(qosmsettings.CUSTOM_TILE_TYPES, customtypes)
        
        self.customUrl.setText("")
        self.customUrl.clearFocus()
    
    def refresh_types(self):
        self.maptypeSpinner.clear()
        
        i = 0
        for tiletype, label in tm.BUILT_IN_LABELS.items():
            self.maptypeSpinner.insertItem(i, label)
            self.maptypeSpinner.setItemData(i, tiletype)
            i += 1
        
        self.maptypeSpinner.insertSeparator(i)
        i += 1
        customtypes = qosmsettings.get(qosmsettings.CUSTOM_TILE_TYPES)
        for tiletype, label in customtypes.items():
            self.maptypeSpinner.insertItem(i, label)
            self.maptypeSpinner.setItemData(i, tiletype)
            i += 1
    
    def get_type(self, urlpattern):
        customtypes = qosmsettings.get(qosmsettings.CUSTOM_TILE_TYPES)
        if urlpattern in customtypes:
            return urlpattern
        else:
            for tiletype, urllist in tm.BUILT_IN_TILETYPES.items():
                for url in urllist:
                    if urlpattern == url:
                        return tiletype
        return None
            
    
    def set_selected_type(self, setselection):
        if not setselection is None:
            index = self.maptypeSpinner.findData(setselection)
            if index != -1:
                self.maptypeSpinner.setCurrentIndex(index)
    
    def reset_defaults(self):
        self.set_selected_type("osm") #change to qosmsettings saved value
        self.customUrl.setText("")
        self.autorefresh.setChecked(True)
    
    def set_layer(self, layer, applyvalues=True):
        self.layer = layer
        if applyvalues:
            self.autorefresh.setChecked(layer.autorefresh)
            self.set_selected_type(layer.tiletype)
            self.customUrl.setText("")
            
            if not self.layer.specifiedzoom is None:
                self.fixedZoom.setValue(self.layer.specifiedzoom)
                self.hasFixedZoom.setChecked(True)
            else:
                if self.layer.actualzoom is None:
                    self.fixedZoom.setValue(tm.maxzoom(self.layer.tiletype))
                else:
                    self.fixedZoom.setValue(self.layer.actualzoom)
                    
            if not self.layer.maxzoom is None:
                self.maxZoom.setValue(self.layer.maxzoom)
                self.hasMaxZoom.setChecked(True)
            else:
                self.maxZoom.setValue(tm.maxzoom(self.layer.tiletype))
                
            
    
    def get_label(self, tiletype):
        if tiletype in tm.BUILT_IN_LABELS:
            return tm.BUILT_IN_LABELS[tiletype]
        else:
            customtypes = qosmsettings.get(qosmsettings.CUSTOM_TILE_TYPES)
            if tiletype in customtypes:
                return customtypes[tiletype]
            else:
                return str(tiletype) # in case None is passed
        
        
    def accept(self):
        #apply values to layer object
        if self.layer.autorefresh != self.autorefresh.isChecked():
            self.layer.autorefresh = self.autorefresh.isChecked()
            
        tiletypevalue = self.maptypeSpinner.itemData(self.maptypeSpinner.currentIndex())
        if self.newlayer:
            self.layer.setLayerName("QOSM layer - " + self.get_label(tiletypevalue))
        if tiletypevalue != self.layer.tiletype:
            #rename any part of the layer that was named according to the tiletype
            layername = unicode(self.layer.name())
            layername = layername.replace(self.get_label(self.layer.tiletype), 
                       self.get_label(tiletypevalue))
            self.layer.setLayerName(layername)
            #set new tiletype and clean old tiles
            self.layer.tiletype = tiletypevalue
            self.layer.cleantiles()
        if self.hasFixedZoom.isChecked():
            self.layer.specifiedzoom = self.fixedZoom.value()
        else:
            self.layer.specifiedzoom = None

        if self.hasMaxZoom.isChecked():
            self.layer.maxzoom = self.maxZoom.value()
        else:
            self.layer.maxzoom = None
        
        self.layer.triggerRepaint()
        self.newlayer = False
        QDialog.accept(self)
    
    def reject(self):
        if self.newlayer:
            layerid = self.layer.id()
            QgsMapLayerRegistry.instance().removeMapLayer(layerid)
        self.newlayer = False
        QDialog.reject(self)
        
            
