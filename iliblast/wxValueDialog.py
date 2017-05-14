import os,wx
                            
class wxValueDialog(wx.Dialog):
    """This is a class that creates a dialog for the model parameters, presented
    in groups by testing conditions 
    """
    def __init__(self,parent,gui,core,modName):
        self.parent,self.modName = parent,modName
        wx.Dialog.__init__(self,gui,-1,size=(320,500))
        grpList = core.getUsedModulesList(modName)
        self.chgroups = wx.Choice(self,-1,choices=grpList)
        self.Bind(wx.EVT_CHOICE,self.onChoiceGroup,self.chgroups)
        self.chlines = wx.Choice(self,-1,choices=[''])
        self.Bind(wx.EVT_CHOICE,self.onChoiceLine,self.chlines)
        self.boxkeys = wxBoxKeys(self)
        frameSizer = wx.BoxSizer(wx.VERTICAL)

        frameSizer.Add(self.chgroups, 5, wx.EXPAND)
        frameSizer.Add(self.chlines, 5, wx.EXPAND)
        frameSizer.Add(self.boxkeys, 50, wx.EXPAND)
        #frameSizer.SetSizeHints(self)
        self.SetSizer(frameSizer)
        #self.Bind(wx.EVT_SIZE, self.onSize)

    def onChoiceGroup(self,evt):
        item = self.FindWindowById(evt.GetId())
        n = item.GetStringSelection()
        self.parent.onChoiceGroup(n)
        
    def onChoiceLine(self,evt):
        item = self.FindWindowById(evt.GetId());
        n = item.GetStringSelection().split('-')[0]; 
        self.parent.onChoiceLine(n)
                    
class wxBoxKeys(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,-1,size=(300,300))
        self.parent,self.modName = parent.parent,parent.modName
        self.bxSizer=wx.BoxSizer(wx.VERTICAL)
        tiSizer=wx.BoxSizer(wx.VERTICAL)
        self.title= wx.StaticText(self,-1,' ')
        tiSizer.Add(self.title,0)
        self.grdSizer = wx.FlexGridSizer(8,2,vgap=0,hgap=5)
        butSizer = wx.FlexGridSizer(1,2,vgap=0,hgap=5)
        self.butApply=wx.Button(self,-1,'Apply')
        self.Bind(wx.EVT_BUTTON,self.parent.OnSetNewVal,self.butApply)
        butClose=wx.Button(self,-1,'Close')
        self.Bind(wx.EVT_BUTTON,self.onExit,butClose)
        butSizer.AddMany([(self.butApply,0),(butClose,0)])
        #tunits=wx.StaticText(self,-1,' ')
        self.bxSizer.AddMany([(tiSizer,0),(self.grdSizer,0),(butSizer,0)])
        self.bxSizer.SetSizeHints(self)
        self.SetSizerAndFit(self.bxSizer)
        #self.layout()
        
    def addButtons(self,names,values,details,types):
        """it adds the new buttons after the user has clicked a choice"""
        self.lValBut=[];self.types=types*1;nb=len(names)#;print 'valudlg addb',types
        self.values=values
        self.grdSizer.DeleteWindows();self.grdSizer.Clear()
        self.grdSizer.SetCols(2)
        self.grdSizer.SetRows(nb)
        self.flagADV = False
        #print names,values,details
        for i in range(nb):
            if i>=len(values):values.append(0)
            bname,btype,bcontent,bselect=self.parent.makeButton(names[i],values[i],details[i],types[i])
            if bname[:6]=='MIXELM': 
                self.flagADV=True; bselect +=1
            if btype == 'choice': 
                but = wx.Choice(self,-1,choices=bcontent)
                but.SetSelection(bselect)
                self.types[i] = 'choice'
            elif btype == 'textlong':
                but = wx.TextCtrl(self,-1,bcontent,style=wx.TE_MULTILINE)
            else :
                but = wx.TextCtrl(self,-1,bcontent)
                    
            txtZ = wx.StaticText(self, -1, bname)
            if names[i].split('(')[0] in self.parent.blind: 
                but.Enable(False)
            self.grdSizer.Add(txtZ, 0)
            self.lValBut.append(but)
            self.grdSizer.Add(but,0)
        self.butApply.Enable(True)
        self.Layout()

    def getValues(self):
        nb=len(self.lValBut)
        for i in range(nb):
            but = self.lValBut[i]
            val = self.values[i]*1
            #print 'vadialog', self.types[i]
            if self.types[i]=='choice':
                self.values[i]=but.GetSelection()
                if self.flagADV : self.values[i]-=1
                continue
            if self.types[i] in ['int','vecint','arrint','layint']:
                val=int(but.GetValue())
            elif self.types[i] in ['float','vecfloat','arrfloat','layfloat']:
                val=float(but.GetValue())
            else :  
                val=but.GetValue()
            self.values[i]=val
        return self.values
        
    def onExit(self,evt):
        self.parent.dialg.Destroy()
