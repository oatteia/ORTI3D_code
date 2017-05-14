import wx
from wxDialogs import *
from parameters import BaseParms

class wxParameters(wx.Panel):

    def __init__(self,gui,core):
        self.gui,self.core, self.addin = gui,core, core.addin
        self.Base = BaseParms(gui,core)
        #self.visu, self.model = gui.visu, model
        self.currentVar, self.currentMil, self.milList = None,0,[]
        wx.Panel.__init__(self,gui,-1) #,size=(-1,300))
        self.panelSizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self,-1,'  Parameters')
        title.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.panelSizer.Add(title,0)
        self.panelSizer.AddSpacer((0,10), 0)
        self.makeBox() #;self.setDualPoro(False)
        self.panelSizer.SetMinSize((-1,544))
        self.SetSizer(self.panelSizer);

    def makeBox(self):
        self.dictBox={}
        skey = self.Base.groups.keys(); skey.sort()
        for g in skey: 
            self.dictBox[g] = Box(self,g);
            self.panelSizer.Add(self.dictBox[g])#,0,wx.EXPAND)
            self.panelSizer.AddSpacer((0, 5), 0)
        self.panelSizer.Add(wx.StaticText(self,-1,' '),1,wx.EXPAND|wx.ALL)
        
    def boutonVisible(self,nomBut,bool):
        item = self.FindWindowByName(nomBut);item.Enable(bool)
        
    def onButton(self,evt):
        item = self.FindWindowById(evt.GetId())
        n = str(item.GetName())
        self.Base.action(n)
        
class Box(wx.Panel):
    def __init__(self,parent,gr):
        """creates a box containing buttons obtained from the parent dic"""
        wx.Panel.__init__(self,parent,-1) #,size=(-1,350))
        bxSizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, gr),wx.VERTICAL)
        grdSizer = wx.GridSizer(2,4,vgap=3,hgap = 3)
        bx2=wx.BoxSizer(wx.HORIZONTAL)
        # tries to find buttons in addins
        butA = parent.addin.addButton(self,gr) # a list of buttons
        icons = parent.gui.icons
        if butA !=None:
            for short,name,pos in butA : 
                if pos==1 : continue
                if name in icons.keys():
                    but=wx.BitmapButton(self,-1,icons[name],size=(25,24),name = name)
                else : 
                    but=wx.Button(self,-1,short,size=(25,24),name = name)
                but.SetToolTipString(name[3:])
                grdSizer.Add(but, 0)
                self.Bind(wx.EVT_BUTTON, parent.onButton, but)
                parent.Base.dicaction[name] = 'self.addin.doaction(\''+name+'\')'
                
        for i in range(len(parent.Base.groups[gr])):
            n=parent.Base.groups[gr][i]
            shortName = gr[2:4]+'_'+n
            but = wx.BitmapButton(self,-1,icons[shortName],size=(25,24),name=shortName)
            but.SetToolTipString(shortName[3:])
            grdSizer.Add(but, 0);
            self.Bind(wx.EVT_BUTTON, parent.onButton, but)

        if butA !=None:
            for short,name,pos in butA :
                if pos==0:continue                
                if name in icons.keys():
                    but=wx.BitmapButton(self,-1,icons[name],size=(25,24),name = name)
                else : 
                    but=wx.Button(self,-1,short,size=(25,24),name = name)
                grdSizer.Add(but, 0)
                self.Bind(wx.EVT_BUTTON, parent.onButton, but)
                parent.Base.dicaction[name] = 'self.addin.doaction(\''+name+'\')'
        bxSizer.AddMany([(grdSizer, 0),(bx2,0)])
        self.SetSizer(bxSizer)

