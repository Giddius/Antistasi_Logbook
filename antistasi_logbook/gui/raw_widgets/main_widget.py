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
from . import antistasi_logbook_main_ressources


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(919, 667)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.info_widget = QWidget(Form)
        self.info_widget.setObjectName(u"info_widget")
        self.info_widget.setMaximumSize(QSize(16777215, 91))

        self.gridLayout.addWidget(self.info_widget, 0, 0, 1, 1)

        self.side_bar_main_interaction_splitter = QSplitter(Form)
        self.side_bar_main_interaction_splitter.setObjectName(u"side_bar_main_interaction_splitter")
        self.side_bar_main_interaction_splitter.setOrientation(Qt.Horizontal)
        self.side_bar_widget = QWidget(self.side_bar_main_interaction_splitter)
        self.side_bar_widget.setObjectName(u"side_bar_widget")
        self.side_bar_widget.setMaximumSize(QSize(196, 16777215))
        self.side_bar_main_interaction_splitter.addWidget(self.side_bar_widget)
        self.main_interaction_widget = QWidget(self.side_bar_main_interaction_splitter)
        self.main_interaction_widget.setObjectName(u"main_interaction_widget")
        self.side_bar_main_interaction_splitter.addWidget(self.main_interaction_widget)

        self.gridLayout.addWidget(self.side_bar_main_interaction_splitter, 1, 0, 1, 1)

        self.retranslateUi(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
    # retranslateUi
