# -*- coding: utf-8 -*-
"""
/***************************************************************************
 qosm
                                 A QGIS plugin
 Open Street Map tiles in QGIS
                             -------------------
        begin                : 2015-12-08
        copyright            : (C) 2015 by Dewey Dunnington / Fish & Whistle
        email                : dewey@fishandwhistle.net
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load qosm class from file qosm.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from qosmpy.qosm import qosm
    return qosm(iface)
