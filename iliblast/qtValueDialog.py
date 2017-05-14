# -*- coding: utf-8 -*-
"""
Created on Sun Aug 02 10:22:05 2015

@author: olive
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
        
class qtValueDialog(QDialog):
    def __init__(self, parent,gui,core,modName):
        QDialog.__init__(self)
        self.parent = parent
        self.setWindowTitle('hello')
        layoutWidget = QWidget(self)
        layoutWidget.setGeometry(QRect(5, 5, 200,400))
        self.vbox = QVBoxLayout(layoutWidget)
        self.vbox.setGeometry(QRect(0, 0, 180,60))
        grpList = core.getUsedModulesList(modName)
        self.chgroups = QComboBox(layoutWidget)
        for i,n in enumerate(grpList):
            self.chgroups.addItem("")
            self.chgroups.setItemText(i, n)
        self.chgroups.activated['QString'].connect(self.onChoiceGroup)
        self.vbox.addWidget(self.chgroups)
        self.chlines = QComboBox(layoutWidget)
        self.chlines.activated['QString'].connect(self.onChoiceLine)
        self.vbox.addWidget(self.chlines)
        #self.vbox2 = QVBoxLayout(layoutWidget)
        #self.vbox2.setGeometry(QRect(0, 60, 180,340))
        self.boxkeys = qtBoxKeys(self,parent)
        
        QMetaObject.connectSlotsByName(self)
        
    def onChoiceGroup(self,value): self.parent.onChoiceGroup(value)
    def onChoiceLine(self,value): self.parent.onChoiceLine(value)   
     
class qtBoxKeys:
    def __init__(self,Main,parent):
        self.Main,self.parent = Main,parent
        self.layoutWidget = QWidget(Main)
        self.gridLayout = QGridLayout(self.layoutWidget)
        bBox = QDialogButtonBox(self.layoutWidget)
        bBox.setOrientation(Qt.Horizontal)
        bBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        QObject.connect(bBox, SIGNAL("accepted()"), parent.OnSetNewVal)
        gl0 = QGridLayout(self.layoutWidget)
        #gl0.setGeometry(QRect(0,60,180,40))
        gl0.addWidget(bBox)
        #self.gridLayout.setGeometry(QRect(0,100,180,300))
        Main.vbox.addWidget(self.layoutWidget)
        self.labl,self.lValBut,self.values=[],[],[]
        
    def setVisible(self,bool):self.layoutWidget.setVisible(bool)
        
    def addButtons(self,names,values,details,types):
        self.values,self.types = values,types;
        nb=len(names);
        # clear the layout
        for b in self.labl: b.deleteLater()
        for b in self.lValBut: b.deleteLater()
        self.labl,self.lValBut=[],[];
        #self.parent.gui.onMessage(str(names)+' '+str(values)+' '+str(details))
        
        for i in range(nb):
            bname,btype,bcontent,bselect=self.parent.makeButton(names[i],values[i],details[i],types[i])
            txt = QLabel(self.layoutWidget)
            txt.setText(bname)
            if btype == 'choice': 
                but = QComboBox(self.layoutWidget)
                but.addItems(bcontent)
                but.setCurrentIndex(bselect)
            #elif btype == 'text':
            else :
                but = QLineEdit(self.layoutWidget)
                but.setText(str(bcontent))
                    
            self.labl.append(txt)
            self.gridLayout.addWidget(txt, i,0,1,1)
            self.lValBut.append(but)
            self.gridLayout.addWidget(but,i,1,1,1)
            
    def getValues(self):
        nb=len(self.values)
        for i in range(nb):
            but=self.lValBut[i]
            val = self.values[i]
            if self.types[i]=='choice':
                self.values[i]=but.currentIndex()
                continue
            if but.text() not in ['formula','zone','array']:
                if self.types[i] in ['int','vecint','arrint']:
                    val=int(but.text())
                elif self.types[i] in ['float','vecfloat','arrfloat']:
                    val=float(but.text())
            else :  val=but.text()
            self.values[i]=val*1
        return self.values
