from PyQt5 import QtWidgets, QtGui, QtCore, uic

from asrInterface import Ui_MainWindow
import sys

import speech_recognition as sr
from voice_thread import MainRecognizingThread, PlaySoundThread
from utils import *


class myWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(myWindow, self).__init__()
        self.myCommand = " "
        self.mode = "zh"
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.greetingThread = MainRecognizingThread(self)
        self.greetingThread.prepare_signal.connect(self.prepared_callback)
        self.greetingThread.start()


    def prepared_callback(self, status):
        if status is True:
            self.ui.retranslateUi(self, "zh")

    def close_window(self):
        self.close()

    def change_color(self, color_tuple):
        self.ui.changeColor(self, color_tuple)

    def change_mode(self):
        if self.mode == "zh":
            self.mode = "en"
        else:
            self.mode = "zh"
        self.ui.retranslateUi(self, self.mode)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    application = myWindow()
    application.show()
    sys.exit(app.exec())

