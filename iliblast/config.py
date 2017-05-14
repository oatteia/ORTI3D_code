# -*- coding: utf-8 -*-
"""
Created on Sun Dec 15 20:53:49 2013

@author: olive
"""
from scipy import arctan,exp,log,log10,ones,concatenate,cumsum,linspace,logspace,sqrt,\
    amax,amin,maximum,meshgrid,nonzero,equal,reshape,array,where,zeros,ravel,rand,\
    arange,unique,sign,clip,sort,argsort,put,take,putmask,mean,shape,median,mod,\
    argmin,transpose,c_,r_,sum,savetxt,zeros_like,dot

import matplotlib.tri as mptri
from numpy.linalg import solve
import warnings,os
warnings.filterwarnings("ignore")

class Config():
    def __init__(self,core):
        if core.gui != None :
            if core.gui.gtyp=='wx':
                    import wxDialogs,wxShow,wxValueDialog
                    self.dialogs,self.show,self.valDlg = wxDialogs,wxShow,wxValueDialog
                    self.gtyp = 'wx'
            elif core.gui.gtyp=='qt':
                import qtDialogs,qtValueDialog
                self.dialogs,self.valDlg = qtDialogs,qtValueDialog
                self.gtyp = 'qt'
        lfi=os.listdir(core.gui.mainDir) # oa 29/3/17
        if 'ilibq' in lfi: self.typInstall = 'python' # oa 29/3/17
        else : self.typInstall = 'exe' # oa 29/3/17
