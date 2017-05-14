# -*- coding: utf-8 -*-
"""
Created on Sun Aug 02 09:53:27 2015

@author: olive
"""
import wx

from config import *

class Show(wx.Panel):
    def __init__(self,parent,gui,core):
        self.core = core
        cfg = Config(core)
        self.dialogs = cfg.dialogs
        wx.Panel.__init__(self,gui,-1) #,size=(-1,300))
        self.panelSizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self,-1,'Results')
        title.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.panelSizer.Add(title,0)
        self.panelSizer.AddSpacer((0,10), 0)
        self.parent,self.gui,self.icons,self.groups = parent,gui,gui.icons,parent.groups
        self.makeBox()
        self.panelSizer.SetMinSize((-1,544))
        self.SetSizer(self.panelSizer)
        self.onSetItem('Model','Plane','L','Z')
        
    def makeBox(self):
        self.numCtrl = 200;#self.swiImg=self.parent.swiImg;
        grdSizer = wx.FlexGridSizer(1,3,vgap=2,hgap=3)
        self.icOri=wx.BitmapButton(self,-1,self.icons['Vis_OriZ'],size=(60,25))
        self.icSwiImg=wx.BitmapButton(self,-1,self.icons['Vis_SwiCont'],size=(25,25))
        grdSizer.Add(self.icOri,0);grdSizer.Add(self.icSwiImg,0)
        self.panelSizer.Add(grdSizer,0)
        self.panelSizer.AddSpacer((0,6), 0)
        self.dictBox={}
        for ig in range(len(self.groups)): 
            for g0 in self.groups: #pour ordonner
                if self.groups[g0][0]==ig: g=g0
            self.dictBox[g] = wxBox(self,g,ig)
            self.panelSizer.Add(self.dictBox[g])#,0,wx.EXPAND)
            self.panelSizer.AddSpacer((0, 2), 0)
        self.panelSizer.Add(wx.StaticText(self,-1,' '),1,wx.EXPAND)
        self.Bind(wx.EVT_BUTTON,self.switchImg,self.icSwiImg)
        
    def OnClick(self,evt):
        """action when a box is clicked, tag L : list """
        item = self.FindWindowById(evt.GetId())
        n = item.GetName(); #getName ou getLabelText
        [group,name,tag]=n.split('_');#print 'guish onclick',group,name,tag
        if tag=='L': 
            if name in ['Layer','Tstep']: 
                retour = item.GetCurrentSelection()
            else :
                retour = item.GetStringSelection() # case of list, retour is the name
        else: retour = evt.Checked() # a check box retour is True or False 
        if name in self.parent.Vtypes['Array']: self.parent.resetDicContour()
        self.parent.dicVisu[group][name]=retour
        nz,ny,nx = shape(self.core.Zblock)
        if name == 'Plane': 
            exec('self.parent.'+name+'=\"'+str(retour)+'\"')
            self.changeIcOri(retour)
            if retour =='Z' : self.setNames('Model_Layer_L',range(nz-1))
            if retour =='Y' : self.setNames('Model_Layer_L',range(ny-1))
            if retour =='X' : self.setNames('Model_Layer_L',range(nx-1))
            self.parent.dicVisu['Model']['Layer']=0
        self.parent.onClick2(group,name,retour)
        
    def changeIcOri(self,ori):
        if ori=='Z':self.icOri.SetBitmapLabel(self.icons['Vis_OriZ'])
        if ori=='X':self.icOri.SetBitmapLabel(self.icons['Vis_OriX'])
        if ori=='Y':self.icOri.SetBitmapLabel(self.icons['Vis_OriY'])

    def switchImg(self,evt):
        if self.parent.swiImg=='Contour':
            self.icSwiImg.SetBitmapLabel(self.icons['Vis_SwiImg'])
            self.parent.swiImg='Image'
        else :
            self.icSwiImg.SetBitmapLabel(self.icons['Vis_SwiCont'])
            self.parent.swiImg='Contour'
        
    def uncheckContours(self):
        """used to uncheck the other contours when group is changed"""
        dic = self.parent.dicVisu
        for n,m in [('Flow','Head'),('Flow','Wcontent'),('Transport','Tracer')]:
            self.onTickBox(n,m,'B',dic[n][m])
        
    def OnChange(self,evt):
        """ change caracteristics of an object"""
        item = self.FindWindowById(evt.GetId());n = item.GetName(); #getName ou getLabelText
        [group,name,tag]=n.split('_')
        change = self.parent.change
        item2=self.FindWindowByName(group+'_'+name+'_L');
        if item2 != None: name=item2.GetStringSelection()
        color = self.parent.getGlist(group,name)['color']
        value = self.parent.getGlist(group,name)['value']
        if name in change.keys(): # cas autres que contours
            if color == None : color = wx.Color(0,0,0)
            lst0=[(name,'Color',color)]
            if change[name] != None:
                lst0.append((change[name][0],'Text',change[name][1]))
            dialg = self.dialogs.genericDialog(self.gui,name,lst0)
            lst1 = dialg.getValues()
            if lst1 != None:
                color = lst1[0]
                if len(lst1)>1: value=lst1[1]
            else : return
        else: # cas contour
            dlgContour = self.dialogs.dialogContour(self.gui, "Contours",value,color)
            if dlgContour.ShowModal() == wx.ID_OK:
                value = dlgContour.GetStrings()
                # create color vector
                c = dlgContour.coul;
                color=[(c[0].Red(),c[0].Green(),c[0].Blue()),(c[1].Red(),c[1].Green(),c[1].Blue()),
                     (c[2].Red(),c[2].Green(),c[2].Blue()),int(c[3])];#print 'in change',color
            else : return
        self.parent.setGlistParm(group,name,'value',value)
        self.parent.setGlistParm(group,name,'color',color)
        self.onTickBox(group,name,tag,True)
        self.parent.visu.changeObject(group,name,value,color)
        
    def boxVisible(self,nameBox,bool):
        if nameBox in self.dictBox.keys():
            box=self.dictBox[nameBox];
            box.Show(bool);box.Enable(bool);
            box.Layout();self.panelSizer.Layout()
    def boutonVisible(self,nameBut,bool):
        item = self.FindWindowByName(nameBut);item.Enable(bool)
        
    def onSetItem(self,group,name,tag,bool):
        """to set an item in a specific state from outside"""
        item=self.FindWindowByName(group+'_'+name+'_'+tag);
        if tag=='B':
            item.SetValue(bool)
            self.parent.dicVisu[group][name]=bool
            self.parent.onClick2(group,name,bool)

    def onTickBox(self,group,name,tag,bool):
        """ pour mettre a jour un bouton sans faire l'action corresp"""
        item=self.FindWindowByName(group+'_'+name+'_'+tag);
        if tag=='B': item.SetValue(bool)
            
    def getCurrentTime(self):
        item = self.FindWindowByName('Model_Tstep_L')
        return item.GetStringSelection()

    def getNames(self,nameBoite):
        item = self.FindWindowByName(nameBoite);
        return item.GetItems()
        
    def setNames(self,nameBoite,names,opt='strings'):
        item = self.FindWindowByName(nameBoite)
        item.Clear()
        if opt=='numbers': # added 23/3/17
            for n in names: item.Append('%.6g' % (n,))
        else :
            for n in names: item.Append(str(n))        

    def getIndexInList(self,nameBoite):
        item = self.FindWindowByName(nameBoite);#print item.GetString()
        return item.GetCurrentSelection()
    def setListPos0(self,nameBoite):
        item = self.FindWindowByName(nameBoite);
        item.SetSelection(0);

class wxBox(wx.Panel):
    def __init__(self,parent,gr,ig):
        wx.Panel.__init__(self,parent,-1) #,size=(-1,300))
        bxSizer=wx.StaticBoxSizer(wx.StaticBox(self, -1, str(ig+1)+'.'+gr), wx.VERTICAL)
        Ctrl = parent.groups[gr][1:]
        grdSizer = wx.FlexGridSizer(len(Ctrl),3,vgap=3,hgap=3)
        for n in Ctrl:
            if type(n)==type([1,2]): #cas liste -> choix
                name = gr+'_'+n[0]+'_L';
                text = wx.StaticText(self, -1, n[0])
                grdSizer.Add(text,0)
                liste = n[1]
                choix = wx.Choice(self, parent.numCtrl, choices=liste, name=name)
                grdSizer.Add(choix, 0)
                wx.EVT_CHOICE(self, parent.numCtrl, parent.OnClick)        
            else : # cas simple : checkbox
                name = gr+'_'+n+'_B';
                text = wx.StaticText(self, -1, n)
                grdSizer.Add(text, 0)
                chk = wx.CheckBox(self, parent.numCtrl, "",name=name)
                grdSizer.Add(chk, 0)
                wx.EVT_CHECKBOX(self, parent.numCtrl, parent.OnClick)
            but = wx.Button(self, parent.numCtrl+1,"C",name=name[:-2]+'_C',size=(16,16))
            grdSizer.Add(but, 0,wx.ALIGN_LEFT)
            wx.EVT_BUTTON(self, parent.numCtrl+1, parent.OnChange)
            if n in ['Map','Visible','Type','Zone']:but.Enable(False)
            if n[0] in ['Plane','Layer','Tstep','Units']:but.Enable(False)
            parent.numCtrl += 2
        bxSizer.Add(grdSizer, 0, wx.ALIGN_CENTER)
        self.SetSizer(bxSizer)
