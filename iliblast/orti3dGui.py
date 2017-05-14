"""this is the main gui for ORTi3D. It creates a wx window where parameter
panel, visualisation panel and visuChoose panel are included.
it uses core for the major job of storing and retrieving the data
writer/readers are available for different models"""
import wx
from wxVisualisation import *
from guiShow import *
from wxParameters import *
from topBar import *
from menus import *
from core import *
from addin import *
import os
from config import *
import wx.lib.inspection

class orti3dGui(wx.Frame):
    
    def __init__(self,title):
        wx.Frame.__init__(self, None, 1, title = title,size=(1200,780)) #, style = wx.DEFAULT_FRAME_STYLE
        #self.Maximize(True)
        self.gtyp = 'wx'
        self.title = title
        self.icons = self.makeIcons()
        self.mainDir = os.path.dirname(os.getcwd());print self.mainDir
        self.core = Core(self)
        cfg = Config(self.core)
        self.linesDic,self.linesCommDic = {},{}
        for mod in self.core.modelList:
            self.linesDic[mod] = self.core.diczone[mod].getLinesDic()
            self.linesCommDic[mod] = self.core.diczone[mod].getLinesCommDic()
        #print self.linesDic
        self.makePanelMatplotlib()
        self.makeTopBar()
        self.makePanelParameters()
        self.makePanelShow()
        self.makeMenus()
        self.core.addin.setGui(self)
        self.core.addin.initMenus()
        self.BackgroundColour = (230,230,230)
        
        self.showSizer = wx.BoxSizer(wx.VERTICAL) #,wx.Size=(900,1300))
        self.showSizer.Add(self.show,0,wx.EXPAND)
        
        frameSizer = wx.BoxSizer(wx.HORIZONTAL)
        frameSizer.Add(self.paramSizer, 12, wx.EXPAND)
        frameSizer.Add(self.matplot,73, wx.EXPAND)
        frameSizer.Add(self.show, 15, wx.EXPAND)

        #frame_flags = wx.SizerFlags().Expand().Border(wx.ALL, 0).Proportion(0)
        #glob_flags = wx.SizerFlags().Expand().Border(wx.ALL, 0).Proportion(1)
        globalSizer = wx.BoxSizer(wx.VERTICAL)
        globalSizer.Add(self.topSizer,1,wx.EXPAND)
        globalSizer.Add(frameSizer,13,wx.EXPAND)
        globalSizer.Add(self.basSizer,1,wx.EXPAND)
        
        self.SetSizerAndFit(globalSizer)
        #wx.Frame.SetIcon(self,main_icon)
        #self.Layout()
        wx.EVT_CLOSE(self,self.OnExit)
        #wx.lib.inspection.InspectionTool().Show()
        
    def on3D(self,bool):
        self.wxParameters.boutonVisible('Ad_3D',bool)
        self.varBox.choice3D.Enable(bool)
        
    def onSetMediaNb(self,nbM,nbL):
        self.varBox.choice3D.Clear()
        for i in range(nbM): self.varBox.choice3D.Append(str(i))
        self.guiShow.setNames('Model_Layer_L',range(nbL))
        
    def onRCT(self,bool):
        self.wxParameters.boutonVisible('Ad_MtSpecies',bool)
        self.wxParameters.boutonVisible('Ad_MtReact',bool)

    ####################################################
    #                   make menus
    ####################################################
    def makeMenus(self):
        self.menus = Menus(self, self.core)
        #file menu
        menuFile = wx.Menu()
        mN = menuFile.Append(-1,"&"+'New'+"\tCTRL+n")
        menuFile.AppendSeparator()
        mO = menuFile.Append(-1, "&"+'Open'+"\tCTRL+o")
        mS1 = menuFile.Append(-1, "&"+'Save'+"\tCTRL+s")
        mS2 = menuFile.Append(-1, "&"+'Save as')
        mV1 = menuFile.Append(-1, "&"+'Import version1')
        mM1 = menuFile.Append(-1, "&"+'Import Modflow Ascii')
        menuFile.AppendSeparator()
        mQ = menuFile.Append(-1, "&"+'Quit'+"\tCTRL+q")

        self.Bind(wx.EVT_MENU, self.menus.OnNew, mN)
        self.Bind(wx.EVT_MENU, self.menus.OnOpen, mO)
        self.Bind(wx.EVT_MENU, self.menus.OnSave, mS1)
        self.Bind(wx.EVT_MENU, self.menus.OnSaveAs, mS2)
        self.Bind(wx.EVT_MENU, self.menus.OnImportVersion1, mV1)
        self.Bind(wx.EVT_MENU, self.menus.OnImportModflowAscii, mM1)
        self.Bind(wx.EVT_MENU, self.OnExit, mQ)
        
        # import menu
        menuImport = wx.Menu()
        mImData = menuImport.Append(-1,"&"+'Data')
        mImSolu = menuImport.Append(-1,"&"+'Solutions')
        mImUser = menuImport.Append(-1,"&"+'User Species')
        self.Bind(wx.EVT_MENU, self.menus.OnImportData, mImData)
        self.Bind(wx.EVT_MENU, self.menus.OnImportSolutions, mImSolu)
        self.Bind(wx.EVT_MENU, self.menus.OnImportUserSpecies, mImUser)
        # export menu
        menuExport = wx.Menu()
        mExParm = menuExport.Append(-1,"&"+'Current Parameter')
        mExResu = menuExport.Append(-1,"&"+'Current Result')
        self.Bind(wx.EVT_MENU, self.menus.OnExportParm, mExParm)
        self.Bind(wx.EVT_MENU, self.menus.OnExportResu, mExResu)
       
       #Add-ins
        self.menuAddin = wx.Menu()

        #Help
        menuHelp = wx.Menu()
        mH = menuHelp.Append(-1, "Help")
        mUpd1 = menuHelp.Append(-1, "Download stable")
        mUpd2 = menuHelp.Append(-1, "Download develop")
        self.Bind(wx.EVT_MENU, self.menus.OnHelp, mH)
        self.Bind(wx.EVT_MENU, self.menus.OnDownloadLast, mUpd1)
        self.Bind(wx.EVT_MENU, self.menus.OnDownloadDev, mUpd2)

        self.menuBarre = wx.MenuBar() 
        self.menuBarre.Append(menuFile, "&File")
        self.menuBarre.Append(menuImport, "&Import")
        self.menuBarre.Append(menuExport, "&Export")
        self.menuBarre.Append(self.menuAddin, "&Add-in")
        self.menuBarre.Append(menuHelp, "&?")
        self.SetMenuBar(self.menuBarre)

    def enableMenu(self,nomM,bool):
        id=self.menuBarre.FindMenu(nomM)
        if id!=-1:self.menuBarre.EnableTop(id,bool)  # pour les griser
        
    def addMenu(self,num,menuName,methd):
        self.menuAddin.Append(num,menuName)
        wx.EVT_MENU(self,num,methd)
        
    def updateTitle(self):
        self.SetTitle(self.title + " - " + self.core.fileDir+'/'+ self.core.fileName)
                               
    def OnExit(self,evt):
        self.menus.askSave(evt)
        self.Destroy()
    #####################################################
    #                   Panel Matplotlib
    ######################################################
    def makePanelMatplotlib(self):
        self.visu = wxVisualisation(self)
        sizerVisu = wx.BoxSizer(wx.VERTICAL)
        sizerVisu.Add(self.visu, 1, wx.EXPAND)
        sizerVisu.SetMinSize((600,544))
        
        self.basSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.basSizer.Add(self.visu.GetToolBar(),0)
        self.pos = wx.StaticText(self,-1,' x: y:') #,size=(200,40))
        self.pos.SetOwnBackgroundColour('WHITE')
        self.basSizer.Add(self.pos,5,wx.EXPAND)        
        self.notify = wx.StaticText(self,-1,'')
        font = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
        self.notify.SetFont(font)
        #self.notify.SetOwnForegroundColour('RED')
        self.basSizer.AddSpacer((0, 5), 0)
        self.basSizer.Add(self.notify,5,wx.EXPAND)
        
        #sizerVisu.Add(basSizer, 5,wx.EXPAND)
        self.matplot = sizerVisu
        self.visu.initDomain() #,self.model.getGlist())
        
    #def getVisu(self): return self.visu
    def onNotify(self,text): self.notify.SetLabel(text)
    def onPosition(self,text): self.pos.SetLabel(text)
    
    #####################################################
    #                   Panel Top et Parametres
    #####################################################
    def makeTopBar(self):
        self.currentModel,self.currentLine,self.currentMedia = 'Modflow',None,0
        self.topSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.varBox = variableBox(self)
        self.topSizer.Add(self.varBox) #, 0,wx.EXPAND)
        self.topSizer.Add(wx.StaticLine(self,-1), 0, wx.ALIGN_CENTER)
        self.addBox = addZoneBox(self)
        self.topSizer.Add(self.addBox)#, 0,wx.EXPAND)
        self.topSizer.Add(wx.StaticLine(self,-1), 0, wx.ALIGN_CENTER)
        self.modifBox = modifBox(self)
        self.topSizer.Add(self.modifBox)#, 0,wx.EXPAND)
        self.topSizer.SetMinSize((300,36))

    def makePanelParameters(self):
        #Creation des differents Panels
        self.paramSizer = wx.BoxSizer(wx.VERTICAL)
        self.wxParameters = wxParameters(self,self.core)
        self.paramSizer.Add(self.wxParameters,0, wx.EXPAND)
        self.onRCT(False)
        
    #####################################################
    #                   Panel Vue
    #####################################################
    def makePanelShow(self):
        self.guiShow = guiShow(self, self.core)
        self.show = wx.BoxSizer(wx.VERTICAL)
        self.show.Add(self.guiShow.dlgShow, 0, wx.EXPAND)
        
    ######################## actions ############################
    def actions(self,action):
        if action == 'zoneStart': self.panelsEnable(False)
        if action == 'zoneEnd': self.panelsEnable(True)

    def panelsEnable(self,bool):
        self.wxParameters.Enable(bool);self.guiShow.dlgShow.Enable(bool)
        self.varBox.Enable(bool);self.addBox.Enable(bool);self.modifBox.Enable(bool)

    ######################## ICONS ############################
    import sys
    os.path.join(os.path.dirname(sys.executable), 'utils')
    def makeIcons(self):
        noms=['blanc','bBleu','ZoneImg','ok',
              'Ad_Grid','Ad_3D','Ad_Time','Ad_Particle',
              #'Ad_MtReact',
              'Ad_ImpDb','Ad_Chemistry',
              'Mo_Map',
              'Top_Point','Top_Ligne','Top_Rect','Top_Poly','Top_PolyV',
              'Top_move','Top_modifPoly','Top_modifPolyRed','Top_supprime',
              'Top_supprimeAll',
              'Fl_Parameters','Fl_Write','Fl_Run',
              'Tr_Parameters','Tr_Write','Tr_Run',
              'Ch_Parameters','Ch_Write','Ch_Run',
              'Ob_Zones',
              'Vis_OriX','Vis_OriY','Vis_OriZ','Vis_SwiImg','Vis_SwiCont']
        dIcons = {}
        if 'addin.py' in os.listdir(os.getcwd()): u_dir = '..\\utils'
        else : u_dir='utils'
        for n in noms:
            img = u_dir+os.sep+ n+'.gif'
            dIcons[n] = wx.Bitmap(img, wx.BITMAP_TYPE_GIF)
        #main = wx.Icon('utils'+os.sep+'ZoneImg.gif', wx.BITMAP_TYPE_GIF)
        return dIcons

