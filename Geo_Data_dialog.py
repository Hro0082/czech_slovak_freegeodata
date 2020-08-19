# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeoDataDialog
                                 A QGIS plugin
 This plugin gathers cz/sk data sources.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2020-08-04
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Test
        email                : test
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

import os
import configparser
import sys

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt import QtGui
from qgis.utils import iface
from qgis.core import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Geo_Data_dialog_base.ui'))


class GeoDataDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(GeoDataDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.pushbutton_print.clicked.connect(self.load_data_sources)
        self.pushbutton_test.clicked.connect(self.load_wms)
        self.data_sources = []

    def load_data_sources(self):
        current_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        sources_dir = os.path.join(current_dir, 'data_sources')

        paths = []

        for name in os.listdir(sources_dir):
            if os.path.isdir(os.path.join(sources_dir, name)):
                paths.append(name)

        config = configparser.ConfigParser()

        index = 0
        for path in paths:
            config.read(os.path.join(sources_dir, path, 'metadata.ini'))
            # print(config.sections())
            # for key in config['gdal']:
            #     print(key)
            # print(config['gdal']['source_file'])
            self.add_item_to_list(config['ui']['alias'], index)
            # TODO check type of sources then add adequate prefix or parameters
            self.data_sources.append(
                {
                    "alias": config['ui']['alias'],
                    "url": "type=xyz&url=" + config['tms']['url']
                }
            )
            index += 1
            # self.wms_sources.append(config['gdal']['url=http://kaart.maaamet.ee/wms/alus&format=image/png&layers=MA-ALUS&styles=&crs=EPSG:3301'])

    def add_item_to_list(self, label, index):
        itemN = QtWidgets.QListWidgetItem()
        widget = QtWidgets.QWidget()
        widgetText = QtWidgets.QLabel(label)
        widgetButton = QtWidgets.QPushButton("Add Layer")
        widgetButton.clicked.connect(lambda: self.add_layer(index))
        widgetLayout = QtWidgets.QHBoxLayout()
        widgetLayout.addWidget(widgetText)
        widgetLayout.addWidget(widgetButton)
        widgetLayout.addStretch()
        widgetLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        widget.setLayout(widgetLayout)
        itemN.setSizeHint(widget.sizeHint())
        widget.show()
        # Add widget to QListWidget funList
        self.listWidget.addItem(itemN)
        self.listWidget.setItemWidget(itemN, widget)

    def add_layer(self, index):
        # print("Add Layer " + (self.wms_sources[index]))
        # rlayer = QgsRasterLayer(self.wms_sources[index], 'MA-ALUS', 'wms')
        layer = QgsRasterLayer(self.data_sources[index]['url'], self.data_sources[index]['alias'], 'wms')
        # TODO check if the layer is valid
        QgsProject.instance().addMapLayer(layer)

    def load_wms(self):
        urlWithParams = 'url=http://kaart.maaamet.ee/wms/alus&format=image/png&layers=MA-ALUS&styles=&crs=EPSG:3301'
        rlayer = QgsRasterLayer(urlWithParams, 'MA-ALUS', 'wms')
        QgsProject.instance().addMapLayer(rlayer)

    # add MapTiler Collection to Browser
    def initGui(self):
        self.dip = DataItemProvider()
        QgsApplication.instance().dataItemProviderRegistry().addProvider(self.dip)

        self._activate_copyrights

    def addToBrowser(self):
        # Sources
        sources = []
        sources.append(["connections-xyz", "Google Maps", "", "", "", "https://mt1.google.com/vt/lyrs=m&x=%7Bx%7D&y=%7By%7D&z=%7Bz%7D", "", "19", "0"])
        sources.append(["connections-xyz", "Stamen Terrain", "", "", "Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL",
                        "http://tile.stamen.com/terrain/%7Bz%7D/%7Bx%7D/%7By%7D.png", "", "20", "0"])

        # Add sources to browser
        for source in sources:
            connectionType = source[0]
            connectionName = source[1]
            QSettings().setValue("qgis/%s/%s/authcfg" % (connectionType, connectionName), source[2])
            QSettings().setValue("qgis/%s/%s/password" % (connectionType, connectionName), source[3])
            QSettings().setValue("qgis/%s/%s/referer" % (connectionType, connectionName), source[4])
            QSettings().setValue("qgis/%s/%s/url" % (connectionType, connectionName), source[5])
            QSettings().setValue("qgis/%s/%s/username" % (connectionType, connectionName), source[6])
            QSettings().setValue("qgis/%s/%s/zmax" % (connectionType, connectionName), source[7])
            QSettings().setValue("qgis/%s/%s/zmin" % (connectionType, connectionName), source[8])

        # Update GUI
        iface.reloadConnections()
