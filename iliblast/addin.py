import os
from config import *
from Pht3d import *
from Min3p import *
from geometry import *
from matplotlib import pylab # for having grafs in batch
from Pest import *
from Opgeo import *

class addin:
    """the addin class is used to add buttons or menus in the interface to
        manage things that are around the model disctionnaries
        the structure dict stores the name and location of addins
        the data are stored in dicaddin (a copy of core.dicaddin)"""
    def __init__(self,core,gui=None):
        self.gui,self.core = gui,core
        self.dickword = core.dickword
        self.grd = None
        self.initAddin()
        
    def setGui(self,gui):
        self.gui = gui
        if gui != None:
            cfg = Config(self.core)
            self.dialogs = cfg.dialogs
            self.gtyp = cfg.gtyp
        
    def initAddin(self):
        self.structure={'button':{},'menu':{}}
        self.pht3d = PHT3D(self.core)
        self.min3pChem = Min3p(self.core)
        #self.fipy = FpModel(self.core)
        self.opgeo = Opgeo(self.core)
        # creating usedModules addin
        self.lastBatch = ''
        name='usedM'
        self.core.dicaddin[name] = {}
        for mod in self.core.modelList:
            lmodules = self.dickword[mod].grpList
            if mod[:4] in ['Min3','Opge','Sutr']: val = [True]*len(lmodules) #,'Fipy'
            else : val = [False]*len(lmodules)
            for i in range(len(lmodules)):
                if (mod=='Modflow') & (lmodules[i] in ['DIS','BAS6','LPF','PCG','WEL']): val[i]=True
                if (mod=='Mt3dms') & (lmodules[i] in ['BTN','ADV','DSP','GCG']): val[i]=True
                if (mod=='Pht3d') & (lmodules[i] in ['PH']): val[i]=True
                if (mod=='Observation') & (lmodules[i] in ['OBS']): val[i]=True
            self.structure['menu'][mod]={'name':name,'position': 0,
                'function': 'onUsedModules','short':'M'}
            self.core.dicaddin[name+'_'+mod] = (lmodules,val) # only data are stored in dicaddin  
        # creating the structure for the buttons
        name = 'Model'
        model = {'dimension':'2D','type':'confined','group':'Modflow series'}
        self.core.dicaddin[name] = model
        self.structure['button']['1.Model'] = [{'name':name,'pos':0,'short':'M'}]
        name = 'Grid'
        grid = {'x0':'0','y0':'0','x1':'100','y1':'50','dx':'5','dy':'2'} # default grid
        self.core.dicaddin[name] = grid
        self.structure['button']['1.Model'].append({'name':name,'pos':0,'short':'G'})
        name = '3D'
        dim = {'zmin':0.,'topMedia':[10],'listLayers':[1]}
        self.core.dicaddin[name] = dim
        self.structure['button']['1.Model'].append({'name':name,'pos':0,'short':'3D'})
        name = 'Time' # select times for the model
        self.core.dicaddin[name] = {'final':'10.','steps':'1.','mode':'linear'} # default time
        self.structure['button']['1.Model'].append({'name':name,'pos':0,'short':'T'})
        name = 'Particle' # create particles
        self.structure['button']['2.Flow'] = [{'name':name,'pos':1,'short':'P'}]
        
        name = 'MtSpecies' # llow to select species for mt3d
        self.core.dicaddin[name] = {'flag':'Mt3dms','species':[]}
        self.structure['button']['3.Transport'] = [{'name':name,'pos':0,'short':'Spc'}]
        name = 'MtReact' # values of parameters for each species
        self.core.dicaddin[name] = {}
        self.structure['button']['3.Transport'].append({'name':name,'pos':0,'short':'Rct'})
        
        name = 'ImpDb' # import the phreeqc database (no data needed)
        self.structure['button']['4.Chemistry']=[{'name':name,'pos':0,'short':'I'}]
        name = 'Chemistry' # opens the chemistry dialog
        self.core.dicaddin[name] = {}
        self.core.dicaddin['MChemistry'] = {} # for Min3p to store a different chemistry
        self.structure['button']['4.Chemistry'].append({'name':name,'pos':0,'short':'C'})        

        name = 'InitialChemistry' # to set specific initial chemistry
        self.core.dicaddin[name] = {'name':'','formula':'value ='}
        self.grd = makeGrid(self.core,self.core.dicaddin['Grid'])
        self.setChemType()
        
    def setChemType(self):
        self.chem = self.pht3d
        if self.core.dicaddin['Model']['group'] == 'Min3p': 
            self.chem = self.min3pChem
        self.chem.resetBase()
        
    def update1(self,dict1):
        cdict = self.core.dicaddin.copy()
        for k in dict1.keys():
            if k not in cdict.keys(): continue
            if type(dict1[k])==type({'d':1}):
                for k1 in dict1[k].keys():
                    cdict[k][k1] = dict1[k][k1]
            elif k[:5]=='usedM': # some moduls can have been added in new version
                lmod,val = cdict[k]
                lmod1,val1 = dict1[k]
                for i,md in enumerate(lmod): 
                    if md in lmod1: 
                        if val1[lmod1.index(md)]: val[i]=True
                cdict[k] = (lmod,val)
            else :
                cdict[k] = dict1[k]
        self.core.dicaddin = cdict.copy()
                
    def initMenus(self):
        #add the menu in the gui interface 
        self.gui.addMenu(502,'Modflow_modules',self.onUsedModules)   
        self.gui.addMenu(503,'Mt3dms_modules',self.onUsedModules)   
        self.gui.addMenu(506,'Batch',self.onBatchDialog)   
        self.gui.addMenu(507,'Initial chemistry',self.onInitialChemistryDialog)   
        self.gui.addMenu(508,'Pest',self.onPest)   
        
    def addButton(self, location, panelName):
        """this method is called by an external panel (for instance parameters)
        and provides a button that will open a dialog able to modify the content
        of the addin dictionnary
        the action to be done is stored in the parametersGui dict of actions """
        sButt = self.structure['button']
        but = None
        if panelName in sButt:
            but = []
            for bdic in sButt[panelName]:
                name = 'Ad_'+bdic['name']
                but.append((bdic['short'],name,bdic['pos']))
        return but
        
    def doaction(self,actionName):
        """the action to be done when an addin button is clicked"""
        if actionName == 'Ad_Model':
            m = self.core.dicaddin['Model']
            data = [('dimension','Choice',(m['dimension'],['2D','3D','Radial','Xsection'])),
                    ('type','Choice',(m['type'],['confined','free'])),
                    ('group','Choice',(m['group'],['Modflow series','Min3p','Opgeo','Sutra']))
                    ]
            dialg = self.dialogs.genericDialog(self.gui,'Model',data)
            retour = dialg.getValues()
            if retour != None:
                m['dimension'],m['type'],m['group'] = retour
                self.gui.varBox.chooseCategory(m['group'])
                if m['type']=='free':
                    self.core.setValueFromName('Modflow','LAYTYP',1) # 0 for confined, 1 for Free
                    self.core.setValueFromName('Mt3dms','TLAYCON',1)
                if m['dimension'] in ['Xsection','Radial']:
                    self.core.setValueFromName('Modflow','TOP',1.)
                    self.core.setValueFromName('Modflow','BOTM',0.)
                    self.core.setValueFromName('Modflow','DELC',1.)
                    self.core.setValueFromName('Modflow','NROW',1)
                self.set3D()
                self.setChemType()
                
        if actionName =='Ad_Grid':
            g = self.core.dicaddin['Grid']
            dvert = 'dy';vert='Y'
            if self.getDim() in ['Radial','Xsection']: 
                dvert = 'dz';vert = 'Z'
            data = [('Xmin','Text',g['x0']),(vert+'min','Text',g['y0']),
                    ('Xmax','Text',g['x1']),(vert+'max','Text',g['y1']),
                    ('dx','Textlong',g['dx']),(dvert,'Textlong',g['dy'])]
            dialg = self.dialogs.genericDialog(self.gui,'Grid',data)
            retour = dialg.getValues()
            if retour != None:
                g['x0'],g['y0'],g['x1'],g['y1'],g['dx'],g['dy'] = retour;#print g
                self.setGridInModel()
                if self.gtyp == 'wx':
                    self.gui.guiShow.dlgShow.onTickBox('Model','Grid','B',True)
                self.gui.visu.initDomain()

        if actionName == 'Ad_3D':
            m = self.core.dicaddin['3D']
            data = [('Top of Media','Textlong',m['topMedia']),
                    ('Bottom','Text',m['zmin']),
                    ('nb of layers','Textlong',m['listLayers'])
                    ]
            dialg = self.dialogs.genericDialog(self.gui,'3D',data)
            retour = dialg.getValues()
            if retour != None:
                m['topMedia'],m['zmin'],m['listLayers'] = retour
                self.set3D()
                dic = self.make3DTable()
                dialg = self.dialogs.myNoteBook(self.gui,'3D',dic)
                retour = dialg.ShowModal()
                
        if actionName == 'Ad_Time':
            t = self.core.dicaddin['Time']
            data = [('Total simulation time','Textlong',t['final']),
                    ('Step size','Textlong',t['steps']),
                    ('Step mode','Choice',(t['mode'],['linear','log']))]
            dialg = self.dialogs.genericDialog(self.gui,'Time',data)
            retour= dialg.getValues()
            if retour != None:
                t['final'],t['steps'],t['mode'] = retour
                self.setTime()
                
        if actionName == 'Ad_Particle':
            self.particle = 1 # forward
            data = [('direction','Choice',('forward',['forward','backward']))]
            dialg = self.dialogs.genericDialog(self.gui,'Particle',data)
            retour = dialg.getValues()
            if retour != None: 
                if retour[0] == 'backward' : self.particle = -1
            if self.gtyp == 'wx':
                self.gui.actions('zoneStart')
                self.gui.visu.startParticles()
                self.gui.guiShow.dlgShow.onTickBox('Flow','Particles','B',True)
                
        if actionName == 'Ad_MtSpecies':
            m = self.core.dicaddin['MtSpecies']
            data = [('Type','Choice',(m['flag'],['Mt3dms','Pht3d'])),
                    ('Species','Textlong',m['species'])
                    ]
            dialg = self.dialogs.genericDialog(self.gui,'Select Species',data,'Dbleporo')
            retour = dialg.getValues()
            if retour != None:
                m['flag'],m['species'] = retour
                #if m['flag']=='Pht3d': m['species'] = self.pht3d.getListSpecies()
            self.setMtSpecies(m['flag'],m['species'])
                
        if actionName == 'Ad_MtReact':
            dic = {'Parameters':self.core.dicaddin['MtReact'].copy()}
            dialg = self.dialogs.myNoteBook(self.gui,"Rct parameters",dic)
            dic2 = dialg.getValues()
            if dic2 != None:
                self.core.dicaddin['MtReact'] = dic2['Parameters']
            dialg.Destroy()  

        if actionName == 'Ad_ImpDb':
            if self.core.dicaddin['Model']['group'] == 'Min3p':
                self.chem = self.min3pChem
                self.chem.importDB(self.min3pChem.Base['MChemistry'])
                self.callCheckDialog()
                self.chem.updateChemistry()
                bs = self.chem.Base['MChemistry'];#print bs
                self.chem.readKinetics(bs['redox']['rows'])
                self.chem.readMinerals(bs['mineral']['rows'])
#                for name in ['comp','complex','gases']:
#                    self.chem.readOtherDb(name,bs[name]['rows'])
#                print bs
            else :
                self.chem = self.pht3d
                if 'pht3d_datab.dat' not in os.listdir(self.core.fileDir):
                    self.dialogs.onMessage(self.gui,'pht3d_datab.dat file missing')
                fname = str(self.core.fileDir+os.sep+'pht3d_datab.dat')
                self.pht3d.tempDbase,self.pht3d.npk= self.pht3d.importDB(fname);
                self.chem.updateChemistry()
            self.dialogs.onMessage(self.gui,'Database imported')
            
        if actionName == 'Ad_Chemistry':
            nameB = 'Chemistry'
            if self.core.dicaddin['Model']['group'] == 'Min3p': 
                nameB='MChemistry'
                dic = self.chem.Base[nameB].copy()
#                if self.core.getValueFromName('Min3pTrans','Diff_choice')==0: # remove gas if not dusty gas model
#                    dic.pop('gases')                
            else :
                dic = self.chem.Base[nameB].copy()
            dialg = self.dialogs.myNoteBook(self.gui,"Chemistry",dic)
            dic2 = dialg.getValues()
            if dic2 != None:
                for k in dic2.keys(): self.chem.Base[nameB][k] = dic2[k]
            self.core.dicaddin[nameB] = self.chem.Base
            dialg.Destroy()
            
    def getUsedModulesList(self,modName):
        """returns only the modules that are used as a list"""
        #print self.core.dicaddin['usedM_'+modName]
        modules,val=self.core.dicaddin['usedM_'+modName]
        l0=[]
        for i in range(len(modules)): 
            if val[i]: l0.append(modules[i])
        return l0
        
    def setUsedModulesList(self,modName,mlist):
        modules,val=self.core.dicaddin['usedM_'+modName]
        for i in range(len(modules)):
            if modules[i] in mlist: val[i]=True
    
    def onUsedModules(self,evt):
        id = evt.GetId();
        item = self.core.gui.menuBarre.FindItemById(id)
        modName = str(item.GetText()).split('_')[0]
        data = self.core.dicaddin['usedM_'+modName]
        # below not really elegant but to have mnwt, rct and vdf for older version
        for n in ['MNWT']:
            if (modName=='Modflow') & (n not in data[0]): 
                data[0].append(n);data[1].append(False)
        for n in ['SSMs','RCT','VDF','UZT']:
            if (modName=='Mt3dms') & (n not in data[0]): 
                data[0].append(n);data[1].append(False)
        dialg = self.dialogs.checkDialog(self.gui,'Select Modules',zip(data[0],data[1]))
        data = dialg.getValues()
        if data != None:
            self.core.dicaddin['usedM_'+modName]=data
            l0=[]
            for i in range(len(data[0])):
                if data[1][i]: l0.append(data[0][i])
            item = self.gui.varBox.choiceG
            self.gui.varBox.setChoiceList(item,l0)
        mtm,mtval = self.core.dicaddin['usedM_Mt3dms']
        bool = False
        if 'RCT' in mtm : bool = mtval[mtm.index('RCT')]
        self.gui.onRCT(bool)
        
    def callCheckDialog(self):
        dicIn = self.chem.temp['Dbase'].copy()
        cpl = self.chem.temp['Dbase']['complex']*1
        dicIn.pop('complex')
        #print 'incallcheck',dicIn
        dialg = self.dialogs.myNoteBookCheck(self.core.gui,'Choose species',dicIn)
        retour = dialg.getValues()
        if retour!= None:
            self.chem.temp['Dbase'] = retour
        self.chem.temp['Dbase']['complex']=cpl
        #print self.chem.temp['Dbase']
        
    def onBatchDialog(self,evt):
        from matplotlib import rcParams
        rcParams['interactive']=True
        head='insert python commands below'
        dialg = self.dialogs.largeTextDialog(self.gui,'Batch program',head,self.lastBatch)
        retour = dialg.GetText();#print retour
        if retour != None:
            txt = retour #dialg.GetTextAsList()
            self.lastBatch=txt
            txt1=txt.replace('core','self.core')
            exec(txt1)
        else : return

    def onInitialChemistryDialog(self,evt):
        head='calculate initial chemistry'
        inC = self.core.dicaddin['InitialChemistry']
        txt = 'name = '+inC['name'] +'\n'+inC['formula']
        txt+= '\n#name=Ca, value=ones((25,30))*5e-4'
        txt+= '\n#name=All, value=importUCN'
        txt+= '\n#name=Hfo_w, value=core.importLayerValues(\'Hfo_layers.txt\',\'Hfo_w\')'
        dialg = self.dialogs.largeTextDialog(self.gui,'Initial chemistry',head,txt)
        retour = dialg.GetText()
        if retour != None:
            txt = dialg.GetText() #dialg.GetTextAsList()
            name = txt.split('\n')[0].split('=')[1].strip()
            f0 = txt.split('#')[0]
            formula = '\n'.join(f0.split('\n')[1:]);#print name,formula
            self.core.dicaddin['InitialChemistry']={'name':name,'formula':formula}
        else : return
        dialg.Destroy()
        
    def onPest(self,evt):
        pest=Pest(self.core)
        pest.readPst()
        pest.writeTpl()
        pest.writeBat()
        pest.getObsPt()
        pest.writeInst()
        pest.writePyscript()
        pest.writePst()

    def setGrd(self,grd): self.grd = grd
    
    def getFullGrid(self): return self.grd      
        
    def setGridInModel(self):
        g0 = self.core.dicaddin['Grid']
        g = makeGrid(self.core,g0)
        self.grd = g
        mgroup = self.core.dicaddin['Model']['group'];#print 'addin line 316 mgroup', mgroup
        self.xsect = False
        if self.getDim() == 'Xsection': self.xsect = True
        if mgroup =='Modflow series':
            self.core.dicval['Modflow']['dis.4']=list(g['dx']) # pb with setting list
            self.core.dicval['Modflow']['dis.5']=list(g['dy'])
            self.core.setValueFromName('Modflow','NCOL',g['nx'])
            self.core.setValueFromName('Modflow','NROW',g['ny'])
        elif mgroup =='Min3p' :
            l2 = 'spat.2'
            if self.xsect: l2 = 'spat.3'
            self.core.dicval['Min3pFlow']['spat.1']=[1,g['nx'],g['x0'],g['x1']] 
            self.core.dicval['Min3pFlow'][l2]=[1,g['ny'],g['y0'],g['y1']] 
        elif mgroup =='Sutra' :
            nx,ny = int(g['nx']),int(g['ny'])
            if self.getDim() == '2D': nbL,nbL1 = 1,1
            else : 
                nbL = getNlayers(self.core)
                nbL1 = nbL + 1
            nno,nel = (nx+1)*(ny+1)*nbL1, nx*ny*nbL
            self.core.dicval['Sutra']['glob.2b'][2:] =[nx+1,ny+1,nbL1] 
            self.core.dicval['Sutra']['glob.3'][:2] = [nno,nel]
        elif mgroup =='Opgeo' :
            self.core.dicval['OpgeoFlow']['domn.2']=list(g['dx']) 
            self.core.dicval['OpgeoFlow']['domn.3']=list(g['dy'])   
            self.opgeo.buildMesh()
        elif mgroup =='Fipy' :
            self.core.dicval['FipyFlow']['domn.2']=list(g['dx']) 
            self.core.dicval['FipyFlow']['domn.3']=list(g['dy'])   
            self.fipy.buildMesh()
        
    def getModelType(self): return self.core.dicaddin['Model']['type']
    def getModelGroup(self): return self.core.dicaddin['Model']['group']
        
    def getDim(self): return self.core.dicaddin['Model']['dimension']
        
    def get3D(self): return self.core.dicaddin['3D']
    
    def set3D(self):
        dm = self.getDim()
        if dm not in ['2D','3D'] : return
        med = self.core.dicaddin['3D']
        self.gui.on3D(dm=='3D')
        if dm=='3D': 
            nbL = getNlayers(self.core)
            self.core.setValueFromName('Modflow','TOP',med['topMedia'])
            z0 = med['zmin']
            botM = med['topMedia'][1:];botM.append(z0)
            self.core.setValueFromName('Modflow','BOTM',botM)
        if dm=='2D':
            nbL = 1
        self.gui.onSetMediaNb(getNmedia(self.core),nbL)
        self.core.setValueFromName('Modflow','NLAY',nbL)            
            
    def make3DTable(self):
        nbL,lilay,dzL = makeLayers(self.core)
        toplist = [float(a) for a in self.core.addin.get3D()['topMedia']]
        nbM = len(lilay)
        bot = float(self.core.addin.get3D()['zmin'])
        toplist.append(bot);#print toplist
        dic={'cols':['Media','Layer','z'],'rows':[str(a) for a in range(nbL)],'data': []}
        top,nl = toplist[0],0
        for im in range(nbM):
            ep = toplist[im]-toplist[im+1]
            for il in range(lilay[im]):
                dz = dzL[im][il]*ep
                dic['data'].append([im,nl,str(top)[:5]+' to '+str(top-dz)[:5]])
                top -= dz
                nl += 1
        return {'3Dlayers':dic}
        
    def setTime(self):
        a = self.core.makeTtable()
        tlist = self.core.getTlist2();nper = len(tlist)
        self.gui.guiShow.setNames('Model_Tstep_L',tlist,'numbers')
        if self.getModelGroup()[:3]=='Mod':
            self.core.setValueFromName('Modflow','NPER',nper)
        elif self.getModelGroup()[:3]=='Min':
            self.core.setValueFromName('Min3pFlow','Tfinal',tlist[-1])
            self.core.setValueFromName('Min3pFlow','Tmaxstep',tlist[-1]/100.)
        elif self.getModelGroup()[:3]=='Sut':        
            tl2 = ' '.join([str(t) for t in tlist])
            self.core.setValueFromName('Sutra','TLIST',tl2)
            self.core.setValueFromName('Sutra','NTLIST',nper)
            stepdiv = self.core.getValueFromName('Sutra','STEPDIV')
            self.core.setValueFromName('Sutra','NCOLPR',stepdiv)
            self.core.setValueFromName('Sutra','LCOLPR',stepdiv)

    def setMtSpecies(self,flag,species):
        rows = species
        #nrows = len(rows)
        cols = ['SP1','SP2','RC1','RC2']
        data,rowIn,dataIn = [],[],[]
        mtreact = self.core.dicaddin['MtReact']
        if mtreact.has_key('rows'): 
            rowIn,dataIn = mtreact['rows'],mtreact['data']
        for sp in rows :
            if sp in rowIn: 
                data.append(dataIn[rowIn.index(sp)])
            else : 
                data.append([0]*len(cols))
        self.core.dicaddin['MtReact']={'rows':rows,'cols':cols,'data':data}
        
    def getMtSpecies(self): return self.core.dicaddin['MtSpecies']
    def getMtReact(self): return self.core.dicaddin['MtReact']
            
###################### CALCULATION OF PARTICLES #################
    def calcParticle(self,xp0,yp0,zoneMatrix=None):
        """ represent the particle in the visu from x0,y0 coordinates"""
        grp = self.getModelGroup()
        if grp[:2]=='Op' and self.core.dicval[grp+'Flow']['domn.1'][0]>0:
            xp,yp,tp = self.calcPartMesh(xp0,yp0)
        else :
            grd  = self.getFullGrid()
            dx,dy = array(grd['dx']), array(grd['dy']);
            data = array([grd['x0'],grd['y0'],xp0,yp0])
            #[xp,yp,tp,cu1,nt] = iphtC1.calcPart1(data,dx,dy,vx[0],vy[0],clim)
            [xp,yp,tp,cu1,nt] = self.calcPartGrid(data,dx,dy,zoneMatrix) #,clim)
            xp,yp,tp = xp[:nt],yp[:nt],tp[:nt]
        return [xp,yp,tp]
        
    def calcPartGrid(self,datain,dxi,dyi,zoneMatrix=None):
        """transient particle tracking for 2D, xsection and semi-3D (along layer)"""
        eps=1.e-6;cst1=5.e-5;#print self.particle
        infos = self.core.flowReader.getPart()
        poro = self.core.getValueFromName('Mt3dms','PRSTY')
        tlist = self.core.getTlist2()
        try : startTime = float(self.gui.guiShow.getCurrentTime())
        except ValueError : startTime = 0.001
        iper=self.gui.guiShow.Tstep
        ilay = self.gui.visu.curLayer
        #print startTime, iper, ilay
        thick = self.core.flowReader.getThickness(self.core,iper);# can be 3D
        x0,y0,xp0,yp0 = datain;
        #ny,a=shape(vxi);nx=a-1;
        nx,ny=len(dxi),len(dyi)
        nt=int(max(nx,ny)*3.) # mod nx
        xg=zeros((nx+1));yg=zeros((ny+1));xg[0]=x0;yg[0]=y0;
        for i in range(1,nx+1): xg[i] = xg[i-1]+dxi[i-1]; # mod dx(i) -> dx(i-1)
        for i in range(1,ny+1): yg[i] = yg[i-1]+dyi[i-1]; # pareil dy

        #* start calculations */
        xp=zeros((nt+1));yp=xp*0.;tp=xp*0.;cu1=xp*0.;
        it = 0;xp[0]=xp0;yp[0]=yp0;tp[0]=startTime;ptin=1;
        if zoneMatrix==None: zoneMatrix = ones((ny,nx))
        while ((it<nt) and (ptin==1) and tp[it]>0):
            it+=1
            dxc = 0.; dyc = 0.;dt = 0.;#print 'ecoul calcp',tp[it-1],iper,tlist[iper]
            #print tp[it-1],iper
            if tp[it-1]>tlist[iper+1] :
                if tp[it-1]<tlist[-1]: 
                    a=tlist-tp[it-1];iper=min(where(a>0)[0])-2
                else : break
            dist=xg[nx-1]-x0;jp=0;
            for j in range(nx):
                a=xp[it-1]-xg[j]
                if ((a<dist)and(a>=0.)):dist=a;jp=j;
            dx=dxi[jp];

            dist=yg[ny-1]-x0;ip=0;
            for i in range(ny):
                a=yp[it-1]-yg[i];
                if ((a<dist)and(a>=0.)):dist=a;ip=i;
            dy=dyi[ip];
            
            cl = zoneMatrix[ip,jp] #clim[ip,jp];
            if ((jp<nx)and(jp>0)and(ip<ny)and(ip>0)and(cl>0))or(it<5): ptin=1
            else : ptin=0
            vx,vy=self.core.flowReader.getLocalTransientV(self.core,infos,thick,ilay,ip,jp-1,iper)
            #if it<5: print 'addin calc part l 477',self.particle,vx,vy
            vx,vy=self.particle*vx,self.particle*vy;#forward or backward
            vx1,vx2=vx/poro;vy1,vy2=vy/poro;
            Ax = (vx2-vx1)/dx;vxm = 2*vx1-vx2;
            Ay = (vy2-vy1)/dy;vym = 2*vy1-vy2;

            x0m = (xp[it-1]-xg[jp]+dx);
            y0m = (yp[it-1]-yg[ip]+dy);
            vxp0 = vxm+Ax*x0m; vyp0 = vym+Ay*y0m;
            sensx = sign(vxp0);sensy = sign(vyp0)
            #* on differencie les cas */
            if ( (abs(vy1)+abs(vy2)) < ((abs(vx1)+abs(vx2))*cst1) ): # sens x
                dt = ((1.5+0.5*sensx)*dx-x0m)/vxp0*(1.+eps);
                dxc = vxp0*dt; dyc = 0;
            elif ( (abs(vx1)+abs(vx2)) < ((abs(vy1)+abs(vy2))*cst1) ): # sens y
                dt = ((1.5+0.5*sensy)*dy-y0m)/vyp0*(1.+eps);
                dyc = vyp0*dt; dxc = 0;
            else :
                lb1 = (vxp0-vxm)/x0m;
                lb2 = (vyp0-vym)/y0m;
                ax1 = max((lb1*dx+vxm)/vxp0,eps);
                ax2 = max((lb1*dx*2+vxm)/vxp0,eps);
                ay1 = max((lb2*dy+vym)/vyp0,eps);
                ay2 = max((lb2*dy*2+vym)/vyp0,eps);
                dtx1 = log(ax1)/lb1;dtx2 = log(ax2)/lb1;dtx = max(dtx1,dtx2);
                dty1 = log(ay1)/lb2;dty2 = log(ay2)/lb2;dty = max(dty1,dty2);
                if (dtx<=0) : dtx=1.e5; 
                if (dty<=0) : dty=1.e5; 
                dt = min(dtx,dty)*(1+eps);
                dxc = ( vxp0*exp(lb1*dt)-vxm )/lb1-x0m; 
                dyc = ( vyp0*exp(lb2*dt)-vym )/lb2-y0m;
            #* mis a jour des matrices */
            #print xp[it-1],dxc,xp[it-1]+dxc,yp[it-1],dyc,yp[it-1]+dyc
            cu1[it] = cu1[it-1] + sqrt(dxc*dxc+dyc*dyc);
            xp[it] = xp[it-1] + dxc;
            yp[it] = yp[it-1] + dyc;
            tp[it] = tp[it-1] + dt*self.particle;
        return xp,yp,tp,cu1,it
        
    def calcPartMesh(self,xp0,yp0):
        """first attempt to calculate particles tracks in a mesh
        be careful this version computes only 30 triangles, the time is wrong
        and does not stop at boundaries..."""
        iper=self.gui.guiShow.Tstep
        opg = self.opgeo
        flr = self.core.flowReader
        velo = flr.readFloFile(self.core,iper)
        x,y,lx,ly=xp0*1,yp0*1,[xp0],[yp0]
        dst = sqrt((xp0-opg.elcenters[:,0])**2+(yp0-opg.elcenters[:,1])**2)
        iel = where(dst==amin(dst))[0][0]
        
        for it in range(80): # loop on 30 triangles
            nodes = opg.trg.triangles[iel]
            xn,yn = opg.trg.x[nodes],opg.trg.y[nodes]
            un,vn = velo[0][0,nodes],velo[1][0,nodes]
            # coords of the lines of the triangle ax+by=1 a in lcoef[0,:], b in lcoef[1,:]
            lcoefs,a=zeros((2,3)),zeros((2,2))
            a[:,0]=xn[:2];a[:,1]=yn[:2];lcoefs[:,0] = solve(a,ones((2,1))[:,0])
            a[:,0]=xn[1:3];a[:,1]=yn[1:3];lcoefs[:,1] = solve(a,ones((2,1))[:,0])
            a[:,0]=xn[[0,2]];a[:,1]=yn[[0,2]];lcoefs[:,2] = solve(a,ones((2,1))[:,0])
            # coords of u ,v planes in the x,y dimension
            M = ones((3,3));M[:,0]=xn;M[:,1]=yn
            ucoef,vcoef = solve(M,un),solve(M,vn) 
            # velocity and position relative to lines of the start point
            u0 = x*ucoef[0]+y*ucoef[1]+ucoef[2]
            v0 = x*vcoef[0]+y*vcoef[1]+vcoef[2]
            pos0=sign(dot(array([x,y]),lcoefs)-1)
            #find dt
            dtx,dty = (max(xn)-min(xn))/abs(u0),(max(yn)-min(yn))/abs(v0)
            dt=min(dtx,dty)/10
            for i in range(15):
                pos = sign(dot(array([x,y]),lcoefs)-1)
                if any(pos!=pos0): break
                u1 = x*ucoef[0]+y*ucoef[1]+ucoef[2]; x += u1*dt
                v1 = x*vcoef[0]+y*vcoef[1]+vcoef[2]; y += v1*dt
                lx.append(x*1);ly.append(y*1); #print 'pos', pos, pos0
            if all(pos==pos0): return lx,ly,ones(len(lx))
            idff = where(abs(pos-pos0))[0][0] # the index of the line that has been crossed
            # move last point, to be close to the last line
            lcx,lcy = lcoefs[0,idff],lcoefs[1,idff]
            #equation lcx(x-a.u1.dt)+lcy(y-a.v1.dt)=1
            a = (x*lcx+y*lcy-1)/(u1*dt*lcx+v1*dt*lcy)*.99
            x,y = x-a*u1*dt, y-a*v1*dt;#plot(x,y,'+')
            # find next triangle
            pts = nodes[mod([idff,idff+1],3)]
            neighb = opg.trg.neighbors[iel]
            for n in neighb:
                if pts[0] in opg.trg.triangles[n] and pts[1] in opg.trg.triangles[n]:
                    iel = n
        return lx,ly,ones(len(lx))
