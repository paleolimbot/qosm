# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'resources/qosm_cachetiles_dialog.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_qosmDialogCacheTiles(object):
    def setupUi(self, qosmDialogCacheTiles):
        qosmDialogCacheTiles.setObjectName(_fromUtf8("qosmDialogCacheTiles"))
        qosmDialogCacheTiles.resize(336, 219)
        qosmDialogCacheTiles.setModal(True)
        self.verticalLayout = QtGui.QVBoxLayout(qosmDialogCacheTiles)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label_4 = QtGui.QLabel(qosmDialogCacheTiles)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setAlignment(QtCore.Qt.AlignCenter)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.verticalLayout.addWidget(self.label_4)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(qosmDialogCacheTiles)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.maxZoom = QtGui.QSpinBox(qosmDialogCacheTiles)
        self.maxZoom.setMaximum(22)
        self.maxZoom.setObjectName(_fromUtf8("maxZoom"))
        self.gridLayout.addWidget(self.maxZoom, 1, 1, 1, 1)
        self.numtilestext = QtGui.QLabel(qosmDialogCacheTiles)
        self.numtilestext.setObjectName(_fromUtf8("numtilestext"))
        self.gridLayout.addWidget(self.numtilestext, 1, 2, 1, 1)
        self.minZoom = QtGui.QSpinBox(qosmDialogCacheTiles)
        self.minZoom.setMaximum(22)
        self.minZoom.setObjectName(_fromUtf8("minZoom"))
        self.gridLayout.addWidget(self.minZoom, 1, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 2, 1, 1)
        self.label_2 = QtGui.QLabel(qosmDialogCacheTiles)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 0, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.doOverwrite = QtGui.QCheckBox(qosmDialogCacheTiles)
        self.doOverwrite.setObjectName(_fromUtf8("doOverwrite"))
        self.verticalLayout.addWidget(self.doOverwrite)
        self.progressBar = QtGui.QProgressBar(qosmDialogCacheTiles)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.verticalLayout.addWidget(self.progressBar)
        self.statusText = QtGui.QLabel(qosmDialogCacheTiles)
        self.statusText.setObjectName(_fromUtf8("statusText"))
        self.verticalLayout.addWidget(self.statusText)
        spacerItem1 = QtGui.QSpacerItem(20, 1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.button_box = QtGui.QDialogButtonBox(qosmDialogCacheTiles)
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.button_box.setObjectName(_fromUtf8("button_box"))
        self.verticalLayout.addWidget(self.button_box)

        self.retranslateUi(qosmDialogCacheTiles)
        QtCore.QMetaObject.connectSlotsByName(qosmDialogCacheTiles)

    def retranslateUi(self, qosmDialogCacheTiles):
        qosmDialogCacheTiles.setWindowTitle(_translate("qosmDialogCacheTiles", "Cache tiles", None))
        self.label_4.setText(_translate("qosmDialogCacheTiles", "(using current map extent)", None))
        self.label.setText(_translate("qosmDialogCacheTiles", "Min Zoom", None))
        self.numtilestext.setText(_translate("qosmDialogCacheTiles", "1 tile (up to 15 kb)", None))
        self.label_2.setText(_translate("qosmDialogCacheTiles", "Max Zoom", None))
        self.doOverwrite.setText(_translate("qosmDialogCacheTiles", "Overwrite existing tiles", None))
        self.statusText.setText(_translate("qosmDialogCacheTiles", "Ready to download.", None))

