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
        setRobotModelDialog.resize(711, 363)
        self.formLayout = QtWidgets.QFormLayout(setRobotModelDialog)
        self.formLayout.setObjectName("formLayout")
        self.frame = QtWidgets.QFrame(setRobotModelDialog)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setObjectName("frame")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.frame)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label = QtWidgets.QLabel(self.frame)
        self.label.setObjectName("label")
        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)
        self.robotModelToolButton = QtWidgets.QToolButton(self.frame)
        self.robotModelToolButton.setObjectName("robotModelToolButton")
        self.gridLayout_2.addWidget(self.robotModelToolButton, 1, 1, 1, 1)
        self.robotModelLineEdit = QtWidgets.QLineEdit(self.frame)
        font = QtGui.QFont()
        font.setFamily("Ubuntu Mono")
        self.robotModelLineEdit.setFont(font)
        self.robotModelLineEdit.setObjectName("robotModelLineEdit")
        self.gridLayout_2.addWidget(self.robotModelLineEdit, 1, 0, 1, 1)
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.SpanningRole, self.frame)
        self.frame_2 = QtWidgets.QFrame(setRobotModelDialog)
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setObjectName("frame_2")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.frame_2)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.packageDirLineEdit = QtWidgets.QLineEdit(self.frame_2)
        font = QtGui.QFont()
        font.setFamily("Ubuntu Mono")
        self.packageDirLineEdit.setFont(font)
        self.packageDirLineEdit.setObjectName("packageDirLineEdit")
        self.gridLayout_3.addWidget(self.packageDirLineEdit, 1, 0, 1, 1)
        self.packageDirToolButton = QtWidgets.QToolButton(self.frame_2)
        self.packageDirToolButton.setObjectName("packageDirToolButton")
        self.gridLayout_3.addWidget(self.packageDirToolButton, 1, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.frame_2)
        self.label_3.setObjectName("label_3")
        self.gridLayout_3.addWidget(self.label_3, 0, 0, 1, 1)
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.SpanningRole, self.frame_2)
        self.frame_3 = QtWidgets.QFrame(setRobotModelDialog)
        self.frame_3.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_3.setObjectName("frame_3")
        self.formLayout_2 = QtWidgets.QFormLayout(self.frame_3)
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_5 = QtWidgets.QLabel(self.frame_3)
        self.label_5.setObjectName("label_5")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.frameNameComboBox = QtWidgets.QComboBox(self.frame_3)
        self.frameNameComboBox.setMaxVisibleItems(5)
        self.frameNameComboBox.setObjectName("frameNameComboBox")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.frameNameComboBox)
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.SpanningRole, self.frame_3)
        self.buttonBox = QtWidgets.QDialogButtonBox(setRobotModelDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Abort|QtWidgets.QDialogButtonBox.Save)
        self.buttonBox.setObjectName("buttonBox")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.SpanningRole, self.buttonBox)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.formLayout.setItem(3, QtWidgets.QFormLayout.FieldRole, spacerItem)

        self.retranslateUi(setRobotModelDialog)
        self.buttonBox.accepted.connect(setRobotModelDialog.accept)
        self.buttonBox.rejected.connect(setRobotModelDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(setRobotModelDialog)

    def retranslateUi(self, setRobotModelDialog):
        _translate = QtCore.QCoreApplication.translate
        setRobotModelDialog.setWindowTitle(_translate("setRobotModelDialog", "Dialog"))
        self.label.setText(_translate("setRobotModelDialog", "Robot Model"))
        self.robotModelToolButton.setText(_translate("setRobotModelDialog", "..."))
        self.packageDirToolButton.setText(_translate("setRobotModelDialog", "..."))
        self.label_3.setText(_translate("setRobotModelDialog", "Package Directory"))
        self.label_5.setText(_translate("setRobotModelDialog", "Base Frame"))
