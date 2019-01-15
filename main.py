# compile com: <pyinstaller --add-data 'icon/*.png:.' -F main.py>

import os
import os.path
import subprocess
import sys
import threading
import time
import urllib.request
from PySide2 import QtCore, QtGui
from PySide2.QtWidgets import *

app_name = 'DogUp!'
__version__ = '1.2a'

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

def resource_path(relative_path):
	"""Estabelece a pasta onde estão os ícones do app.
	Se compilado pelo PyInstaller, então está em '/tmp/__MEIPASS/';
	se executado pelo script original, então estsão na 'base_path'"""

	try:
		# PyInstaller creates a temp folder and stores path in _MEIPASS
		base_path = sys._MEIPASS
	except Exception:
		# a pasta do script pode ser tirada por 'os.path.abspath('')'
		base_path = '/home/frajola/mega/codes/dogup/icon'

	return os.path.join(base_path, relative_path)

def info(msg, newline = False, notify = False, end = '.'):
	"logger debugger"

	log_file = open(log_tray, 'a')
	log_time = time.strftime('%d/%m/%y, %H:%M')
	log_msg = f"[{log_time}]: {msg}{end}\n"

	if notify == True:
		subprocess.run(f"notify-send '{app_name}' '{msg}.'", shell = True)

	if newline:
		log_file.write(f'\n{log_msg}\n')
	else:
		log_file.write(f'{log_msg}\n')

	print(log_msg)
	log_file.close()


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

	def __init__(self):
		"Atualiza a situação do sistema"

		info('Refreshing...\n\npacman -Syy', end = '')
		refresh = subprocess.run(f'sudo pacman -Syy >> {log_tray}', shell=True)
		if refresh.returncode == 0:
			raw_packages = subprocess.run(
								'pacman -Quq', shell=True, capture_output=True, encoding='utf-8')
			if raw_packages.returncode == 0:
				self.builder(raw_packages.stdout.split('\n'))
			elif raw_packages.returncode == 1:
				info('O sistema está atualizado', newline = True, notify = True)
				sys.exit(0)
			else:
				pass # exception
		else:
			pass # exception

	def builder(self, packages):
		"Construtor dos dados"

		self.list = []

		for element in packages:
			if element != '':
				self.list.append(element)

		self.version_process = threading.Thread(target=self.new_version_builder)
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


class TrayWidget(QSystemTrayIcon):
	"GUI Tray"

	def __init__(self, parent = None):
		super().__init__(parent)

		# OutputWidget
		self.parent = parent

		# Add icon and tooltip
		if 'linux' in pacman.list or 'linux-lts' in pacman.list:
			icon_file = 'kernel.png'
		else:
			icon_file = 'normal.png'

		self.setIcon(QtGui.QIcon(resource_path(icon_file)))
		self.setToolTip(f'{app_name}')

		self.menu = QMenu()
		submenu = QMenu(f'Há {pacman.len} pacotes desatualizados!')
		for element in pacman.list:
			submenu.addAction(element)
		self.menu.addMenu(submenu)
		self.menu.addAction('Atualizar o sistema', self.update)
		self.menu.addAction('Informações sobre os pacotes', self.show_output)
		self.menu.addAction('Sair', self.exit)

		# Abre o menu tanto pelo botão direito quanto pelo esquerdo do mouse
		# Se quiser somente pelo botão direito, use setContextMenu()
		self.activated.connect(self.main_menu)

	def update(self):
		"Atualiza o sistema"

		info(f"Atualizando: {', '.join(pacman.list)}.\n\npacman -Su --noconfirm", end = '')
		self.hide()

		try:
			subprocess.run(f'sudo pacman -Su --noconfirm >> {log_tray}', shell=True)
			info('O sistema foi atualizado', newline = True, notify = True)
			self.log_and_exit()
		except:
			self.show()

	def log_and_exit(self):
		"Escreve os pacotes atualizados no log e fecha o app"

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
		self.exit()

	def show_output(self):
		"Mostra as informações"

		self.parent.show()

	def exit(self):
		"Fecha o app completamente"

		self.parent.signal = True
		self.parent.close()

	def main_menu(self):
		"Abre o ContextMenu"

		self.menu.exec_(QtGui.QCursor.pos())


class OutputWidget(QWidget):
	"Mostra as info de pacman -Qui"

	comma_keys = [
			'Licenses', 'Provides', 'Depends On',
			'Required By', 'Optional For', 'Optional Deps',
			'Replaces', 'Conflicts With'
			]

	def __init__(self, parent = None):
		super().__init__(parent)

		info('Tray iniciado')

		# Signal to close
		self.signal = False

		# Show TrayWidget
		tray = TrayWidget(self)
		tray.show()

		self.setWindowTitle(f'{app_name}')
		self.setFixedSize(850, 650)

		self.max_length = 50
		self.full_info = False

		main_layout = QGridLayout()
		main_layout.setHorizontalSpacing(30)
		left_wing = QVBoxLayout()
		left_wing.setSpacing(10)
		right_wing = QVBoxLayout()
		main_layout.addLayout(left_wing, 1, 1)
		main_layout.addLayout(right_wing, 1, 2)
		self.setLayout(main_layout)

		self.info_button = QPushButton('More info')
		self.info_button.clicked.connect(self.expand)
		left_wing.addWidget(self.info_button)

		self.list_view = QListWidget()
		self.list_view.setFixedWidth(190)
		self.list_view.setMinimumHeight(550)
		self.list_view.setFont(QtGui.QFont('Helvetica', 16))
		self.list_view.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
		self.list_view.itemSelectionChanged.connect(self.journalist)
		left_wing.addWidget(self.list_view)

		for package in pacman.list:
			self.list_view.addItem(package)
		self.list_view.setCurrentItem(self.list_view.item(0))

		self.label_dict = {}

		for key in pacman.query_keylist:
			self.label_dict[key] = QLabel(key)
			self.label_dict[key].setFont(QtGui.QFont('Helvetica', 14))
			right_wing.addWidget(self.label_dict[key])

		self.journalist()

	def journalist(self):
		"Quando o item da lista é selecionado, completa-se os campos do pacote"

		max_length = self.max_length

		package = self.list_view.currentItem().text()
		for dictionary in pacman.info_dict[package]:
			for key in pacman.query_keylist:
				try:
					value = ''
					if key == 'Version' and not pacman.version_process.isAlive():
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
						elif not self.full_info:
							if len(value) + 4 <= max_length:
								value += ' ...'
							else:
								value = f"{value[:-4]} ..."
							break
						else:
							if len(element) > max_length:
								value += f"{element[:-4]} ..."
							elif key in self.comma_keys:
								value += f",\n\t  {element}"
							else:
								value += f"\n\t  {element}"
							max_length += self.max_length

					max_length = self.max_length
					self.label_dict[key].setText(f'{key}: {value}')
				except:
					pass

	def expand(self, fullscreen_trigger = False):
		"Mostra as informações na sua totalidade"

		if self.full_info:
			self.info_button.setText('More info')
			self.full_info = False
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

		if self.signal:
			info(f'{app_name} foi encerrado')
			event.accept()
		else:
			event.ignore()
			self.hide()


if __name__ == '__main__':
	info(f'{app_name} ({__version__})')
	connection = InternetConnection()
	if connection.online:
		pacman = Update()
		app = QApplication([])
		widget = OutputWidget()
		sys.exit(app.exec_())
