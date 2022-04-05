# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'robot_log_visualizer/ui/misc/about.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_aboutWindow(object):
    def setupUi(self, aboutWindow):
        aboutWindow.setObjectName("aboutWindow")
        aboutWindow.resize(541, 102)
        aboutWindow.setMaximumSize(QtCore.QSize(541, 102))
        self.centralwidget = QtWidgets.QWidget(aboutWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setEnabled(True)
        self.label_2.setOpenExternalLinks(True)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        aboutWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(aboutWindow)
        QtCore.QMetaObject.connectSlotsByName(aboutWindow)

    def retranslateUi(self, aboutWindow):
        _translate = QtCore.QCoreApplication.translate
        aboutWindow.setWindowTitle(_translate("aboutWindow", "Robot Log Visualizer - About"))
        self.label_2.setText(_translate("aboutWindow", "<html><head/><body><p><span style=\" font-size:14pt; font-weight:600;\">About Robot Log Visualizer</span></p><p><span style=\" font-size:12pt;\">This program is Licensed under the </span><a href=\"https://github.com/ami-iit/robot-log-visualizer/blob/main/LICENSE\"><span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">3-Clause BSD License</span></a></p><p><span style=\" font-size:12pt;\">The project is mantained by the </span><a href=\"https://ami.iit.it/\"><span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">Artificial and Mechanical Intelligence lab</span></a></p></body></html>"))
