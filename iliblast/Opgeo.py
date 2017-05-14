# -*- coding: utf-8 -*-
"""
Created on Wed Aug 26 21:52:19 2015

@author: olive
"""
from geometry import *
import matplotlib.tri as mptri
import os

class Opgeo:
    
    def __init__(self, core):
        self.core = core
        
    def buildMesh(self,nlay=1):
        if self.core.dicval['OpgeoFlow']['domn.1'][0]==0: 
            nx,ny,xv,yv = getXYvects(self.core)
            self.nel = nx*ny
            self.nnod = (nx+1)*(ny+1)
            return None # rectangular
        dct = self.core.diczone['OpgeoFlow'].dic
        dicD = dct['domn.4']
        if dct.has_key('flow.5'): dicK = dct['flow.5'] # K hydraul
        else : dicK = {'name':[]}
        s = gmeshString(dicD,dicK)
        os.chdir(self.core.fileDir)
        f1 = open('gm_in.txt','w');f1.write(s);f1.close()
        bindir = self.core.baseDir+os.sep+'bin'+os.sep
        os.system(bindir+'gmsh gm_in.txt -2 -o gm_out.msh')
        #os.chdir(self.core.fileDir)
        f1 = open('gm_out.msh','r');a = f1.read();f1.close()
        # nodes
        b = a.split('$Nodes')[1]
        c = b.split('$EndNodes')[0]
        c1 = c.split('\n')
        self.nnod = int(c1[1])        
        c2 = [x.split() for x in c1[2:-1]];#print len(c2)
        arr = array(c2,dtype='float')
        arr[:,0] = arr[:,0]-1 # node number start from 0
        self.nodes = arr
        s1 = self.arr2string(arr)
        self.nodestring = s1.replace('.  ','  ')
        # elements
        b = a.split('$Elements')[1];#print len(b)
        c = b.split('$EndElements')[0];#print len(c)
        c1 = c.split('\n')
        c2 = [x.split() for x in c1[2:] if len(x.split())==8];#print len(c2)
        arr = array(c2,dtype='int');#print 'ogModel 48',arr
        arr = arr-1
        arr = arr[:,[0,3,4,5,6,7]] # 2nd column is useless
        nel,nc = shape(arr)
        arr[:,0]=arange(nel)
        arr[:,1]=arr[:,2] # this is the material number, which starts from 1 in gmsh and 0 in opgeo
        self.nel = nel
        self.elements = arr
        arr[:,2] = -100 # before the nodes number
        s = self.arr2string(arr)
        s = s.replace('-100',' -1 tri')
        self.elementstring = s
                # get the triangulation
        xnds,ynds = self.nodes[:,1],self.nodes[:,2]
        trg = mptri.Triangulation(xnds,ynds,triangles=arr[:,-3:]) # be careful the numbering can be differnet from gmesh
        self.trg = trg
        nel = len(trg.triangles)
        self.elx = trg.x[trg.triangles]
        self.ely = trg.y[trg.triangles]
        self.elcenters = zeros((nel,2))
        self.elcenters[:,0] = mean(self.elx,axis=1)
        self.elcenters[:,1] = mean(self.ely,axis=1)
        return 
        
    def getCellCenters(self):    
        if self.core.dicval['OpgeoFlow']['domn.1'][0]==0:
            return getXYmeshCenters(self.core,'Z',0)
        else :
            return self.elcenters
            
    def getNumberOfCells(self):
        return self.nel
            
    def arr2string(self,arr):
        s=''
        nr,nc = shape(arr)
        for i in range(nr):
            s += str(int(arr[i,0]))+' '
            for j in range(1,nc):
                s += str(arr[i,j])+' '
            s += '\n'
        return s