# compile com: <pyinstaller --add-data 'icon/*.png:.' -F main.py>

import os
import os.path
import subprocess
import sys
import time
import urllib.request
from threading import Thread
from PySide2 import QtCore, QtGui
from PySide2.QtWidgets import *

app_name = 'DogUp!'
__version__ = '1.3a'

home_path = os.getenv('HOME')
local_path = os.path.join(home_path, '.local')
share_path = os.path.join(local_path, 'share')
log_path = os.path.join(home_path, '.local/share/dogup/')
log_tray = os.path.join(log_path, 'report.txt')
log_update = os.path.join(log_path, 'update.log')

if not os.path.exists(log_path):
	if os.path.exists(local_path):
		if os.path.exists(share_path):
			os.mkdir(log_path)
		else:
			os.mkdir(share_path)
			os.mkdir(log_path)
	else:
		os.mkdir(local_path)
		os.mkdir(share_path)
		os.mkdir(log_path)

if os.path.exists(log_tray):
	os.remove(log_tray)

def resource_path(relative_path, icon_path = True):
	"""Estabelece a pasta onde estão os ícones do app.
	Se compilado pelo PyInstaller, então está em '/tmp/__MEIPASS/';
	se executado pelo script original, então estsão na 'base_path'"""

	try:
		# PyInstaller creates a temp folder and stores path in _MEIPASS
		base_path = sys._MEIPASS
	except Exception:
		# a pasta do script pode ser tirada por 'os.path.abspath('')'
		if icon_path:
			base_path = '/home/frajola/mega/codes/dogup/icon/'
		else:
			base_path = '/home/frajola/mega/codes/dogup/'

	return os.path.join(base_path, relative_path)

def info(msg, newline = False, notify = False, end = '.'):
	"logger debugger"

	log_file = open(log_tray, 'a')
	log_time = time.strftime('%d/%m/%y, %H:%M')
	log_msg = f"[{log_time}]: {msg}{end}\n"

	if notify == True:
		send_notify(msg)

	if newline:
		log_file.write(f'\n{log_msg}\n')
	else:
		log_file.write(f'{log_msg}\n')

	print(log_msg)
	log_file.close()


def send_notify(msg):
	"Envia ao OS uma notificação"

	subprocess.run(f"notify-send '{app_name}' '{msg}'", shell = True)


class InternetConnection:
	"Verifica se há atualizações e, se sim, manipula essas logrmações"

	def __init__(self):

		self.online = False

		while self.online != True:
			self.online = self.connect()
			time.sleep(1)

	def connect(self):
		"Verifica a conexão de internet"

		info('Tentando conectar..')
		try:
			ping = urllib.request.urlopen('https://www.google.com/', timeout=1)
			if ping.getcode() == 200:
				info(f'Status da Conexão: Conectado ({ping.getcode()})')
				return True
			else:
				info(f'Status da Conexão: Desconectado ({ping.getcode()})')
				return False
		except:
			return False


class Update:
	"Constrói os dados para o uso no GUI"

	query_keylist = [
		'Name', 'Version', 'Description', 'Architecture',
		'URL', 'Licenses', 'Groups', 'Provides',
		'Depends On', 'Optional Deps', 'Required By', 'Optional For',
		'Conflicts With', 'Replaces', 'Installed Size', 'Packager',
		'Build Date', 'Install Date', 'Install Reason', 'Install Script',
		'Validated By'
		]

	def a__init__(self):
		raw_packages = subprocess.run(
							'pacman -Quq', shell=True, capture_output=True, encoding='utf-8')
		if raw_packages.returncode == 0:
			self.builder(raw_packages.stdout.split('\n'))
		elif raw_packages.returncode == 1:
			info('O sistema está atualizado', newline = True, notify = True)
			sys.exit(0)
		else:
			pass # exception

	def __init__(self):
		"Atualiza a situação do sistema"

		info('Refreshing...\n\npacman -Syy', end = '')
		refresh = subprocess.run(f'sudo pacman -Syy &>> {log_tray}', shell=True)
		if refresh.returncode == 0:
			raw_packages = subprocess.run(
								'pacman -Quq', shell=True, capture_output=True, encoding='utf-8')
			if raw_packages.returncode == 0:
				self.builder(raw_packages.stdout.split('\n'))
			elif raw_packages.returncode == 1:
				info('O sistema está atualizado', newline = True, notify = True)
				sys.exit(0)
			else:
				self.status = 'exception'
		else:
			self.status = 'exception'

	def builder(self, packages):
		"Construtor dos dados"

		try:
			self.list = []

			for element in packages:
				if element != '':
					self.list.append(element)

			self.version_process = Thread(target=self.new_version_builder)
			self.version_process.run()

			info(f"Pacotes desatualizados: {', '.join(self.list)}", newline = True)
			self.len = len(self.list)

			self.info_dict = {}

			for package in self.list:
				key = None
				dict_list = []
				value_list = []

				query = subprocess.run(
						f'pacman -Qi {package}', shell=True, capture_output=True, encoding='utf-8')
				raw_query = query.stdout.split('\n')

				for element in raw_query:
					if element != '' and ':' in element:
						content_list = element.split(':')

						if content_list[0].strip() in self.query_keylist:
							if key:
								value = self.value_generator(key, value_list)
								dict_list.append({key : value})
								value_list = []

						if len(content_list) == 2:
							if content_list[0].strip() in self.query_keylist:
								key = content_list[0].strip()
								value_list.append(content_list[1].strip())
							else:
								part_1 = content_list[0].strip()
								part_2 = content_list[1].strip()
								value_list.append(f'{part_1}: {part_2}')
							continue
						elif len(content_list) > 2:
							if content_list[0].strip() in self.query_keylist:
								key = content_list[0].strip()
								value = ':'.join(content_list[1:])
								value.strip()
								value_list.append(value)
					elif element and ':' not in element:
						value_list.append(element.strip())

					if key and key == 'Validated By':
						value = self.value_generator(key, value_list)
						dict_list.append({key : value})

				self.info_dict[package] = dict_list

			info('Foram geradas as informações dos pacotes desatualizados')
			self.status = 'normal'

		except:
			self.status = 'exception'

	def new_version_builder(self):
		"""Gera os valores da versão para qual o pacote será atualizado e as informações
		do log geral dos pacotes que forem atualizados"""

		self.sync_log = []
		self.version = {}

		command = subprocess.run('pacman -Qu', shell=True, capture_output=True, encoding='utf-8')
		raw_stdout = command.stdout.split('\n')
		for package in self.list:
			stdout_package = raw_stdout[0]
			self.sync_log.append(stdout_package.strip())
			split = stdout_package.split('->')
			self.version[package] = split[1].strip()
			raw_stdout.pop(0)

	def value_generator(self, key, raw_value):
		"Gera os valores para adicionar ao dicionário central (self.info_dict)"

		value_list = []

		if key == 'Optional Deps':
			for element in raw_value:
				value_list.append(element.strip())
		else:
			for element in raw_value:
				split_list = element.split(' ')
				if '' in split_list:
					while '' in split_list:
						split_list.remove('')
				for new_element in split_list:
					value_list.append(new_element.strip())

		return value_list


class TrayIcon(QSystemTrayIcon):
	"GUI Tray"

	def __init__(self, parent = None):
		super().__init__(parent)

		info('GUI iniciada')

		# TrayMainMenu
		self.parent = parent

		# Add icon and tooltip
		try:
			if 'linux' in pacman.list or 'linux-lts' in pacman.list:
				icon_file = 'kernel.png'
			else:
				icon_file = 'normal.png'
		except:
			icon_file = 'operation.png'

		self.icon(icon_file)
		self.setToolTip(f'{app_name}')

		# Abre o menu tanto pelo botão direito quanto pelo esquerdo do mouse
		# Se quiser somente pelo botão direito, use setContextMenu()
		self.activated.connect(self.show_menu)

	def icon(self, icon_file):
		"Gera o ícone do tray"

		self.setIcon(QtGui.QIcon(resource_path(icon_file)))

	def show_menu(self):
		"Abre o Menu"

		self.parent.show_menu()


class TrayMainMenu(QWidget):

	def __init__(self, initial_status = None):
		super().__init__()

		# Build and show TrayIcon
		self.tray = TrayIcon(self)
		self.tray.show()

		# QProcess da atualização
		self.process = QtCore.QProcess(self)
		self.process.finished.connect(self.log_writer)

		# Estética geral do widget
		self.setFixedSize(300, 250)
		self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

		box_frame = QFrame(self)
		box_frame.setGeometry(10, 20, 280, 220)
		box_frame.setFrameShape(QFrame.Box)
		box_frame.setFrameShadow(QFrame.Sunken)

		header_title = QLabel("DogUp!", self)
		header_title.setAlignment(QtCore.Qt.AlignCenter)
		header_title.setStyleSheet("font: 11pt; background-color: rgb(239, 239, 239);")
		header_title.setGeometry(20, 4, 80, 35)

		self.buttons = {}
		self.button_creator('sync', 'Atualizar', 20, 80, 260, 30, self.updater)
		self.button_creator('menu', 'Lista de pacotes', 20, 120, 260, 30)
		self.button_creator('info', 'Informações', 20, 160, 260, 30, self.show_output)
		self.button_creator('exit', 'Sair', 20, 200, 260, 30, self.exit)

		self.status = QLabel(self)
		self.status.setAlignment(QtCore.Qt.AlignCenter)
		self.status.setGeometry(20, 40, 260, 30)
		self.status.setFrameShape(QFrame.Box)
		self.status_changer(initial_status)

		# Build (OutputWidget and QMenu) or LogOutput
		try:
			self.output_widget = OutputWidget()

			self.menu = QMenu(self.buttons['menu'])
			for element in pacman.list:
				self.menu.addAction(str(element))
			self.buttons['menu'].setMenu(self.menu)
		except:
			self.buttons['menu'].setEnabled(False)
		finally:
			self.log_widget = LogOutput()

	def button_creator(self, name, label, x, y, width, height, func = None):
		"Cria os botões do main menu"

		self.buttons[name] = QPushButton(label, self)
		self.buttons[name].setGeometry(x, y, width, height)
		if func:
			self.buttons[name].clicked.connect(func)

	def show_menu(self):
		"Abre o main menu"

		self.show()
		mouse_qpoint = QtGui.QCursor.pos()
		self.move((mouse_qpoint.x() - self.minimumWidth()), mouse_qpoint.y())

	def show_output(self):
		"Mostra as informações ou o log"

		if self.buttons['info'].text() != 'Ver log':
			self.hide()
			self.output_widget.show()
		else:
			self.hide()
			self.log_widget.log_generator()

	def status_changer(self, status):
		"Gerencia o status no main menu"

		if status == 'updating':
			msg = 'Atualizando...'
			color = 'blue'
		elif status == 'updated':
			msg = 'O sistema está atualizado!'
			color = 'green'
		elif status == 'exception':
			msg = 'Houve um erro!'
			color = 'red'
			self.buttons['sync'].setEnabled(False)
			self.buttons['info'].setText('Ver log')
			info('Um erro surgiu durante a execução!')
			send_notify('Um erro surgiu durante a execução!')
		else:
			msg = f'Há {len(pacman.list)} pacotes desatualizados!'
			color = 'red'

		self.status.setText(msg)
		self.status.setStyleSheet(f"font: bold 10pt; color: {color}")

	def updater(self):
		"Atualiza o sistema"

		info(f"Atualizando: {', '.join(pacman.list)}.\n\npacman -Su --noconfirm", end = '')
		self.status_changer('updating')
		self.tray.icon('operation.png')
		self.buttons['sync'].setEnabled(False)
		self.hide()

		try:
			command = f"{resource_path(f'qprocess.py', False)}"
			args = [f"{log_tray}"]
			self.process.start(command, args)
		except:
			self.status_changer('exception')

	def log_writer(self, exitCode, exitStatus):
		"Escreve os pacotes atualizados no log e fecha o app"

		info('O sistema foi atualizado', newline = True, notify = True)
		self.status_changer('updated')
		self.tray.icon('normal.png')

		log_text = ''

		if os.path.exists(log_update):
			option = 'a'
			log_text += '\n'
		else:
			option = 'w'
			log_text += "## Dogup's updates ##\n\n"

		log_file = open(log_update, option)
		log_text += f"[Update - {time.strftime('%d/%m/%y')}]:\n"
		for package in pacman.sync_log:
			log_text += f"{package}\n"
		log_file.write(log_text)
		log_file.close()

	def exit(self):
		"Fecha o app completamente"

		if self.process.state() == QtCore.QProcess.NotRunning:
			self.close()
		else:
			send_notify('Aguarde o sistema atualizar...')

	def leaveEvent(self, event):
		"Esconde o menu quando o mouse deixa o widget"

		if not self.menu.isVisible():
			self.hide()


class OutputWidget(QWidget):
	"Mostra as info de pacman -Qui"

	comma_keys = [
			'Licenses', 'Provides', 'Depends On',
			'Required By', 'Optional For', 'Optional Deps',
			'Replaces', 'Conflicts With'
			]

	def __init__(self, parent = None):
		super().__init__(parent)

		self.setWindowTitle(f'{app_name} - Informações:')
		self.setFixedSize(850, 650)

		self.max_length = 50
		self.full_info = False

		main_layout = QGridLayout()
		main_layout.setHorizontalSpacing(10)
		left_wing = QVBoxLayout()
		left_wing.setSpacing(10)
		right_wing = QVBoxLayout()

		main_layout.addLayout(left_wing, 1, 1)
		main_layout.addLayout(right_wing, 1, 2)
		self.setLayout(main_layout)

		scroll = QScrollArea()
		scroll.setGeometry(210, 100, 620, 500)
		scroll.setWidgetResizable(True)

		self.info_button = QPushButton('More info')
		self.info_button.setMinimumSize(190, 40)
		self.info_button.clicked.connect(self.expand)
		left_wing.addWidget(self.info_button)

		right_wing.addWidget(scroll)

		self.list_view = QListWidget()
		self.list_view.setFixedWidth(190)
		self.list_view.setMinimumHeight(550)
		self.list_view.setSpacing(4)
		self.list_view.setFont(QtGui.QFont('Helvetica', 16))
		self.list_view.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
		self.list_view.itemSelectionChanged.connect(self.journalist)
		left_wing.addWidget(self.list_view)

		for package in pacman.list:
			self.list_view.addItem(package)
		self.list_view.setCurrentItem(self.list_view.item(0))

		label_widget = QWidget()
		label_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
		label_layout = QVBoxLayout()
		label_widget.setLayout(label_layout)
		self.label_dict = {}

		for key in pacman.query_keylist:
			self.label_dict[key] = QLabel(key)
			self.label_dict[key].setFont(QtGui.QFont('Helvetica', 14))
			label_layout.addWidget(self.label_dict[key])

		self.list_view.setFocus()
		scroll.setWidget(label_widget)
		self.journalist()

	def journalist(self):
		"Quando o item da lista é selecionado, completa-se os campos do pacote"

		max_length = self.max_length

		package = self.list_view.currentItem().text()
		for dictionary in pacman.info_dict[package]:
			for key in pacman.query_keylist:
				try:
					value = ''

					if key == 'Version' and not pacman.version_process.is_alive():
						version_value = f"{dictionary[key][0]} > {pacman.version[package]}"
						value_list = [version_value]
					else:
						value_list = dictionary[key]

					for element in value_list:
						if len(value) + len(element) <= max_length:
							if value == '':
								value += element
							else:
								if key in self.comma_keys:
									value += f', {element}'
								else:
									value += f' {element}'
						else:
							if not self.full_info:
								if len(value) + 4 <= max_length:
									value += ' ...'
								else:
									value = f"{value[:-4]} ..."
								break
							else:
								if value == '':
									value += element
								else:
									if key in self.comma_keys:
										value += f",\n\t  {element}"
									else:
										value += f"\n\t  {element}"

									max_length += (self.max_length - 20)

					max_length = self.max_length
					self.label_dict[key].setText(f'{key}: {value}')
				except:
					pass

	def expand(self, fullscreen_trigger = False):
		"Mostra as informações na sua totalidade"

		if self.full_info:
			self.info_button.setText('More info')
			self.full_info = False
			self.list_view.setFocus()
		else:
			self.info_button.setText('Less info')
			self.full_info = True

		self.font_setter()
		self.journalist()

	def font_setter(self):
		"Redimensiona o tamanho da fonte"

		for key in pacman.query_keylist:
			if self.isFullScreen() or not self.full_info:
				size = 14
			elif self.full_info:
				size = 12

			self.label_dict[key].setFont(QtGui.QFont('Helvetica', size))

	def resizeEvent(self, event):
		"Ajusta o ponto de corte da linha"

		if self.isVisible():
			event.accept()

			if self.isFullScreen() or self.isMaximized():
				if self.max_length != 110:
					self.max_length = 110
			else:
				if self.max_length != 50:
					self.max_length = 50

			self.font_setter()
			self.journalist()

	def closeEvent(self, event):
		"Coordena os signals para fechar o app"

		event.ignore()
		self.hide()


class LogOutput(QWidget):
	"Mostra o log quando exceptions são raised"

	def __init__(self, parent = None):
		super().__init__()

		self.setWindowTitle(f'{app_name} - Log ({log_tray}):')
		self.setFixedSize(850, 650)

		self.scroll = QScrollArea(self)
		self.scroll.setGeometry(10, 10, 830, 620)
		self.scroll.setWidgetResizable(True)

	def log_generator(self):
		"Gera o log e mostra o widget"

		report = open(log_tray)
		content = report.read()
		report.close()
		label_content = QLabel(content)
		label_content.setMargin(10)
		self.scroll.setWidget(label_content)

		self.show()

	def closeEvent(self, event):
		"Coordena os signals para fechar o app"

		event.ignore()
		self.hide()


if __name__ == '__main__':
	info(f'{app_name} ({__version__})')
	connection = InternetConnection()
	if connection.online:
		pacman = Update()
		app = QApplication([])
		widget = TrayMainMenu(pacman.status)
		sys.exit(app.exec_())
