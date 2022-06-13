# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'robot_log_visualizer/ui/misc/video_tab.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_VideoTab(object):
    def setupUi(self, VideoTab):
        VideoTab.setObjectName("VideoTab")
        VideoTab.resize(400, 300)
        self.horizontalLayout = QtWidgets.QHBoxLayout(VideoTab)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.webcamView = QVideoWidget(VideoTab)
        self.webcamView.setObjectName("webcamView")
        self.horizontalLayout.addWidget(self.webcamView)

        self.retranslateUi(VideoTab)
        QtCore.QMetaObject.connectSlotsByName(VideoTab)

    def retranslateUi(self, VideoTab):
        _translate = QtCore.QCoreApplication.translate
        VideoTab.setWindowTitle(_translate("VideoTab", "Form"))
from PyQt5.QtMultimediaWidgets import QVideoWidget
