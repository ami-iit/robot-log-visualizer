# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'robot_log_visualizer/ui/misc/plot_tab.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_PlotTab(object):
    def setupUi(self, PlotTab):
        PlotTab.setObjectName("PlotTab")
        PlotTab.resize(331, 149)
        self.horizontalLayout = QtWidgets.QHBoxLayout(PlotTab)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.plotLayout = QtWidgets.QVBoxLayout()
        self.plotLayout.setObjectName("plotLayout")
        self.horizontalLayout.addLayout(self.plotLayout)

        self.retranslateUi(PlotTab)
        QtCore.QMetaObject.connectSlotsByName(PlotTab)

    def retranslateUi(self, PlotTab):
        _translate = QtCore.QCoreApplication.translate
        PlotTab.setWindowTitle(_translate("PlotTab", "Form"))
