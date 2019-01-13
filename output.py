import pdb
import sys
from PySide2 import QtCore, QtGui
from PySide2.QtWidgets import *

#pdb.set_trace()

lista = ['pacote 1', 'pacote 2', 'pacote 3', 'pacote 4']

class OutputWidget(QWidget):
	"Mostra as info de pacman -Qui"

	def __init__(self, parent = None):
		super().__init__(parent)

		self.setFixedSize(300, 200)
		self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
		#menu_widget = QWidget(self)
		#menu_widget.setGeometry(0, 0, 290, 40)
		#hlayout = QHBoxLayout()
		#menu_widget.setLayout(hlayout)

		menu_button = QPushButton('Pacotes desatualizados', self)
		menu_button.setGeometry(10, 10, 235, 50)
		menu_button.setFont(QtGui.QFont('Helvetica', 14))

		number = QLabel(f"<font color=red size=20><b>{len(lista)}<\b><\font>", self)
		number.setGeometry(260, -10, 30, 90)

		#submenu.setMinimumSize(290, 90)
		#for element in lista:
		#	submenu.addAction(element)
		#menu.addMenu(submenu)

		#hlayout.addWidget(menu_button)
		#hlayout.addSpacing(20)


if __name__ == '__main__':
	app = QApplication([])
	widget = OutputWidget()
	widget.show()
	sys.exit(app.exec_())
