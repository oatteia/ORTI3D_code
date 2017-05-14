# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 23:43:54 2014

@author: olive
"""
from geometry import *


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from PyQt4 import *

class qtVisu:
    def __init__(self,iface,gui,core):
        self.iface, self.gui,self.core = iface,gui,core
        self.canvas = self.iface.mapCanvas()
        
    def clearLayers(self):
        """clear all laysers, used when opening a new model"""
        allLayers = self.canvas.layers()
        for layer in allLayers:
            QgsMapLayerRegistry.instance().removeMapLayer(layer)
        
    def initDomain(self): 
        """initalize the grid and all cells in Qgis"""
        allLayers = self.canvas.layers()
        layer = QgsVectorLayer("Polygon", 'Grid',  "memory")
        QgsMapLayerRegistry.instance().addMapLayer(layer)
        layer.startEditing()
        provider = layer.dataProvider()
        provider.addAttributes( [QgsField("id", QVariant.Int) ] )
        provider.addAttributes( [QgsField("value", QVariant.Double) ] )
        layer.commitChanges()

        g = self.core.addin.getFullGrid()
        a,count = g['x0'],0
        for i in range(g['nx']):
            b,c = g['y0'],g['dx'][i]
            for j in range(g['ny']):
                d =  g['dy'][j]
                lcoord=[QgsPoint(a,b),QgsPoint(a+c,b),QgsPoint(a+c,b+d),QgsPoint(a,b+d)]
                feat = QgsFeature();
                feat.setGeometry(QgsGeometry.fromPolygon([lcoord]));
                feat.setAttributes([count,0.])
                provider.addFeatures([feat]);
                b += d
                count += 1
            a += c
        layer.updateExtents()
        layer.commitChanges()
        
    def createAndShowObject(self,dataM,dataV,opt,value,color):
        """create the object and show it, typObj in Grid,Contour, Vector, Map
        """
        #self.gui.dialogs.onMessage(self.gui,dataM)
        if dataM == None : self.drawContour(False)
        else : 
            if self.gui.guiShow.swiImg == 'Contour':
                self.createContour(dataM,value,color)
            else : 
                self.createImage(dataM)
        if dataV == None : self.drawVector(False)
        else : self.createVector(dataV)
                        
    def drawObject(self,typObj,bool):
        exec('self.draw'+typObj+'('+str(bool)+')')
        
    def createLayer(self,line):
        """create one new layer from a line"""
        ptlist=['lpf.8','wel.1','btn.11']
        allLayers = self.canvas.layers();#print allLayers
        # finds the dickword of the current line
        for modName in self.core.modelList:
            if line in self.core.dickword[modName].lines.keys():
                dick = self.core.dickword[modName]
                break
        if line in ptlist: typList=[('Linestring','line'),('Point','pts')]
        else : typList=[('Linestring','line')]
        comm = dick.lines[line]['comm'][:25]
        layerList = []
        for ptyp in typList:
            layerName = line + '_'+ptyp[1]+' ' + comm
            # search if the layer already exists, if yes, returns it
            for layer in allLayers:
                if layer.name() == layerName : return [layer]
            # creating the layer
            if len(allLayers)>0:
                crs = allLayers[0].crs()# finds the coordinates system
                layer = QgsVectorLayer(ptyp[0]+"?crs=" + crs.authid(), layerName, "memory") # "delimitedtext")
            else:
                layer = QgsVectorLayer(ptyp[0], layerName, "memory") # "delimitedtext")
            QgsMapLayerRegistry.instance().addMapLayer(layer)
            layer.startEditing()
            layer.dataProvider().addAttributes( [QgsField("id", QVariant.Int) ] )
            layer.dataProvider().addAttributes( [QgsField("name", QVariant.String) ] )
            layer.dataProvider().addAttributes( [QgsField("value", QVariant.Double) ] )
            layer.dataProvider().addAttributes( [QgsField("media", QVariant.Int) ] )
            layer.commitChanges()
            layerList.append(layer)
        return layerList
        
    def zonesQgs2core(self):
        '''creates zones from existing polys in Qgis layers'''
        allLayers = self.canvas.layers()
        for layer in allLayers:
            if layer.name() == 'Grid' : continue
            line,typP = layer.name().split()[0],'asPolyline()'
            if len(line.split('_'))>0: 
                line,typ0 = line.split('_')
                if typ0=='pts': typP='asPoint()'
            for modName in self.core.modelList:
                if line in self.core.dickword[modName].lines.keys():
                    dicz = self.core.diczone[modName]
                    break
            feats = layer.getFeatures()
            dicz.dic[line]={'number':[],'name':[],'coords':[],'media':[],'value':[],'type':[]}                
            for i,f in enumerate(feats):
                dicz.addZone(line)
                dicz.setValue(line,'value',i,f['value'])
                dicz.setValue(line,'name',i,f['name'])
                dicz.setValue(line,'media',i,f['media'])
                exec('coords = f.geometry().'+typP)
                dicz.setValue(line,'coords',i,coords)
                
    def zonesCore2qgs(self):
        """uses zones stored in core to create and fill the qgis
        layers with layers and features"""
        for modName in self.core.modelList:
            dicz = self.core.diczone[modName]
            lines = dicz.dic.keys()
            for line in lines:
                nz = dicz.getNbZones(line)
                # get layer or layers
                layerList = self.createLayer(line)
                layer = layerList[0]
                provider = layer.dataProvider()
                if len(layerList)>1:
                    layer1 = layerList[1]
                    provider1 = layer1.dataProvider()                    
                # add zones in the layer(s)
                for i in range(nz):
                    coords = dicz.getValue(line,'coords',i)
                    lcoord = []
                    for pt in coords:
                        a=QgsPoint(float(pt[0]),float(pt[1]))
                        lcoord.append(a)
                    feat = QgsFeature()
                    if len(lcoord)==1:
                        feat.setGeometry(QgsGeometry.fromPoint(lcoord[0]));
                    else :
                        feat.setGeometry(QgsGeometry.fromPolyline(lcoord));
                    a = str(dicz.getValue(line,'name',i))
                    b = float(dicz.getValue(line,'value',i))
                    c = int(dicz.getValue(line,'media',i))
                    feat.setAttributes([i,a,b,c])
                    if len(lcoord)==1:
                        provider1.addFeatures([feat]);
                    else :
                        provider.addFeatures([feat]);
                        

    def drawGrid(self,bool) : pass
    def drawImage(self,bool) : pass
    def drawMap(self,bool) : pass
    def drawVector(self,bool) : pass
    def drawContour(self,bool):pass
    def drawParticles(self,bool) : pass

    def createContour(self,data,value,color):
        """creates a coutour or image object using the Grid layer 
        of Qgis"""
        X,Y,Z = data
        ny,nx = shape(Z)
        d0,i = {},0
        for ix in range(nx):
            for iy in range(ny):
                d0[i]={0:i,1:float(Z[iy,ix])}
                i+=1
        allLayers = self.canvas.layers()
        for i,layer in enumerate(allLayers):
            if layer.name()=='Grid': break
        pr = layer.dataProvider();#self.gui.dialogs.onMessage(self.gui,str(layer.name()))
        layer.startEditing()
        pr.changeAttributeValues(d0)
        layer.commitChanges()
