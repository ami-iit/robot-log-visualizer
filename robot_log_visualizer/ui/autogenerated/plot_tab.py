# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'robot_log_visualizer/ui/misc/plot_tab.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


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
