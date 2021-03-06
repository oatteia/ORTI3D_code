from os import sep
import wx
from wxDialogs import *
from geometry import *

class boxes(wx.Panel):
    def __init__(self,gui):
        wx.Panel.__init__(self,gui,-1,size=(-1,45))
        self.gui,self.visu,self.core = gui,gui.visu,gui.core
        self.icons = gui.icons
        self.currentGroup = 'DIS'
        
    def setChoiceList(self,item,l):
        item.Clear()
        for n in l: item.Append(n)
        
    def modifZones(self,line):
        if self.gui.guiShow.curVar.has_key(line):
            self.gui.guiShow.curVar.pop(line)
    
class variableBox(boxes):
    def __init__(self,parent):
        self.parent = parent
        self.currentModel = self.parent.currentModel
        self.currentMedia = self.parent.currentMedia
        boxes.__init__(self,parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self,-1,'Spatial Attributes', style = wx.ALIGN_CENTER)
        sizer.Add(title,0, wx.ALIGN_CENTER|wx.EXPAND)
        sizer.AddSpacer((0,2), 0)
        zoneSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        categories = ['Modflow series','Min3p','Opgeo','Sutra'] #,'Fipy'
        models = self.core.modelList*1
        for i in range(3): models[i] = models[i].upper()
        self.choiceC = wx.Choice(self, -1, choices = categories,size=(60,20))                
        self.Bind(wx.EVT_CHOICE, self.onChoiceCategory, self.choiceC)        
        self.choiceC.SetSelection(0)
        self.choiceM = wx.Choice(self, -1, choices = models[:4],size=(80,20)) # starts with modflow series             
        self.Bind(wx.EVT_CHOICE, self.onChoiceModel, self.choiceM)        
        self.choiceG = wx.Choice(self, -1, choices = [],size=(50,20))                
        self.Bind(wx.EVT_CHOICE, self.onChoiceGroup, self.choiceG)
        self.choiceL = wx.Choice(self, -1, choices = [],size=(150,20))                
        self.Bind(wx.EVT_CHOICE, self.onChoiceLine, self.choiceL)
        mediatxt = wx.StaticText(self,-1,' Media ')
        self.choice3D = wx.Choice(self, -1, choices = [],size=(50,20))                
        self.Bind(wx.EVT_CHOICE, self.onChoiceMedia, self.choice3D)
        backtxt = wx.StaticText(self,-1,' Backg. ')
        self.backg = wx.TextCtrl(self,-1,'0',size=(45,20))
        butOk = wx.Button(self, -1, 'OK',size=(20,20),name='Ok')
        self.Bind(wx.EVT_BUTTON, self.onBackOk, butOk)
        typtxt = wx.StaticText(self,-1,' Type ')
        typeList = ['one_value','formula','zone','importZones','interpolate','array']
        self.choiceT = wx.Choice(self, -1, choices = typeList) #, size=(60,20))  
        self.Bind(wx.EVT_CHOICE, self.onChoiceType, self.choiceT)
        self.chkView = wx.CheckBox(self,-1)
        self.Bind(wx.EVT_CHECKBOX, self.onViewVariable, self.chkView)

        zoneSizer.AddMany([(self.choiceC,0),(self.choiceM,0),(self.choiceG,0),(self.choiceL,0),
            (mediatxt,0,wx.ALIGN_CENTER_VERTICAL),(self.choice3D,0),(backtxt,0,wx.ALIGN_CENTER_VERTICAL),
            (self.backg,0),(butOk,0),(typtxt,0,wx.ALIGN_CENTER_VERTICAL),(self.choiceT,0),
            (self.chkView,0,wx.ALIGN_CENTER_VERTICAL)])
        zoneSizer.AddSpacer((10, 0), 0)
        zoneSizer.Add(wx.StaticLine(self, -1,style=wx.LI_VERTICAL), 0, wx.EXPAND)
        sizer.Add(zoneSizer, 0, wx.EXPAND)
        self.SetSizer(sizer)
        self.blind = {}
        for k in self.core.modelList: self.blind[k] = []
        self.blind['Mt3dms']=['btn.9','btn.10','uzt.3','uzt.4'],
        #self.chooseCategory('Mod series')
        self.curVar = {}
        
    def onChoiceCategory(self,evt):
        """the categories of models : modflow series, sutra, min3p"""
        #evt.skip()
        c0 = self.choiceC.GetStringSelection()
        self.chooseCategory(c0)
        
    def chooseCategory(self,c0):
        self.currentCategory = c0;#print c0,self.core.modelList
        lshort = ['Sutra','Min3p','Fipy','Opgeo']
        lshort2 = ['Sutr','Min3','Fipy','Opge']
        if c0 in lshort:
            lmodels = [x for x in self.core.modelList if x[:4]==c0[:4]]
        else :
            lmodels = [x for x in self.core.modelList if x[:4] not in lshort2]
        if 'Observation' not in lmodels: lmodels.append('Observation')
        self.setChoiceList(self.choiceM,lmodels)

    def onChoiceModel(self,evt):
        """contains the models : for modflow series : modflow, mt3d, pht3d..."""
        m0 = self.choiceM.GetStringSelection()
        if m0[:4] not in ['Min3','Fipy','Opge','Sutr']: #modflow series
            m1 = m0.lower();mod = m1[0].upper()+m1[1:];
        else :
            mod = m0
        self.parent.currentModel, self.currentModel = mod,mod
        lmodules = self.core.addin.getUsedModulesList(mod); #print 'topbar,l84',lmodules# to set the groups
        self.setChoiceList(self.choiceG,lmodules)
        
    def onChoiceGroup(self,evt):
        curGroup = self.choiceG.GetStringSelection()
        self.parent.currentGroup = curGroup;#print 'topb 100',curGroup
        self.choiceL.Clear()
        if curGroup not in self.gui.linesDic[self.currentModel].keys() : return
        lines = self.gui.linesDic[self.currentModel][curGroup]
        indx = self.testConditions(self.currentModel,lines)
        lcomm = self.gui.linesCommDic[self.currentModel][curGroup]
        for il in indx: 
            if lines[il] in self.blind[self.currentModel]: continue
            self.choiceL.Append(lines[il]+' '+lcomm[il])
        self.setChoiceList(self.gui.modifBox.choice,[''])
        
    def testConditions(self,modName,lstL):
        """ test if the lines indices given in lstL sastify the condition
        also test if the data are like arrays"""
        indexout=[];
        for i,l in enumerate(lstL):
            cond = self.core.dickword[modName].lines[l]['cond']
            atype = self.core.dickword[modName].lines[l]['type'][0]
            if self.core.testCondition(modName,cond) and (atype[:3]=='arr'):
                indexout.append(i)
        return indexout

    def onChoiceLine(self,evt):
        line = str(self.choiceL.GetStringSelection().split()[0])
        self.parent.currentLine = line
        media = self.currentMedia
        vallist = self.core.dicval[self.currentModel][line];#print 'topbar valist',vallist
        nval = len(vallist)
        nmedia = getNmedia(self.core)
        if nval<nmedia : vallist.extend([vallist[0]]*(nmedia-nval))
        self.backg.SetValue(str(vallist[media])) # set to the new value
        self.gui.modifBox.updateChoiceZone(line)
        self.choiceT.SetStringSelection(self.core.dictype[self.currentModel][line][0])
        self.visu.showVar(line, media)
        self.gui.modifBox.valZ.Enable(False)
            
    def onChoiceMedia(self,evt):
        """changes the media in visualization and stores the current media"""
        media = self.choice3D.GetSelection()
        self.currentMedia = media
        line = self.parent.currentLine
        vallist = self.core.dicval[self.currentModel][line]
        self.backg.SetValue(str(vallist[media]))
        self.visu.showVar(line, self.currentMedia)
        
    def onBackOk(self,evt):
        line = self.parent.currentLine
        media = self.currentMedia
        self.core.setValue(self.currentModel,line,media,float(self.backg.GetValue()))
        
    def onChoiceType(self,evt):
        line = self.parent.currentLine
        choice = str(self.choiceT.GetStringSelection()); #print choice
        self.core.dictype[self.currentModel][line] = [choice]
        if choice == 'formula': self.onFormula(evt)
        elif choice=='interpolate': self.onInterpolate(evt)
        elif choice == 'importZones': 
            self.onImportZones(evt)
            self.core.dictype[self.currentModel][line] = ['zone']
        #print line,self.curVar.keys()
        if self.curVar.has_key(line): 
            self.curVar.pop(line);#print line,self.curVar.keys() # when a type is selected, it removes the stored  view
        
    def onImportZones(self,evt):
        fdialg = myFileDialog()
        fileDir,fileName = fdialg.getFile(self.gui,evt,'Open','*.txt')
        self.core.importZones(fileDir,fileName,self.currentModel,self.parent.currentLine)

    def onFormula(self,evt):
        """opens a dialog to ask for python formula and executes them
        to get the value of the given keyword in the last line
        """
        line = self.parent.currentLine
        formulaIn = self.core.getFormula(self.currentModel,line)[0]; #print formula
        dialg = textDialog(self,'input python formula',(340,300),str(formulaIn))
        retour = dialg.ShowModal()
        if retour == wx.ID_OK:
            formula = dialg.getText();
            self.core.dicformula[self.currentModel][line]=[str(formula)]
            self.core.dictype[self.currentModel][line]=['formula']
            self.modifZones(line)
        dialg.Destroy()
        
    def onInterpolate(self,evt):
        """creates the string for a specific formula"""
        ll = self.parent.currentLine
        mod = self.currentModel
        reg = 'Regular'
        if mod[:5]=='Opgeo': reg = 'Unstruct'
        s='modName = \''+mod+'\'\nline = \''+ll+'\'\nintp = 1\n'
        s+='#choices : interp. Kr, interp. ID; vtype: spher, gauss, gauss3\n'
        s+='opt = \'interp. Kr;vrange=22;vtype=@gauss3@\'\n'
        s+='value = block'+reg+'(self,modName,line,intp,opt,0)'
        self.core.dicformula[mod][ll]=[s]
        self.core.dictype[self.currentModel][ll]=['formula']
        self.choiceT.SetStringSelection('formula')
        self.onFormula(evt)
        
    def onViewVariable(self,evt):
        """used to see the current variable for current medium"""
        if self.chkView.GetValue(): 
            mod = self.parent.currentModel
            line = self.parent.currentLine
            opt, iper, plane, section = None,0, 'Z',self.currentMedia; #print 'guisho 275',line,self.curVar
            if self.curVar.has_key(line): 
                mat = self.curVar[line]*1
            else:
                mat = self.core.getValueLong(mod,line,0)*1;#print 'topb 210',shape(mat)
                self.curVar[line] = mat*1
            X,Y = getXYmeshSides(self.core,plane,section)
            if self.core.addin.getModelGroup()=='Opgeo':
                return None,None,mat[0][0]
            if self.core.addin.getDim() in ['Radial','Xsection']:
                m2 = mat[-1::-1,0,:]
            else :
                if plane=='Z': m2 = mat[section,:,:] #-1 for different orientation in modflow and real world
                elif plane=='Y': m2 = mat[:,section,:]
                elif plane=='X': m2 = mat[:,:,section]
        #self.curVarView = m2
            self.visu.createImage([X,Y,m2])
        else :
            self.visu.drawImage(False)
        
class addZoneBox(boxes):

    def __init__(self,parent):
        # icons pour choisir les zones
        self.parent = parent
        self.currentMedia = parent.currentMedia
        boxes.__init__(self,parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, -1, "Add Zones", style = wx.ALIGN_CENTER)
        sizer.Add(title,0, wx.ALIGN_CENTER|wx.EXPAND)
        sizer.AddSpacer((0,2), 0)
        zoneSizer = wx.BoxSizer(wx.HORIZONTAL)
        butPt = wx.BitmapButton(self, -1, self.icons['Top_Point'],size=(25,24),name='POINT')
        butL = wx.BitmapButton(self, -1, self.icons['Top_Ligne'],size=(25,24),name='LINE')
        butR = wx.BitmapButton(self, -1, self.icons['Top_Rect'],size=(25,24),name='RECT')
        butPo = wx.BitmapButton(self, -1, self.icons['Top_Poly'],size=(25,24),name='POLY')
        butPv = wx.BitmapButton(self, -1, self.icons['Top_PolyV'],size=(25,24),name='POLYV')        
        #butI = wx.BitmapButton(self, -1, self.icons['Top_Interp'],size=(25,24))        

        butPt.SetToolTipString('Add point')
        butL.SetToolTipString('Add line')
        butR.SetToolTipString('Add rectangle')
        butPo.SetToolTipString('Add polygon')
        butPv.SetToolTipString('Add variable polygon')
        #butI.SetToolTipString('Interpolation')
        
        zoneSizer.AddSpacer((10, 0), 0)
        zoneSizer.AddMany([(butPt,0),(butL,0),(butR,0),(butPo,0),(butPv,0)])
        zoneSizer.AddSpacer((10, 0), 0)
        #zoneSizer.Add(but7,0)
        #zoneSizer.AddSpacer((10, 0), 0)
        zoneSizer.Add(wx.StaticLine(self, -1,style=wx.LI_VERTICAL))
        sizer.Add(zoneSizer, 0, wx.EXPAND)
        self.SetSizer(sizer)
                
        self.Bind(wx.EVT_BUTTON, self.onShape, butPt)
        self.Bind(wx.EVT_BUTTON, self.onShape, butL)
        self.Bind(wx.EVT_BUTTON, self.onShape, butR)
        self.Bind(wx.EVT_BUTTON, self.onShape, butPo)
        self.Bind(wx.EVT_BUTTON, self.onShape, butPv)
        #self.Bind(wx.EVT_BUTTON, self.OnInterpol, butI)

    def onShape(self, evt):
        line = self.parent.currentLine
        item = self.FindWindowById(evt.GetId())
        shap = item.GetName()
        #print 'topbar 240',line, self.currentModel,self.parent.currentGroup#self.gui.linesDic[self.currentModel][self.parent.currentGroup]
        if (line == None) or (line not in self.gui.linesDic[self.parent.currentModel][self.parent.currentGroup]):
            onMessage(self.gui,"choose one variable")
            return
        self.gui.actions('zoneStart')
        exec('self.visu.setZoneReady(\"'+shap+'\",\"'+line+'\")')

    #####################################################################
    #                            GESTION Zone

    def onZoneCreate(self, typeZone, xy):
        """ zone drawn in visu, we get coords
        and open the dialog to fill it
        """
        curzones = self.core.diczone[self.parent.currentModel]
        line = self.parent.currentLine
        curzones.addZone(line)
        iz = curzones.getNbZones(line)-1
        curzones.setValue(line,'coords',iz,xy)
        curzones.setValue(line,'value',iz,' ')
        curzones.setValue(line,'media',iz,self.currentMedia)
        # create dialog
        dialg = zoneDialog(self, self.core,self.parent.currentModel,line, curzones.dic[line], iz)
        retour = dialg.ShowModal()
        self.gui.actions('zoneEnd')
        if retour == wx.ID_OK:
            dialg.saveCurrent()
            lz = curzones.dic[line]
            self.gui.visu.addZone(lz['media'][iz],lz['name'][iz],lz['value'][iz],lz['coords'][iz])
            self.gui.modifBox.updateChoiceZone(line)
            self.core.dictype[self.parent.currentModel][line]=['zone']
            self.core.makeTtable()
            self.modifZones(line)
        else : #cancel
            curzones.delZone(line,iz)
            self.visu.redraw()
        if line=='obs.1':
            onames = self.core.diczone['Observation'].dic['obs.1']['name']
            self.gui.guiShow.setNames('Observation_Zone_L',onames)
        curVar = self.gui.varBox.curVar
        if curVar.has_key(line): curVar.pop(line) # adding a zone changes the view of the current variable
            
#////////////////////////////////////////////////////////////////////////////

class modifBox(boxes):
    
    def __init__(self,parent):
        # icons to choose zones
        self.parent = parent
        boxes.__init__(self,parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, -1,"Modify Zones", style = wx.ALIGN_CENTER)
        sizer.Add(title, 0, wx.ALIGN_CENTER|wx.EXPAND)
        sizer.AddSpacer((0,2), 0)
        modifSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.zmodif,self.zmove,self.zindex=0,0,[]
        self.copyXy,self.copyVal=[],0.
        self.currentZone = None;
        # choice de la zone
        self.choice = wx.Choice(self, -1, choices = [],size=(60,20))                
        
        modifSizer.AddSpacer((10, 0), 0)
        modifSizer.Add(self.choice, 0, wx.ALIGN_CENTER_VERTICAL)
        #modifSizer.AddSpacer((10, 0), 0)

        # valeur de la zone selectionnee
        self.valZ = wx.Button(self, -1,'Val : ',size=(60,24))
        self.valZ.Enable(False)
        #bouton  milieu pour zone, puis deplacer, puis modif
        butMove=wx.BitmapButton(self, -1, self.icons['Top_move'],size=(25,24))
        butMod=wx.BitmapButton(self,-1,self.icons['Top_modifPoly'],size=(25,24))
        butX=wx.BitmapButton(self,-1,self.icons['Top_supprime'],size=(25,24))
        butXX=wx.BitmapButton(self,-1,self.icons['Top_supprimeAll'],size=(25,24))
        version = wx.StaticText(self,-1,"           version 28/04/2017  ")
        version.SetFont(wx.Font(7, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        butMove.SetToolTipString('move zone')
        butMod.SetToolTipString('modify polygon')
        butX.SetToolTipString('Delete zone')
        butXX.SetToolTipString('Delete all zones')
        
        modifSizer.Add(self.valZ,0,wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border = 5)
        modifSizer.AddMany([(butMove,0),(butMod,0),(butX, 0),(butXX, 0),(version,0,wx.ALIGN_BOTTOM)])
        sizer.Add(modifSizer, 0, wx.EXPAND)
        self.SetSizer(sizer)

        self.Bind(wx.EVT_CHOICE, self.onChoice, self.choice)
        self.Bind(wx.EVT_BUTTON, self.onValeurZ,self.valZ)
        self.Bind(wx.EVT_BUTTON, self.onMoveZ, butMove)
        self.Bind(wx.EVT_BUTTON, self.onModifZone, butMod)
        self.Bind(wx.EVT_BUTTON, self.onDelZone, butX)
        self.Bind(wx.EVT_BUTTON,self.onDelAllZones,butXX)
  
    def updateChoiceZone(self,line):
        # mise a jour de la liste de zone pour la nouvelle variable selectionnee
        # sur un milieu donne
        dicz = self.core.diczone[self.parent.currentModel].dic
        if (line == None) or (line not in dicz.keys()): 
            self.setChoiceList(self.choice,[''])
            return
        #self.valZ.SetLabel(line+' :')
        self.currentZname = None 
        self.currentZlist = dicz[line]
        namelist = self.currentZlist['name']
        self.setChoiceList(self.choice,namelist)
        self.valZ.SetLabel("Val : ")
   
    def onChoice(self, evt):  #choice of the  zone
        self.izone = self.choice.GetSelection();
        self.currentZname = self.currentZlist['name'][self.izone]
        self.valZ.SetLabel("Val : "+str(self.currentZlist['value'][self.izone])[:5])
        self.valZ.Enable(True)
        
    def onValeurZ(self, evt):
        dialg = zoneDialog(self, self.core,self.parent.currentModel,self.parent.currentLine,self.currentZlist,self.izone)
        retour = dialg.ShowModal()
        if retour == wx.ID_OK:
            dialg.saveCurrent() 
            line = self.parent.currentLine
            val = self.currentZlist['value'][self.izone];#print val
            self.valZ.SetLabel("Val : "+str(val)[:5])
            med = self.currentZlist['media'][self.izone]
            xy = self.currentZlist['coords'][self.izone]
            self.visu.modifZoneAttr(line, self.izone,val,med,xy)
            self.modifZones(line)
        dialg.Destroy() 
        
    def txt2coords(self,s):
        s1, xy = s.split('\n'),[]
        for s2 in s1:
            if len(s2)>1: 
                exec('a=['+s2+']')
                xy.append(a)
        return xy
        
    def onTable(self,evt):
        tbl = self.core.diczone[self.parent.currentModel].dic.getTableOfZones(line)
    
    def onMoveZ(self,evt):
        """ start moving a zone"""
        if self.currentZname != None:
            self.gui.actions('zoneStart') 
            self.visu.startMoveZone(self.parent.currentLine, self.izone)
            self.modifZones(self.parent.currentLine)
        else :
            onMessage ("please select a zone")
        
    def onModifZone(self, evt):
        """" start modification of zone after tests"""
        if self.currentZname != None:
            self.gui.actions('zoneStart') 
            self.visu.modifZone(self.parent.currentLine, self.izone)
            self.modifZones(self.parent.currentLine)
        else :
            onMessage ("please select a zone")
            
    # get back coordinates and change them
    def onModifZoneCoord(self, line, index, coord):
        self.gui.actions('zoneEnd')
        mod = self.parent.currentModel
        self.core.diczone[mod].setValue(self.parent.currentLine,'coords',self.izone,coord)        
        
    def onDelZone(self, evt):
        # si pas de zone selectionnee, on ne supprime pas...
        mod, line = self.parent.currentModel, self.parent.currentLine
        if self.currentZname != None:
            self.core.diczone[mod].delZone(line,self.izone)
            self.visu.delZone(line,self.izone)
            self.updateChoiceZone(line)
        else :
            onMessage("please select a zone")

    def onDelAllZones(self,evt):
        znb = len(self.currentZlist['name'])
        dlg= wx.MessageDialog(self,"Caution you will destroy all zones","Attention",style = \
                wx.ICON_INFORMATION|wx.CENTRE|wx.OK|wx.CANCEL)
        retour=dlg.ShowModal()
        if retour==wx.ID_OK:
            for i in range(znb-1,-1,-1):
                self.core.diczone[self.parent.currentModel].delZone(self.parent.currentLine,i)
                self.visu.delZone(self.parent.currentLine,i)
                
#    def getZonesByName(self, var, nom):
#        zList=self.aquifere.getZoneList(var); zLout=[]
#        for i in range(len(zList)):
#            if zList[i].getNom()==nom:
#                zLout.append(zList[i].getInfo()[1])
#        return zLout
