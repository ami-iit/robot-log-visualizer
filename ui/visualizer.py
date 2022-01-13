# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/visualizer.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1678, 983)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.vertSplitter = QtWidgets.QSplitter(self.centralwidget)
        self.vertSplitter.setOrientation(QtCore.Qt.Vertical)
        self.vertSplitter.setChildrenCollapsible(False)
        self.vertSplitter.setObjectName("vertSplitter")
        self.dataVisualizationGroupBox = QtWidgets.QGroupBox(self.vertSplitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(2)
        sizePolicy.setHeightForWidth(self.dataVisualizationGroupBox.sizePolicy().hasHeightForWidth())
        self.dataVisualizationGroupBox.setSizePolicy(sizePolicy)
        self.dataVisualizationGroupBox.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.dataVisualizationGroupBox.setObjectName("dataVisualizationGroupBox")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.dataVisualizationGroupBox)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.horizSplitter = QtWidgets.QSplitter(self.dataVisualizationGroupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.horizSplitter.sizePolicy().hasHeightForWidth())
        self.horizSplitter.setSizePolicy(sizePolicy)
        self.horizSplitter.setOrientation(QtCore.Qt.Horizontal)
        self.horizSplitter.setChildrenCollapsible(False)
        self.horizSplitter.setObjectName("horizSplitter")
        self.variableTreeWidget = QtWidgets.QTreeWidget(self.horizSplitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.variableTreeWidget.sizePolicy().hasHeightForWidth())
        self.variableTreeWidget.setSizePolicy(sizePolicy)
        self.variableTreeWidget.setMinimumSize(QtCore.QSize(361, 500))
        self.variableTreeWidget.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.variableTreeWidget.setSizeIncrement(QtCore.QSize(0, 0))
        self.variableTreeWidget.setBaseSize(QtCore.QSize(0, 0))
        self.variableTreeWidget.setFrameShape(QtWidgets.QFrame.Box)
        self.variableTreeWidget.setObjectName("variableTreeWidget")
        self.plotGroupBox = QtWidgets.QGroupBox(self.horizSplitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plotGroupBox.sizePolicy().hasHeightForWidth())
        self.plotGroupBox.setSizePolicy(sizePolicy)
        self.plotGroupBox.setMinimumSize(QtCore.QSize(900, 500))
        self.plotGroupBox.setSizeIncrement(QtCore.QSize(0, 0))
        self.plotGroupBox.setBaseSize(QtCore.QSize(100, 0))
        self.plotGroupBox.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.plotGroupBox.setMouseTracking(False)
        self.plotGroupBox.setTabletTracking(False)
        self.plotGroupBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.plotGroupBox.setAcceptDrops(True)
        self.plotGroupBox.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.plotGroupBox.setObjectName("plotGroupBox")
        self.plotBoxLayout = QtWidgets.QGridLayout(self.plotGroupBox)
        self.plotBoxLayout.setObjectName("plotBoxLayout")
        self.meshcatView = QtWebEngineWidgets.QWebEngineView(self.horizSplitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.meshcatView.sizePolicy().hasHeightForWidth())
        self.meshcatView.setSizePolicy(sizePolicy)
        self.meshcatView.setMinimumSize(QtCore.QSize(367, 500))
        self.meshcatView.setObjectName("meshcatView")
        self.gridLayout_3.addWidget(self.horizSplitter, 0, 0, 1, 1)
        self.timeGroupBox = QtWidgets.QGroupBox(self.vertSplitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.timeGroupBox.sizePolicy().hasHeightForWidth())
        self.timeGroupBox.setSizePolicy(sizePolicy)
        self.timeGroupBox.setMinimumSize(QtCore.QSize(0, 70))
        self.timeGroupBox.setMaximumSize(QtCore.QSize(16777215, 50))
        self.timeGroupBox.setObjectName("timeGroupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.timeGroupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.pauseButton = QtWidgets.QPushButton(self.timeGroupBox)
        self.pauseButton.setEnabled(False)
        self.pauseButton.setMaximumSize(QtCore.QSize(40, 16777215))
        self.pauseButton.setText("")
        icon = QtGui.QIcon.fromTheme("media-playback-pause")
        self.pauseButton.setIcon(icon)
        self.pauseButton.setCheckable(False)
        self.pauseButton.setDefault(False)
        self.pauseButton.setFlat(False)
        self.pauseButton.setObjectName("pauseButton")
        self.gridLayout.addWidget(self.pauseButton, 0, 6, 1, 1)
        self.timeLabel = QtWidgets.QLabel(self.timeGroupBox)
        self.timeLabel.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.timeLabel.sizePolicy().hasHeightForWidth())
        self.timeLabel.setSizePolicy(sizePolicy)
        self.timeLabel.setObjectName("timeLabel")
        self.gridLayout.addWidget(self.timeLabel, 0, 0, 1, 1)
        self.startButton = QtWidgets.QPushButton(self.timeGroupBox)
        self.startButton.setEnabled(False)
        self.startButton.setMaximumSize(QtCore.QSize(40, 16777215))
        self.startButton.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.startButton.setText("")
        icon = QtGui.QIcon.fromTheme("media-playback-start")
        self.startButton.setIcon(icon)
        self.startButton.setObjectName("startButton")
        self.gridLayout.addWidget(self.startButton, 0, 5, 1, 1)
        self.timeSlider = QtWidgets.QSlider(self.timeGroupBox)
        self.timeSlider.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.timeSlider.sizePolicy().hasHeightForWidth())
        self.timeSlider.setSizePolicy(sizePolicy)
        self.timeSlider.setSingleStep(1)
        self.timeSlider.setPageStep(1)
        self.timeSlider.setProperty("value", 0)
        self.timeSlider.setTracking(True)
        self.timeSlider.setOrientation(QtCore.Qt.Horizontal)
        self.timeSlider.setTickPosition(QtWidgets.QSlider.TicksAbove)
        self.timeSlider.setTickInterval(1)
        self.timeSlider.setObjectName("timeSlider")
        self.gridLayout.addWidget(self.timeSlider, 0, 1, 1, 1)
        self.logGroupBox = QtWidgets.QGroupBox(self.vertSplitter)
        self.logGroupBox.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.logGroupBox.sizePolicy().hasHeightForWidth())
        self.logGroupBox.setSizePolicy(sizePolicy)
        self.logGroupBox.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.logGroupBox.setObjectName("logGroupBox")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.logGroupBox)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.logScrollArea = QtWidgets.QScrollArea(self.logGroupBox)
        self.logScrollArea.setMinimumSize(QtCore.QSize(0, 170))
        self.logScrollArea.setStyleSheet("background: white")
        self.logScrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.logScrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.logScrollArea.setWidgetResizable(True)
        self.logScrollArea.setObjectName("logScrollArea")
        self.logScrollAreaWidgetContents = QtWidgets.QWidget()
        self.logScrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 1634, 168))
        self.logScrollAreaWidgetContents.setObjectName("logScrollAreaWidgetContents")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.logScrollAreaWidgetContents)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.logLabel = QtWidgets.QLabel(self.logScrollAreaWidgetContents)
        self.logLabel.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.logLabel.setText("")
        self.logLabel.setObjectName("logLabel")
        self.verticalLayout_3.addWidget(self.logLabel)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem)
        self.logScrollArea.setWidget(self.logScrollAreaWidgetContents)
        self.verticalLayout_2.addWidget(self.logScrollArea)
        self.gridLayout_2.addWidget(self.vertSplitter, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1678, 22))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionQuit = QtWidgets.QAction(MainWindow)
        icon = QtGui.QIcon.fromTheme("exit")
        self.actionQuit.setIcon(icon)
        self.actionQuit.setObjectName("actionQuit")
        self.actionOpen = QtWidgets.QAction(MainWindow)
        icon = QtGui.QIcon.fromTheme("document-open")
        self.actionOpen.setIcon(icon)
        self.actionOpen.setObjectName("actionOpen")
        self.actionAbout = QtWidgets.QAction(MainWindow)
        self.actionAbout.setObjectName("actionAbout")
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        self.menuHelp.addAction(self.actionAbout)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Visualizer"))
        self.variableTreeWidget.headerItem().setText(0, _translate("MainWindow", "Variables"))
        self.plotGroupBox.setTitle(_translate("MainWindow", "Plot"))
        self.timeLabel.setText(_translate("MainWindow", "Time"))
        self.logGroupBox.setTitle(_translate("MainWindow", "Log"))
        self.menuFile.setTitle(_translate("MainWindow", "&File"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))
        self.actionQuit.setText(_translate("MainWindow", "&Quit"))
        self.actionQuit.setShortcut(_translate("MainWindow", "Ctrl+Q"))
        self.actionOpen.setText(_translate("MainWindow", "&Open"))
        self.actionOpen.setShortcut(_translate("MainWindow", "Ctrl+O"))
        self.actionAbout.setText(_translate("MainWindow", "About"))
from PyQt5 import QtWebEngineWidgets
