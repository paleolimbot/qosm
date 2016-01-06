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

class QosmDialog(QDialog, Ui_qosmDialogBase):
    
    def __init__(self, parent=None, deleteoncancel=False):
        """Constructor."""
        super(QosmDialog, self).__init__(parent)
        self.setupUi(self)
        self.refresh_types()
        self.deleteoncancel = deleteoncancel
    
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
        #may wish to check to see if selected type exists and add it
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
        
    def accept(self):
        #apply values to layer object
        if self.layer.autorefresh != self.autorefresh.isChecked():
            self.layer.autorefresh = self.autorefresh.isChecked()
            
        tiletypevalue = self.maptypeSpinner.itemData(self.maptypeSpinner.currentIndex())
        if tiletypevalue != self.layer.tiletype:
            self.layer.tiletype = tiletypevalue
            self.layer.cleantiles()
        
        self.layer.triggerRepaint()
        self.deleteoncancel = False
        QDialog.accept(self)
    
    def reject(self):
        if self.deleteoncancel:
            layerid = self.layer.id()
            QgsMapLayerRegistry.instance().removeMapLayer(layerid)
        self.deleteoncancel = False
        QDialog.reject(self)
        
            
