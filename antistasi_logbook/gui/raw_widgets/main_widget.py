# -*- coding: utf-8 -*-

################################################################################
# Form generated from reading UI file 'main_widget.ui'
##
# Created by: Qt User Interface Compiler version 6.2.1
##
# WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
                            QMetaObject, QObject, QPoint, QRect,
                            QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
                           QFont, QFontDatabase, QGradient, QIcon,
                           QImage, QKeySequence, QLinearGradient, QPainter,
                           QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QSizePolicy, QSplitter,
                               QWidget)


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(919, 667)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.InfoWidget = QWidget(Form)
        self.InfoWidget.setObjectName(u"InfoWidget")
        self.InfoWidget.setMaximumSize(QSize(16777215, 91))

        self.gridLayout.addWidget(self.InfoWidget, 0, 0, 1, 1)

        self.splitter = QSplitter(Form)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.SideBarWidget = QWidget(self.splitter)
        self.SideBarWidget.setObjectName(u"SideBarWidget")
        self.SideBarWidget.setMaximumSize(QSize(196, 16777215))
        self.splitter.addWidget(self.SideBarWidget)
        self.MainInteractionWidget = QWidget(self.splitter)
        self.MainInteractionWidget.setObjectName(u"MainInteractionWidget")
        self.splitter.addWidget(self.MainInteractionWidget)

        self.gridLayout.addWidget(self.splitter, 1, 0, 1, 1)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
    # retranslateUi
