# -*- coding: utf-8 -*-

################################################################################
# Form generated from reading UI file 'version_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QLabel, QLineEdit,
                               QSizePolicy, QVBoxLayout)
from . import antistasi_logbook_main_ressources


class Ui_VersionDialog(object):
    def setupUi(self, VersionDialog):
        if not VersionDialog.objectName():
            VersionDialog.setObjectName(u"VersionDialog")
        VersionDialog.resize(400, 100)
        VersionDialog.setMaximumSize(QSize(400, 100))
        self.verticalLayout = QVBoxLayout(VersionDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.version_label = QLabel(VersionDialog)
        self.version_label.setObjectName(u"version_label")
        font = QFont()
        font.setPointSize(19)
        font.setBold(True)
        self.version_label.setFont(font)
        self.version_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.version_label)

        self.version_line = QLineEdit(VersionDialog)
        self.version_line.setObjectName(u"version_line")
        self.version_line.setReadOnly(True)

        self.verticalLayout.addWidget(self.version_line)

        self.retranslateUi(VersionDialog)
    # setupUi

    def retranslateUi(self, VersionDialog):
        VersionDialog.setWindowTitle(QCoreApplication.translate("VersionDialog", u"Dialog", None))
        self.version_label.setText(QCoreApplication.translate("VersionDialog", u"VERSION", None))
    # retranslateUi
