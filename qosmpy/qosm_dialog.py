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

from qgis.core import QgsMapLayerRegistry, QgsCoordinateTransform, \
                     QgsCoordinateReferenceSystem, QgsRectangle
from qgis.gui import QgsMessageBar

import tilemanagement as tm
import qosmsettings
import openstreetmap as osm

from ui_qosm_dialog_base import Ui_qosmDialogBase
from dialog_cachetiles import DialogCachetiles

class QosmDialog(QDialog, Ui_qosmDialogBase):
    
    def __init__(self, iface):
        """Constructor."""
        super(QosmDialog, self).__init__(None)
        self.setupUi(self)
        self.refresh_types()
        self.newlayer = False
        self.iface = iface
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
            
            self.set_summarystats()
        else:
            self.statusText.setText("")
         
    def set_summarystats(self):   
        numtiles = len(self.layer.loadedlayers)
        zoom = self.layer.actualzoom if self.layer.specifiedzoom is None else \
                self.layer.specifiedzoom
        
        extent = self.iface.mapCanvas().extent() 
        crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        widthpx = self.iface.mapCanvas().width()
        xform = QgsCoordinateTransform(crs,
                                    QgsCoordinateReferenceSystem(4326))
        extll = xform.transform(extent)
        
        calczoom = osm.autozoom(widthpx/(extll.xMaximum()-extll.xMinimum()))
        layerzoom = calczoom if zoom is None else zoom
        numtilestot = len(osm.tiles(extll.xMinimum(), extll.xMaximum(), 
                      extll.yMinimum(), extll.yMaximum(), layerzoom))
        
        self.statusText.setText("Loaded %s of %s tiles at zoom level %s (automatic zoom would be %s). \
                                %s rendering errors (see QOSM Settings/Logs for more details)." %
                                (numtiles, numtilestot, zoom, calczoom, self.layer.rendererrors))
    
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
        #check environment to make sure this will work
        if not self.iface.mapCanvas().mapRenderer().destinationCrs().isValid():
            if len(QgsMapLayerRegistry.instance().mapLayers()) > 1:
                self.iface.messageBar().pushMessage("Error", "You need to set a project CRS for QOSM to work!", 
                                                level=QgsMessageBar.CRITICAL)
                self.reject()
            else:
                #this is the only layer.
                self.iface.mapCanvas().mapRenderer().setProjectionsEnabled(True) # Enable on the fly reprojections
                self.iface.mapCanvas().mapRenderer().setDestinationCrs(QgsCoordinateReferenceSystem(3857)) #best for osm
                
                #zoom to USA
                usa = QgsRectangle(-124.39, 25.82, -66.94, 49.38)
                xform = QgsCoordinateTransform(QgsCoordinateReferenceSystem(4326),
                                               QgsCoordinateReferenceSystem(3857))
                usa = xform.transform(usa)
                self.iface.mapCanvas().setExtent(usa)
        
        #apply values to layer object
        if self.layer.autorefresh != self.autorefresh.isChecked():
            self.layer.set_autorefresh(self.autorefresh.isChecked())
            
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
            self.layer.set_tiletype(tiletypevalue)
            self.layer.cleantiles()
        if self.hasFixedZoom.isChecked():
            self.layer.set_fixedzoom(self.fixedZoom.value())
        else:
            self.layer.set_fixedzoom(None)

        if self.hasMaxZoom.isChecked():
            self.layer.set_maxzoom(self.maxZoom.value())
        else:
            self.layer.set_maxzoom(None)
        
        self.layer.triggerRepaint()
        self.newlayer = False
        QDialog.accept(self)
    
    def reject(self):
        if self.newlayer:
            layerid = self.layer.id()
            QgsMapLayerRegistry.instance().removeMapLayer(layerid)
        self.newlayer = False
        QDialog.reject(self)
        
            
