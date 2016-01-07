# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'resources/qosm_dialog_base.ui'
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

class Ui_qosmDialogBase(object):
    def setupUi(self, qosmDialogBase):
        qosmDialogBase.setObjectName(_fromUtf8("qosmDialogBase"))
        qosmDialogBase.resize(495, 180)
        qosmDialogBase.setModal(True)
        self.verticalLayout = QtGui.QVBoxLayout(qosmDialogBase)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label = QtGui.QLabel(qosmDialogBase)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.maptypeSpinner = QtGui.QComboBox(qosmDialogBase)
        self.maptypeSpinner.setObjectName(_fromUtf8("maptypeSpinner"))
        self.horizontalLayout.addWidget(self.maptypeSpinner)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.customUrl = QtGui.QLineEdit(qosmDialogBase)
        self.customUrl.setObjectName(_fromUtf8("customUrl"))
        self.horizontalLayout_2.addWidget(self.customUrl)
        self.addCustomType = QtGui.QPushButton(qosmDialogBase)
        self.addCustomType.setObjectName(_fromUtf8("addCustomType"))
        self.horizontalLayout_2.addWidget(self.addCustomType)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.autorefresh = QtGui.QCheckBox(qosmDialogBase)
        self.autorefresh.setChecked(True)
        self.autorefresh.setObjectName(_fromUtf8("autorefresh"))
        self.horizontalLayout_3.addWidget(self.autorefresh)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        spacerItem1 = QtGui.QSpacerItem(20, 1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.button_box = QtGui.QDialogButtonBox(qosmDialogBase)
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.button_box.setObjectName(_fromUtf8("button_box"))
        self.verticalLayout.addWidget(self.button_box)

        self.retranslateUi(qosmDialogBase)
        QtCore.QObject.connect(self.button_box, QtCore.SIGNAL(_fromUtf8("accepted()")), qosmDialogBase.accept)
        QtCore.QObject.connect(self.button_box, QtCore.SIGNAL(_fromUtf8("rejected()")), qosmDialogBase.reject)
        QtCore.QMetaObject.connectSlotsByName(qosmDialogBase)

    def retranslateUi(self, qosmDialogBase):
        qosmDialogBase.setWindowTitle(_translate("qosmDialogBase", "QOSM Layer Properties", None))
        self.label.setText(_translate("qosmDialogBase", "Select map type:", None))
        self.customUrl.setPlaceholderText(_translate("qosmDialogBase", "http://a.tile.opencyclemap.org/cycle/${z}/${x}/${y}.png", None))
        self.addCustomType.setText(_translate("qosmDialogBase", "Add Custom Type", None))
        self.autorefresh.setText(_translate("qosmDialogBase", "Auto refresh map when extent changes", None))

