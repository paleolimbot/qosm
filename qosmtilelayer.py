'''
Created on Dec 30, 2015

@author: dewey
'''

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

def currentlatlonextents(iface):
    extent = iface.mapCanvas().extent()
    xform = QgsCoordinateTransform(iface.mapCanvas().mapRenderer().destinationCrs(),
                                    QgsCoordinateReferenceSystem(4326))
    return xform.transform(extent)