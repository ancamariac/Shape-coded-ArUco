# importare biblioteci
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot, QPoint
from PyQt5.QtGui import QImage, QPixmap, QPainter
import os
import sys
import time
import cv2
import math
import numpy as np

# Definire clasa thread, care va updata interfata cu streamul video de la camera
class Thread(QThread):
    # Semnal trimis de la thread la aplicatie la fiecare achizitie a unui frame
    changePixmap = pyqtSignal(QImage)
    # Variabila ce pastreaza modul de vizualizare al camerei
    currentCameraView = 'normal'

    def run(self):
        # deschidere camera cu Opencv
        cap = cv2.VideoCapture(0)
        
        width = QDesktopWidget().screenGeometry(-1).width()
        height = QDesktopWidget().screenGeometry(-1).height()
        
        while True:
            # citire frame de la camera folosind OpenCV
            ret, frame = cap.read()
            if ret:
                if( self.currentCameraView == 'normal' ):
                    # Convertire din formatul in care se reprezinta o imagine in OpenCV (BGR) 
                    # in formatul folosit la afisarea pe ecran (RGB)
                    rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                elif( self.currentCameraView == 'grayscale' ):
                    # Convertire imagine din color in tonuri de gri
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    # Convertire de la tonuri de gri la formatul folosit la afisarea pe ecran (RGB)
                    rgbImage = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
                    
                elif( self.currentCameraView == 'hsv' ):
                    # Convertire imagine din color (BGR) in spatiul de culoare HSV (Hue, Saturation, Value)
                    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    rgbImage[:,:,0], rgbImage[:,:,1], rgbImage[:,:,2] = hsv[:,:,2], hsv[:,:,1], hsv[:,:,0]
                    
                elif( self.currentCameraView == 'lineview' ):
                    # Extragerea muchiilor (liniilor) dintr-o imagine folosind algoritmul Canny
                    canny = cv2.Canny(frame, 50, 200, None, 3)
                    rgbImage = cv2.cvtColor(canny, cv2.COLOR_GRAY2BGR)
                    
                elif(self.currentCameraView == 'haar' ):
                    # Initializare clasificator pentru detectia fetei
                    haar_cascade = cv2.CascadeClassifier('Haarcascade_frontalface_default.xml')
                    gray_img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    # Detectare fata in imaginea in tonuri de gri
                    faces_rect = haar_cascade.detectMultiScale(gray_img, 1.1, 9)
                    # Desenarea pe imaginea initiala a patratelor care incadreaza fetele detectare
                    for (x, y, w, h) in faces_rect:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                elif( self.currentCameraView == 'stop' ):
                    break
                
                h, w, ch = rgbImage.shape
                bytesPerLine = ch * w
                # Convertire la formatul necesar obiectului de tip QImage, trimis printr-un semnal 
                convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
                p = convertToQtFormat.scaled(width//2-200, height//2-200, Qt.KeepAspectRatio)
                # Emitere semnal pentru updatare interfata
                self.changePixmap.emit(p)
        # Eliberare si inchidere camera
        cap.release()
    
    # Definirea unui decorator care converteste functia set_option intr-un slot de PyQt
    # mai multe despre decoratori: https://towardsdatascience.com/how-to-use-decorators-in-python-by-example-b398328163b 
    @pyqtSlot(str)
    def set_option(self, option):
        self.currentCameraView = option

# Clasa ferestrei principale
class MainWindow(QMainWindow):
    # Semnal trimis de la aplicatie la thread la schimbarea modului de vizualizare al camerei
    cameraOption = pyqtSignal(str)
  
    # Constructor
    def __init__(self):
        super().__init__()
        
        # Setare titlu fereastra
        self.setWindowTitle("AM Lab 1 - Video Stream")
        
        # Extragere dimensiuni ecran
        self.width = QDesktopWidget().screenGeometry(-1).width()
        self.height = QDesktopWidget().screenGeometry(-1).height()
        
        # Setare dimensiuni ecran proportional cu dimensiunile ecranului
        self.setGeometry(100, 100, self.width//2, self.height//2)
        
        # Crearea unui widget (un obiect de interfata gol) central pentru afisarea camerei
        self.central_widget = QWidget()               
        self.setCentralWidget(self.central_widget)    
        lay = QVBoxLayout(self.central_widget)
        # Crearea unui label pe care vom updata frame-urile camerei
        self.label = QLabel(self)
        # Adaugarea labelului pe widget
        lay.addWidget(self.label)

        # Crearea unei variabile pentru thread si setarea lui ca None (momentan threadul nu a fost creat)
        self.th = None
        #self.button_start = None
        
        # Functie definita mai jos care deseneaza butoanele
        self.UiComponents() 
        
        # Variabila care stocheaza daca a fost trimisă comanda de oprire stream video
        self.streamingStopped = False
        
        # Afisare fereastra principala
        self.show()
    
    # Definirea unui decorator care converteste functia setImage intr-un slot de PyQt    
    @pyqtSlot(QImage)
    def set_image(self, image):
        # Setarea spatiului din label cu imaginea provenita de la thread
        if( self.streamingStopped == False ):
            self.label.setPixmap(QPixmap.fromImage(image))
        
    def UiComponents(self):
        w_align = self.width//2 - 100
        h_align = self.height//15
        w_btn = self.width//15
        h_btn = self.height//20
        
        # Crearea unui buton pentru start
        self.button_start = QPushButton("Start Stream", self)
        # Setare dimenisiuni si asezare buton 
        self.button_start.setGeometry(w_align, h_align, w_btn, h_btn)
        # Adaugare actiune care sa fie executata la apasarea butonului
        self.button_start.clicked.connect(self.start_stream)  
        
        # Crearea unui buton pentru afisarea videoului in tonuri de gri
        self.button_gray = QPushButton("Grayscale Stream", self)
        # Setare dimenisiuni si asezare buton 
        self.button_gray.setGeometry(w_align, 2*h_align, w_btn, h_btn)
        # Adaugare actiune care sa fie executata la apasarea butonului
        self.button_gray.clicked.connect(self.grayscale_stream)
        
        self.button_lines = QPushButton("Lines Stream", self)
        self.button_lines.setGeometry(w_align, 3*h_align, w_btn, h_btn)
        self.button_lines.clicked.connect(self.lines_stream)
        
        self.button_hsv = QPushButton("HSV Stream", self)
        self.button_hsv.setGeometry(w_align, 4*h_align, w_btn, h_btn)
        self.button_hsv.clicked.connect(self.hsv_stream)
        
        self.button_face = QPushButton("Face Detection", self)
        self.button_face.setGeometry(w_align, 5*h_align, w_btn, h_btn)
        self.button_face.clicked.connect(self.face_detection)
        
        # Crearea unui buton pentru inchidere stream video
        self.button_close = QPushButton("Close Stream", self)
        # Setare dimenisiuni si asezare buton 
        self.button_close.setGeometry(w_align, 6*h_align, w_btn, h_btn)
        # Adaugare actiune care sa fie executata la apasarea butonului
        self.button_close.clicked.connect(self.close_camera)
            
    def start_stream(self):
        if( self.th is None ):
            # Crearea unei imagini negre
            new_pix = QPixmap(self.width//2-400, self.height//2-200)
            # Si afisarea pana in momentul in care camera este deschisa si se afiseaza streamul
            # deoarece actiunea de deschidere a camerei poate dura cateva secunde
            self.label.setPixmap(new_pix)
            
            # Instantirea threadului de citire camera
            self.th = Thread(self)
            # Conectarea semnalului changePixmap din thread la metoda set_image din clasa MainWindow
            self.th.changePixmap.connect(self.set_image)
            # Conectarea semnalului cameraOption din clasa MainWindow la metoda set_option din thread
            self.cameraOption.connect(self.th.set_option)
            # Pornire thread
            self.th.start()
            # Schimbare text pe butonul de start
            self.button_start.setText("RGB Stream")
        else:
            self.cameraOption.emit('normal')
        self.streamingStopped = False
    
    def grayscale_stream( self ):
        self.cameraOption.emit('grayscale')
    
    #TODO:
    def face_detection( self ):
        self.cameraOption.emit('haar')
        #print("La thread trebuie trimis semnal pentru detectare fata")
        
    #TODO:
    def lines_stream( self ):
        self.cameraOption.emit('lineview')
        #print("La thread trebuie trimis semnal pentru vizualizare muchii")
        
    #TODO:
    def hsv_stream( self ):
        self.cameraOption.emit('hsv')
        #print("La thread trebuie trimis semnal pentru vizualizare in spatiu de culoare HSV")
        
    def close_camera( self ):
        # Emitere semnal de oprire si inchidere camera
        self.cameraOption.emit('stop')
        # Schimbare text pe butonul de start
        self.button_start.setText("Start Stream")
        # Oprirea threadului, daca acesta a fost creat
        if( self.th is not None ):
            self.th.exit()
            self.th = None
        self.streamingStopped = True
        
        # Afisarea unui pixmap gol atunci cand se opreste streamul
        # Deoarece terminarea threadului si inchiderea camerei nu se produc instant
        new_pix = QPixmap(self.width//2-200, self.height//2-200)
        # Setarea pixmap-ului ca transparent
        new_pix.fill(Qt.transparent)
        self.label.setPixmap(new_pix)
        
# Cod principal
if __name__ == "__main__" :
    # Crearea unei aplicatii in PyQt5
    App = QApplication(sys.argv)
  
    # Crearea unei instante a clasei definite mai sus
    window = MainWindow()
    
    # Executarea aplicatiei, afisarea ferestrei
    App.exec_() 
    
    # Terminarea aplicatiei atunci cand este apasat butonul X
    App.quit() 
    
    # Inchiderea stream-ului video si al camerei
    window.close_camera()
