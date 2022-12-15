# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'robot_log_visualizer/ui/misc/set_robot_model.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_setRobotModelDialog(object):
    def setupUi(self, setRobotModelDialog):
        setRobotModelDialog.setObjectName("setRobotModelDialog")
        setRobotModelDialog.resize(365, 217)
        self.gridLayout = QtWidgets.QGridLayout(setRobotModelDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.buttonBox = QtWidgets.QDialogButtonBox(setRobotModelDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Abort|QtWidgets.QDialogButtonBox.Save)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 3, 0, 1, 1)
        self.frame = QtWidgets.QFrame(setRobotModelDialog)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setObjectName("frame")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.frame)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.robotModelLineEdit = QtWidgets.QLineEdit(self.frame)
        font = QtGui.QFont()
        font.setFamily("Ubuntu Mono")
        self.robotModelLineEdit.setFont(font)
        self.robotModelLineEdit.setObjectName("robotModelLineEdit")
        self.gridLayout_2.addWidget(self.robotModelLineEdit, 1, 0, 1, 1)
        self.label = QtWidgets.QLabel(self.frame)
        self.label.setObjectName("label")
        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)
        self.robotModelToolButton = QtWidgets.QToolButton(self.frame)
        self.robotModelToolButton.setObjectName("robotModelToolButton")
        self.gridLayout_2.addWidget(self.robotModelToolButton, 1, 1, 1, 1)
        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)
        self.frame_2 = QtWidgets.QFrame(setRobotModelDialog)
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setObjectName("frame_2")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.frame_2)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.label_3 = QtWidgets.QLabel(self.frame_2)
        self.label_3.setObjectName("label_3")
        self.gridLayout_3.addWidget(self.label_3, 0, 0, 1, 1)
        self.packageDirToolButton = QtWidgets.QToolButton(self.frame_2)
        self.packageDirToolButton.setObjectName("packageDirToolButton")
        self.gridLayout_3.addWidget(self.packageDirToolButton, 1, 1, 1, 1)
        self.packageDirLineEdit = QtWidgets.QLineEdit(self.frame_2)
        font = QtGui.QFont()
        font.setFamily("Ubuntu Mono")
        self.packageDirLineEdit.setFont(font)
        self.packageDirLineEdit.setObjectName("packageDirLineEdit")
        self.gridLayout_3.addWidget(self.packageDirLineEdit, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.frame_2, 1, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 2, 0, 1, 1)

        self.retranslateUi(setRobotModelDialog)
        self.buttonBox.accepted.connect(setRobotModelDialog.accept)
        self.buttonBox.rejected.connect(setRobotModelDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(setRobotModelDialog)

    def retranslateUi(self, setRobotModelDialog):
        _translate = QtCore.QCoreApplication.translate
        setRobotModelDialog.setWindowTitle(_translate("setRobotModelDialog", "Dialog"))
        self.label.setText(_translate("setRobotModelDialog", "Robot Model"))
        self.robotModelToolButton.setText(_translate("setRobotModelDialog", "..."))
        self.label_3.setText(_translate("setRobotModelDialog", "Package Directory"))
        self.packageDirToolButton.setText(_translate("setRobotModelDialog", "..."))
