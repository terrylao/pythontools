"""
  publish with BSD Licence.
	Copyright (c) Terry Lao
"""
# REQUIREMENT:
#1.	Python 3.7
#2.	pytesseract
#3.	pyperclip
#4.	Pillow
#5.	PyQt5_sip
#6.	PyQt5
#7.	win10toast
#8.	SystemHotkey
#9. numpy
#10.	https://github.com/UB-Mannheim/tesseract/wiki for tesseract 4/5
#11.	https://github.com/tesseract-ocr/tessdata_best for trained data, chi_trad,chi_sim and so on
#12.	環境變數 path 加入tesseract
#
#使用方法: 帶兩個參數，第一個語系：eng(英文)/chi_tra(繁中)/chi_sim(簡中) and so on，第二個為OPTIONAL，以處理黑底的畫面：b 
#python screenshottext.py eng/chi_tra/chi_sim/eng+chi_tra/eng+chi_sim [b]


import io
import os
import sys
import numpy as np
import pyperclip
import pytesseract
from system_hotkey import SystemHotkey
from functools import partial
from PIL import Image,ImageOps
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QMenu, QAction, QSystemTrayIcon
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QIcon
try:
	from pynotifier import Notification
except ImportError:
	pass

class Snipper(QtWidgets.QWidget):
	bwhite=0
	exit_signal = pyqtSignal()
	sig_keyhot = pyqtSignal(str)
	def __init__(self, parent=None, flags=Qt.WindowFlags(),paramsbwhite=0):
		super().__init__(parent=parent, flags=flags)
		bwhite=paramsbwhite
		self.setWindowTitle("ScreenShotText")
		self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog)
		self.setWindowState(self.windowState() | Qt.WindowFullScreen)
		self.plang='eng'
		self.screen = QtWidgets.QApplication.screenAt(QtGui.QCursor.pos()).grabWindow(0)
		palette = QtGui.QPalette()
		palette.setBrush(self.backgroundRole(), QtGui.QBrush(self.screen))
		self.setPalette(palette)

		QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))

		self.start, self.end = QtCore.QPoint(), QtCore.QPoint()
		
		# Adding an icon 
		icon = QIcon("icon.png") 
		
		# Adding item on the menu bar 
		self.tray = QSystemTrayIcon() 
		self.tray.setIcon(icon) 
		self.tray.setVisible(True) 
		
		self.langs = pytesseract.get_languages()
		print('langs:',self.langs)
		# Creating the options 
		self.menu = QMenu() 
		self.options=[]
		i=int(0)
		#2. 設定我們的自訂快速鍵響應函數
		self.sig_keyhot.connect(self.MKey_pressEvent)
		self.hk = SystemHotkey()
		for lang in self.langs:
			if lang=='eng' or lang=='osd':
				continue;
			qact=QAction('Capture:'+lang, self)
			qact.triggered.connect(lambda checked, lang='eng+'+lang: self.triggerCapture(lang))
			self.options.append(qact)
			
			i+=1
			self.hk.register(('control', str(i)), callback=lambda checked, lang=lang:self.send_key_event(lang))
			if i==8:
				break
		self.hk.register(('control', 'q'), callback=app.quit)
		for j in range(i):
			self.menu.addAction(self.options[j]) 
		self.maxHotKey=i

		# To quit the app 
		self.quit = QAction("Quit") 
		self.quit.triggered.connect(app.quit) 
		self.menu.addAction(self.quit) 
		
		# Adding options to the System Tray 
		self.tray.setContextMenu(self.menu) 
		self.tray.show()
	def triggerCapture(self,alang):
		self.screen = QtWidgets.QApplication.screenAt(QtGui.QCursor.pos()).grabWindow(0)
		palette = QtGui.QPalette()
		palette.setBrush(self.backgroundRole(), QtGui.QBrush(self.screen))
		self.setPalette(palette)

		QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
		self.plang=alang
		self.start, self.end = QtCore.QPoint(), QtCore.QPoint()
		self.show()
		
	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Escape:
			QtWidgets.QApplication.quit()
		# Ctrl + ...
		"""if event.modifiers() == Qt.ControlModifier:
			for i in range(self.maxHotKey):
			# (ctrl + 1~maxHotKey) REF:https://doc.qt.io/qt-6/qt.html
				if event.key() == 0x30+i:
					self.triggerCapture(self.langs[i])
		"""		

		return super().keyPressEvent(event)

	def paintEvent(self, event):
		painter = QtGui.QPainter(self)
		painter.setPen(Qt.NoPen)
		painter.setBrush(QtGui.QColor(0, 0, 0, 100))
		painter.drawRect(0, 0, self.width(), self.height())

		if self.start == self.end:
			return super().paintEvent(event)

		painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 3))
		painter.setBrush(painter.background())
		painter.drawRect(QtCore.QRect(self.start, self.end))
		return super().paintEvent(event)

	def mousePressEvent(self, event):
		self.start = self.end = event.pos()
		self.update()
		return super().mousePressEvent(event)

	def mouseMoveEvent(self, event):
		self.end = event.pos()
		self.update()
		return super().mousePressEvent(event)
	
	def mouseReleaseEvent(self, event):
		if self.start == self.end:
			return super().mouseReleaseEvent(event)

		self.hide()
		QtWidgets.QApplication.processEvents()
		shot = self.screen.copy(QtCore.QRect(self.start, self.end))
		if bwhite:
			print('BlackBackGroundImage')
			BlackBackGroundImage(shot)
		else:
			print('processImage')
			processImage(shot,self.plang)
		#QtWidgets.QApplication.quit()
		self.hide()
	def closeEvent(self, event):
		self.exit_signal.emit()
	#快速鍵處理函數
	def MKey_pressEvent(self,i_str):
		print("按下的按键是%s" % (i_str,))
		self.triggerCapture(i_str)
		
	#快速鍵訊號傳送函數(將外部訊號，轉化成qt訊號)
	def send_key_event(self,i_str):
		self.sig_keyhot.emit(i_str)

def processImage(img,plang='eng'):
	buffer = QtCore.QBuffer()
	buffer.open(QtCore.QBuffer.ReadWrite)
	img.save(buffer, "PNG")
	pil_imgo = Image.open(io.BytesIO(buffer.data()))
	pil_img = pil_imgo.resize((int(pil_imgo.width*1.3),int(pil_imgo.height*1.3)))
	buffer.close()
	print('processImage:',plang)
	config = ("--oem 1 --psm 7")
	try:
		result = pytesseract.image_to_string(pil_img, timeout=100, lang=plang, config=config)
	except RuntimeError as error:
		print(f"ERROR: An error occurred when trying to process the image: {error}")
		return
	
	if result:
		pyperclip.copy(result)
		print(f'INFO: Copied "{result}" to the clipboard')
	else:
		print(f"INFO: Unable to read text from image, did not copy")

def BlackBackGroundImage(imginput):
	buffer = QtCore.QBuffer()
	buffer.open(QtCore.QBuffer.ReadWrite)
	imginput.save(buffer, "PNG")
	pil_img = Image.open(io.BytesIO(buffer.data())).convert("L")
	buffer.close()
	img = ImageOps.invert(pil_img)
	#img.show()
	threshold = 200
	table = []
	pixelArray = img.load()
	for y in range(img.size[1]): # binaryzate it
		List = []
	for x in range(img.size[0]):
		if pixelArray[x,y] < threshold:
			List.append(0)
		else:
			List.append(255)
	table.append(List)

	imginv = Image.fromarray(np.array(table,dtype="uint8")) # load the image from array.
	#imginv.show()
	#print('finished binarized')
	plang=None
	if len(sys.argv) > 1:
		plang=sys.argv[1]
	try:
		result = pytesseract.image_to_string(
		imginv, timeout=100, lang=plang#(sys.argv[1] if len(sys.argv) > 1 else None)
		)
	except RuntimeError as error:
		print(f"ERROR: An error occurred when trying to process the image: {error}")
		return
	if result:
		if plang.find('chi_tra')>-1 or plang.find('chi_sim')>-1:
			result=result.replace(' ', '')
			pyperclip.copy(result)
			print(f'INFO: Copied "{result}" to the clipboard')

		else:
			print(f"INFO: Unable to read text from image, did not copy")

if __name__ == "__main__":
	#global bwhite
	bwhite=0
	#usage: python screenshottext.py eng/chi_tra/chi_sim/chi_tra+eng [b]
	if len(sys.argv) > 2:
		bwhite=sys.argv[2]
	else:
		if len(sys.argv)==0:
			print('usage: python screenshottext.py eng/chi_tra/chi_tra+eng [b]')
			sys.exit()
	try:
		pytesseract.get_tesseract_version()
	except EnvironmentError:
		print(
		"ERROR: Tesseract is either not installed or cannot be reached.\n"
		"Have you installed it and added the install directory to your system path?"
		)
		sys.exit()
	version = pytesseract .get_tesseract_version()
	print('version:',version)
	QtCore.QCoreApplication.setAttribute(Qt.AA_DisableHighDpiScaling)
	app = QtWidgets.QApplication(sys.argv)
	window = QtWidgets.QMainWindow()
	snipper = Snipper(window,paramsbwhite=bwhite)
	#snipper.show()
	print('snipper ready')
	snipper.exit_signal.connect(app.quit)
	sys.exit(app.exec_())
