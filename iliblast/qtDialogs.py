# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_file.ui'
#
# Created: Sat Feb 15 15:09:21 2014
#      by: PyQt4 UI code generator 4.8.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4.QtCore import *
from PyQt4.QtGui import *

def onMessage(gui,text):  QMessageBox.information(gui,"Info",text)
def onQuestion(gui,text):  QMessageBox.information(gui,"Info",text)

class textDialog(QDialog):
    def __init__(self,gui, title, tsize, text):
        QDialog.__init__(self)
        self.setWindowTitle(title)
        self.glWidget = QWidget(self)
        self.glWidget.setGeometry(QRect(5, 5, tsize[0],tsize[1]))
        scrollArea = QScrollArea(self.glWidget)
        self.txed = QTextEdit(scrollArea)
        self.txed.setText(text)
        scrollArea.setWidget(self.txed)                
        QMetaObject.connectSlotsByName(self)

    def showDialogAndDisconnect(self):
        self.show()
        self.gui.actionToggleEditing().triggered.disconnect(self.showDialogAndDisconnect)

    def getText(self):
        return self.txed.document().toPlainText()
        
class genericDialog(QDialog):
    def __init__(self, gui, title, data):
        self.gui,self.data = gui,data
        QDialog.__init__(self)
        self.setWindowTitle("Generic")
        self.glWidget = QWidget(self)
        nb = len(self.data)
        self.glWidget.setGeometry(QRect(5, 5, 200, nb*30+100))
        #self.glWidget.setObjectName(_fromUtf8("gridLayoutWidget"))
        self.gl = QGridLayout(self.glWidget)
        i=0;
        self.item = range(nb)
        for name,typ,value in self.data:
            y0=10+i*20
            txt = QLabel(self.glWidget)
            txt.setText(name) 
            self.gl.addWidget(txt,i,0,1,1)
            if typ == 'Choice':
                self.item[i] = QComboBox(self.glWidget)
                chlist = value[1];
                j=0
                for n in chlist:
                    self.item[i].addItem("")
                    self.item[i].setItemText(j,n)
                    j+=1
                self.item[i].setCurrentIndex(value[1].index(value[0]))
                self.gl.addWidget(self.item[i],i,1,1,1)
            elif typ=='Text':
                self.item[i] = QLineEdit(self.glWidget)
                #self.item[i].setGeometry(QRect(50, y0, 100, 20))
                self.item[i].setText(str(value))
                self.gl.addWidget(self.item[i],i,1,1,1)
            elif typ=='Textlong':
                scrollArea = QScrollArea(self.glWidget)
                scrollArea.setGeometry(QRect(50, y0, 100, 50))
                self.item[i] = QTextEdit(scrollArea)
                y0 += 30
                if type(value)==type([5,6]): 
                    value = '\n'.join([str(v) for v in value]) # cretaes a text with line returns
                self.item[i].setText(str(value))
                scrollArea.setWidget(self.item[i])                
                self.gl.addWidget(scrollArea,i,1,1,1)

            i+=1
        self.buttonBox = QDialogButtonBox(self)
        #self.buttonBox.setGeometry(QRect(10, y0+50, 120, 32))
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.glWidget2 = QWidget(self)
        self.glWidget2.setGeometry(QRect(5, nb*30+100, 200, 40))
        self.gl2 = QGridLayout(self.glWidget2)
        self.gl2.setMargin(0)
        self.gl2.addWidget(self.buttonBox) #,nb,1,2,1)
        #self.QTabWidget.setCurrentIndex(0)
        QObject.connect(self.buttonBox, SIGNAL("accepted()"), self.accept)
        QObject.connect(self.buttonBox, SIGNAL("rejected()"), self.reject)
        QMetaObject.connectSlotsByName(self)

    def showDialogAndDisconnect(self):
        self.show()
        self.gui.actionToggleEditing().triggered.disconnect(self.showDialogAndDisconnect)

    def getValues(self):
        self.exec_()
        nb = len(self.data)
        val = range(nb)
        for i in range(nb):
            typ = self.data[i][1]
            if typ == 'Choice': val[i] = self.item[i].currentText()
            if typ == 'Text': val[i] = self.item[i].text()
            if typ == 'Textlong': 
                v0 = self.item[i].document().toPlainText()
                val[i] = v0.split('\n')            
        return val
        
class myFileDialog:
    def __init__(self):
        a = 3 #dummy 
    def getFile(self,gui,evt,title,filt):
        fileName = QFileDialog.getOpenFileName(gui,title,filter=filt)
        fName = fileName.split('/')[-1]
        fDir = fileName.replace(fName,'')
        fName = fName.split('.')[0]
        return fDir,fName

class myNoteBook(QDialog):
    def __init__(self, gui,title, dicIn):
        QDialog.__init__(self)
        self.pages,self.dicIn ={},dicIn
        self.glWidget = QWidget(self)
        self.glWidget.setGeometry(QRect(5, 5, 450,400))
        nb = QTabWidget(self.glWidget)
        for n in dicIn.keys():
            if dicIn[n]==None:continue
            if len(dicIn[n]['rows'])==0 and n!='Species': continue
            pg=myNBpanelGrid(nb,dicIn[n])
            self.pages[n]=pg
            nb.addTab(pg,n)
            pg.show()
        QMetaObject.connectSlotsByName(self)
        
    def showDialogAndDisconnect(self):
        self.show()
        self.gui.actionToggleEditing().triggered.disconnect(self.showDialogAndDisconnect)
            
    def getValues(self):
        self.exec_()
        return None
            
class myNBpanelGrid(QTableWidget):       
    def __init__(self, parentWidget,data):
        QTableWidget.__init__(self,5,3)
        self.data = data
        self.setmydata()
        QMetaObject.connectSlotsByName(self)
        
    def setmydata(self):
        n = 0
        for i,line in enumerate(self.data['data']):
            m = 0
            for item in line:
                self.setItem(m, n, QTableWidgetItem(item))
                m += 1
            n += 1
