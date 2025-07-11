#!/usr/bin/env python3
# encoding: utf-8
import os
import cv2
import sys
import math
import time
import yaml
import addcolor
from ServoCmd import *
from Ui import Ui_Form
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class MainWindow(QWidget, Ui_Form):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)       
        #################################界面#######################################
        self.resetServos_ = False
        self.path = '/home/pi/TurboPi/'
        self.lab_file = 'lab_config.yaml'
        self.servo_file = 'servo_config.yaml'
        self.color = 'red'
        self.L_Min = 0
        self.A_Min = 0
        self.B_Min = 0
        self.L_Max = 255
        self.A_Max = 255
        self.B_Max = 255
        self.servo1 = 1500
        self.servo2 = 1500
        self.kernel_erode = 3
        self.kernel_dilate = 3
        self.camera_ui = False
        self.camera_ui_break = False
        
        self.horizontalSlider_LMin.valueChanged.connect(lambda: self.horizontalSlider_labvaluechange('lmin'))
        self.horizontalSlider_AMin.valueChanged.connect(lambda: self.horizontalSlider_labvaluechange('amin'))
        self.horizontalSlider_BMin.valueChanged.connect(lambda: self.horizontalSlider_labvaluechange('bmin'))
        self.horizontalSlider_LMax.valueChanged.connect(lambda: self.horizontalSlider_labvaluechange('lmax'))
        self.horizontalSlider_AMax.valueChanged.connect(lambda: self.horizontalSlider_labvaluechange('amax'))
        self.horizontalSlider_BMax.valueChanged.connect(lambda: self.horizontalSlider_labvaluechange('bmax'))
        
        self.horizontalSlider_servo1.valueChanged.connect(lambda: self.horizontalSlider_labvaluechange('servo1'))
        self.horizontalSlider_servo2.valueChanged.connect(lambda: self.horizontalSlider_labvaluechange('servo2'))
        
        self.pushButton_connect.pressed.connect(lambda: self.on_pushButton_action_clicked('connect'))
        self.pushButton_disconnect.pressed.connect(lambda: self.on_pushButton_action_clicked('disconnect'))
        self.pushButton_labWrite.pressed.connect(lambda: self.on_pushButton_action_clicked('labWrite'))
        self.pushButton_save_servo.pressed.connect(lambda: self.on_pushButton_action_clicked('save_servo'))
        self.pushButton_addcolor.clicked.connect(self.addcolor)
        self.pushButton_deletecolor.clicked.connect(self.deletecolor)
               
        self._timer = QTimer()
        self._timer.timeout.connect(self.show_image)
        self.createConfig()
        
        self.current_servo_data = self.get_yaml_data(self.path + self.servo_file)
        
        self.servo1 = int(self.current_servo_data['servo1'])
        self.servo2 = int(self.current_servo_data['servo2'])

        self.horizontalSlider_servo1.setValue(self.servo1)
        self.horizontalSlider_servo2.setValue(self.servo2)
        self.label_servo1_value.setNum(self.servo1)
        self.label_servo2_value.setNum(self.servo2)
        
        setServoPulse(1, self.servo1, 500)
        setServoPulse(2, self.servo2, 500)
        
    # 弹窗提示函数
    def message_from(self, str):
        try:
            QMessageBox.about(self, '', str)
        except:
            pass

    # 窗口退出
    def closeEvent(self, e):        
        result = QMessageBox.question(self,
                                    "Prompt box",
                                    "quit?",
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.No)
        if result == QMessageBox.Yes:
            self.camera_ui = True
            self.camera_ui_break = True
            QWidget.closeEvent(self, e)
        else:
            e.ignore()           

    def message_delect(self, string):
        messageBox = QMessageBox()
        messageBox.setWindowTitle('')
        messageBox.setText(string)
        messageBox.addButton(QPushButton('OK'), QMessageBox.YesRole)
        messageBox.addButton(QPushButton('Cancel'), QMessageBox.NoRole)

        return messageBox.exec_()

    def addcolor(self):
        self.qdi = QDialog()
        self.d = addcolor.Ui_Dialog()
        self.d.setupUi(self.qdi)
        self.qdi.show()
        self.d.pushButton_ok.clicked.connect(self.getcolor)
        self.d.pushButton_cancel.pressed.connect(self.closeqdialog)
    
    def deletecolor(self):
        result = self.message_delect('Delect?')
        if not result:
            self.color = self.comboBox_color.currentText()
            del self.current_lab_data[self.color]
            self.save_yaml_data(self.current_lab_data, self.path + self.lab_file)
            self.comboBox_color.clear()
            self.comboBox_color.addItems(self.current_lab_data.keys())
                
    def getcolor(self):
        color = self.d.lineEdit.text()
        self.comboBox_color.addItem(color)
        time.sleep(0.1)
        self.qdi.accept()
    
    def closeqdialog(self):
        self.qdi.accept()

    ################################################################################################
    #获取面积最大的轮廓
    def getAreaMaxContour(self,contours) :
            contour_area_temp = 0
            contour_area_max = 0
            area_max_contour = None;

            for c in contours :
                contour_area_temp = math.fabs(cv2.contourArea(c)) #计算面积
                if contour_area_temp > contour_area_max : #新面积大于历史最大面积就将新面积设为历史最大面积
                    contour_area_max = contour_area_temp
                    if contour_area_temp > 10: #只有新的历史最大面积大于10,才是有效的最大面积
                                               #就是剔除过小的轮廓
                        area_max_contour = c

            return area_max_contour #返回得到的最大面积，如果没有就是 None

    def show_image(self):
        if self.camera_opened:
            ret, orgframe = self.cap.read()
            if ret:
                orgFrame = cv2.resize(orgframe, (400, 300))
                orgframe_ = cv2.GaussianBlur(orgFrame, (3, 3), 3)
                frame_lab = cv2.cvtColor(orgframe_, cv2.COLOR_BGR2LAB)
                mask = cv2.inRange(frame_lab,
                                   (self.current_lab_data[self.color]['min'][0],
                                    self.current_lab_data[self.color]['min'][1],
                                    self.current_lab_data[self.color]['min'][2]),
                                   (self.current_lab_data[self.color]['max'][0],
                                    self.current_lab_data[self.color]['max'][1],
                                    self.current_lab_data[self.color]['max'][2]))#对原图像和掩模进行位运算
                eroded = cv2.erode(mask, cv2.getStructuringElement(cv2.MORPH_RECT, (self.kernel_erode, self.kernel_erode)))
                dilated = cv2.dilate(eroded, cv2.getStructuringElement(cv2.MORPH_RECT, (self.kernel_dilate, self.kernel_dilate)))
                showImage = QImage(dilated.data, dilated.shape[1], dilated.shape[0], QImage.Format_Indexed8)
                temp_pixmap = QPixmap.fromImage(showImage)
                
                frame_rgb = cv2.cvtColor(orgFrame, cv2.COLOR_BGR2RGB)
                showframe = QImage(frame_rgb.data, frame_rgb.shape[1], frame_rgb.shape[0], QImage.Format_RGB888)
                t_p = QPixmap.fromImage(showframe)
                
                self.label_process.setPixmap(temp_pixmap)
                self.label_orign.setPixmap(t_p)

    def horizontalSlider_labvaluechange(self, name):
        if name == 'lmin': 
            self.current_lab_data[self.color]['min'][0] = self.horizontalSlider_LMin.value()
            self.label_LMin.setNum(self.current_lab_data[self.color]['min'][0])
        if name == 'amin':
            self.current_lab_data[self.color]['min'][1] = self.horizontalSlider_AMin.value()
            self.label_AMin.setNum(self.current_lab_data[self.color]['min'][1])
        if name == 'bmin':
            self.current_lab_data[self.color]['min'][2] = self.horizontalSlider_BMin.value()
            self.label_BMin.setNum(self.current_lab_data[self.color]['min'][2])
        if name == 'lmax':
            self.current_lab_data[self.color]['max'][0] = self.horizontalSlider_LMax.value()
            self.label_LMax.setNum(self.current_lab_data[self.color]['max'][0])
        if name == 'amax':
            self.current_lab_data[self.color]['max'][1] = self.horizontalSlider_AMax.value()
            self.label_AMax.setNum(self.current_lab_data[self.color]['max'][1])
        if name == 'bmax':
            self.current_lab_data[self.color]['max'][2] = self.horizontalSlider_BMax.value()
            self.label_BMax.setNum(self.current_lab_data[self.color]['max'][2])
        if name == 'servo1':
            self.current_servo_data['servo1'] = self.horizontalSlider_servo1.value()
            self.label_servo1_value.setNum(self.current_servo_data['servo1'])
            self.servo1 = int(self.current_servo_data['servo1'])
            setServoPulse(1, int(self.servo1), 20)
        if name == 'servo2':
            self.current_servo_data['servo2'] = self.horizontalSlider_servo2.value()
            self.label_servo2_value.setNum(self.current_servo_data['servo2'])
            self.servo2 = int(self.current_servo_data['servo2'])
            setServoPulse(2, int(self.servo2), 20)
    
    def get_yaml_data(self, yaml_file):
        file = open(yaml_file, 'r', encoding='utf-8')
        file_data = file.read()
        file.close()
        
        data = yaml.load(file_data, Loader=yaml.FullLoader)
        
        return data

    def save_yaml_data(self, data, yaml_file):
        file = open(yaml_file, 'w', encoding='utf-8')
        yaml.dump(data, file)
        file.close()
    
    def createConfig(self):
        if not os.path.isfile(self.path + self.lab_file):          
            data = {'red': {'max': [255, 255, 255], 'min': [0, 150, 130]},
                    'green': {'max': [255, 110, 255], 'min': [47, 0, 135]},
                    'blue': {'max': [255, 136, 120], 'min': [0, 0, 0]},
                    'black': {'max': [89, 255, 255], 'min': [0, 0, 0]},
                    'white': {'max': [255, 255, 255], 'min': [193, 0, 0]}}
            self.save_yaml_data(data, self.path + self.lab_file)
            self.current_lab_data = data
            
            self.color_list = ['red', 'green', 'blue', 'black', 'white']
            self.comboBox_color.addItems(self.color_list)
            self.comboBox_color.currentIndexChanged.connect(self.selectionchange)       
            self.selectionchange()
        else:
            try:
                self.current_lab_data = self.get_yaml_data(self.path + self.lab_file)
                self.color_list = self.current_lab_data.keys()
                self.comboBox_color.addItems(self.color_list)
                self.comboBox_color.currentIndexChanged.connect(self.selectionchange)       
                self.selectionchange() 
            except:
                self.message_from('read error！')
        
        if not os.path.isfile(self.path + self.servo_file):          
            data = {'servo1': 1500,
                    'servo2': 1500}
            self.save_yaml_data(data, self.path + self.servo_file)
                          
    def getColorValue(self, color):  
        if color != '':
            self.current_lab_data = self.get_yaml_data(self.path + self.lab_file)
            if color in self.current_lab_data:
                self.horizontalSlider_LMin.setValue(self.current_lab_data[color]['min'][0])
                self.horizontalSlider_AMin.setValue(self.current_lab_data[color]['min'][1])
                self.horizontalSlider_BMin.setValue(self.current_lab_data[color]['min'][2])
                self.horizontalSlider_LMax.setValue(self.current_lab_data[color]['max'][0])
                self.horizontalSlider_AMax.setValue(self.current_lab_data[color]['max'][1])
                self.horizontalSlider_BMax.setValue(self.current_lab_data[color]['max'][2])
            else:
                self.current_lab_data[color] = {'max': [255, 255, 255], 'min': [0, 0, 0]}
                self.save_yaml_data(self.current_lab_data, self.path + self.lab_file)
                
                self.horizontalSlider_LMin.setValue(0)
                self.horizontalSlider_AMin.setValue(0)
                self.horizontalSlider_BMin.setValue(0)
                self.horizontalSlider_LMax.setValue(255)
                self.horizontalSlider_AMax.setValue(255)
                self.horizontalSlider_BMax.setValue(255)

    def selectionchange(self):
        self.color = self.comboBox_color.currentText()      
        self.getColorValue(self.color)
        
    def on_pushButton_action_clicked(self, buttonName):
        if buttonName == 'labWrite':
            try:              
                self.save_yaml_data(self.current_lab_data, self.path + self.lab_file)
            except Exception as e:
                self.message_from('save failed！')
                return
            self.message_from('save success！')
        elif buttonName == 'save_servo':
            try:               
                self.save_yaml_data(self.current_servo_data, self.path + self.servo_file)
            except Exception as e:
                self.message_from('save failed！')
                return
            self.message_from('save success！')                      
        elif buttonName == 'connect':
            self.cap = cv2.VideoCapture(-1)
            if not self.cap.isOpened():
                self.label_process.setText('Can\'t find camera')
                self.label_orign.setText('Can\'t find camera')
                self.label_process.setAlignment(Qt.AlignCenter|Qt.AlignVCenter)
                self.label_orign.setAlignment(Qt.AlignCenter|Qt.AlignVCenter)
            else:
                self.camera_opened = True
                self._timer.start(20)
        elif buttonName == 'disconnect':
            self.camera_opened = False
            self._timer.stop()
            self.label_process.setText(' ')
            self.label_orign.setText(' ')           
            self.cap.release()

if __name__ == "__main__":  
    app = QApplication(sys.argv)
    myshow = MainWindow()
    myshow.show()
    sys.exit(app.exec_())
