# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'download_song.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(697, 516)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("images/iconfinder.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Form.setWindowIcon(icon)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lineEdit_search = QtWidgets.QLineEdit(Form)
        self.lineEdit_search.setObjectName("lineEdit_search")
        self.horizontalLayout.addWidget(self.lineEdit_search)
        self.pushButton_search = QtWidgets.QPushButton(Form)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("images/magnifier.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_search.setIcon(icon1)
        self.pushButton_search.setObjectName("pushButton_search")
        self.horizontalLayout.addWidget(self.pushButton_search)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.scrollArea = QtWidgets.QScrollArea(Form)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 677, 445))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.gridLayout_search = QtWidgets.QGridLayout()
        self.gridLayout_search.setObjectName("gridLayout_search")
        self.verticalLayout_2.addLayout(self.gridLayout_search)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
        self.label_error = QtWidgets.QLabel(Form)
        self.label_error.setText("")
        self.label_error.setObjectName("label_error")
        self.verticalLayout.addWidget(self.label_error)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Добавить песню"))
        self.lineEdit_search.setPlaceholderText(_translate("Form", "Поиск..."))
        self.pushButton_search.setText(_translate("Form", "Искать"))
