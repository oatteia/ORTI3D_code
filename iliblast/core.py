#
import os,subprocess,time,base64
from numpy import frombuffer,float64
from modflowWriter import *
from mtphtWriter import *
from min3pWriter import *
from sutraWriter import *
from ogWriter import *
import xml.dom.minidom as xdom
from geometry import *
from importExport import *
from addin import *
from timeperiod import *
from pylab import loadtxt,size
from numpy import savez_compressed
from numpy import load as npload
from config import *

class Core:
    """this is the central class that makes the link between all objects
    it can be used on graphic mode or batche mode
    """
    def __init__(self,gui=None):
        self.modelList = ['Modflow','Mt3dms','Pht3d','Min3pFlow','Min3pTrans',
                'Min3pChem', #'FipyFlow','FipyTrans','FipyChem',
                'OpgeoFlow','OpgeoTrans','Sutra','Observation']
        self.gui = gui
        self.baseDir=os.getcwd()
        if gui!=None:
            if gui.gtyp=='qt': self.baseDir= self.gui.plugin_dir
            else : self.baseDir=self.gui.mainDir
        self.dicval = {}
        self.dictype = {}
        self.diczone = {}
        self.dickword = {}
        self.dicarray = {}
        self.dicformula = {}
        for mod in self.modelList:
            self.dicval[mod] = {}
            self.dictype[mod] = {}
            self.dicarray[mod] = {}
            self.dicformula[mod] = {}
        import modflowKeywords as Mf; self.dickword['Modflow'] = Mf
        import mtPhtKeywords as Mt; self.dickword['Mt3dms'] = Mt
        import pht3dKeywords as Ph; self.dickword['Pht3d'] = Ph
        import min3pFlowKeywords as m3F; self.dickword['Min3pFlow'] = m3F
        import min3pTransKeywords as m3T; self.dickword['Min3pTrans'] = m3T;#print self.dickword['Min3pTrans'].lines
        import min3pChemKeywords as m3C; self.dickword['Min3pChem'] = m3C;#print self.dickword['Min3pTrans'].lines
        self.dickword['FipyChem'] = Ph # fipy uses the same chemistry as pht3d
        import ogFlowKeywords as ogf; self.dickword['OpgeoFlow'] = ogf
        import ogTransKeywords as ogt; self.dickword['OpgeoTrans'] = ogt
        import sutraKeywords as su; self.dickword['Sutra'] = su
        import obsKeywords as Obs; self.dickword['Observation'] = Obs
        self.initAll()
        self.dicaddin = {}
        self.addin = addin(self)
        self.addin.initAddin()
        self.fileDir,self.fileName = None,None
        self.createKwList()
        self.radfact,self.Zblock,self.grd = 1.,None,None
        
#********************* initialisation ****************************
    def initAll(self):
        for mod in self.modelList:
            self.dicval[mod] = self.initVal(mod)
            self.dictype[mod],self.dicarray[mod] = self.initArray(mod)
            self.diczone[mod] = dicZone(self,mod)

    def initVal(self,modName):
        val = {}
        lines = self.dickword[modName].lines
        for n in lines.keys():
            if lines[n].has_key('default'):
                val[n] = lines[n]['default']
            else : val[n] = [0]*len(lines[n]['kw'])
        return val
    
    def initArray(self,modName):
        array,atype = {},{}
        lines = self.dickword[modName].lines
        for n in lines.keys():
            if lines[n]['type'][0][:3] == 'arr': 
                array[n],atype[n] = None,['one_value']
            else : 
                atype[n]=['one_value']
        return atype,array
    
    def getFormula(self,modName,line):
        """if the formula exists it returns it, if not, it
        creates a void one in the dic and returns it"""
        if self.dicformula[modName].has_key(line): 
            return self.dicformula[modName][line]
        else :
            kys = self.dickword[modName].lines[line]['kw']
            self.dicformula[modName][line] = ['value =']
            return ['value =']
            
    def updateDicts(self):
        """this methods copies the values in one model to another one if 
        the key is the same or if the correspondance is in the list"""
        def copies(nam1,nam2,kM1,kM2):
            for k in kM2.keys():
                if k in kM1.keys():
                    ll1,nb1 = kM1[k]
                    ll2,nb2 = kM2[k]
                    self.dicval[nam2][ll2][nb2] = self.dicval[nam1][ll1][nb1]
        nam1, nam2 = 'Modflow','Mt3dms'
        kM1 = self.KwList[nam1]
        kM2 = self.KwList[nam2]
        copies(nam1,nam2,kM1,kM2)
#        nam2 = 'Pht3d'
#        kM2 = self.KwList[nam2]
#        copies(nam1,nam2,kM1,kM2)
        
    def getUsedModulesList(self,modName):
        return self.addin.getUsedModulesList(modName)
    
    def setUsedModulesList(self,modName,grpList):
        self.addin.setUsedModulesList(modName,grpList)
        
    def makeTtable(self):
        self.ttable = makeTransientTable(self)
        return self.ttable
    
    def getTlist2(self):
        tlist = array(self.ttable['tlist'])
        return tlist[1:] #(tlist[:-1]+tlist[1:])/2.
        
#*************************** load, save,run models ********************    
    def openModel(self,fDir,fName):
        """opens an orti file, stored in xml"""
        self.fileDir,self.fileName = fDir,fName
        self.initAll()
        fullName = fDir+os.sep+fName; 
        if fName+'.orti' in os.listdir(self.fileDir): fullName +='.orti'
        else : fullName +='.iqpht'
        flgArr = False
        f1 = file(fullName, 'r');doc = f1.read();f1.close()
        if 'compressdata.npz' in os.listdir(fDir):
            darr = npload(fDir+os.sep+'compressdata.npz');flgArr = True
        dom = xdom.parseString(doc)    
        dicts = dom.getElementsByTagName("dict")
        for d in dicts:
            dname = d.getElementsByTagName("name")[0].childNodes[0].data
            model,typ = dname.split('_')
            if (model not in self.modelList) & (model!='dic'): continue
            keys = d.getElementsByTagName("key");dict1 = {}
            for k in keys:
                kname = str(k.getElementsByTagName("name")[0].childNodes[0].data)
                kdata = k.getElementsByTagName("content")[0].childNodes[0].data
                exec('dict1[kname] = '+kdata);
            if typ=='val': self.dicval[model].update(dict1);#print self.dicval[model]
            elif typ=='type': self.dictype[model].update(dict1)
            elif typ=='zone': self.diczone[model].setDic(dict1)
            elif typ=='array' and flgArr: 
                for k in keys : 
                    kname = str(k.getElementsByTagName("name")[0].childNodes[0].data)
                    self.dicarray[model][kname] = darr[kname.replace('.','')]
            elif typ=='formula': self.dicformula[model].update(dict1)
            elif typ=='addin': self.addin.update1(dict1)
            #print self.dicaddin
        self.addin.grd = makeGrid(self,self.dicaddin['Grid']);#print 'core 152',self.addin.grd
        self.makeTtable()
        self.Zblock = makeZblock(self)
        mtype = self.dicaddin['Model']['group'][:5]
        if mtype == 'Modfl':
            self.flowReader = modflowReader(fDir,fName)
            self.transReader = mtphtReader(fDir,fName)
        elif mtype == 'Min3p' :
            self.flowReader = min3pReader(fDir,fName)
            self.transReader = min3pReader(fDir,fName)
        elif mtype == 'Opgeo' :
            self.addin.opgeo.buildMesh()
            self.flowReader = ogReader(fDir,fName,'flow')
            self.transReader = ogReader(fDir,fName,'trans')
        elif mtype == 'Sutra' :
            self.flowReader = sutraReader(fDir,fName)
            self.transReader = sutraReader(fDir,fName)
        self.addin.setChemType()
                
    def saveModel(self,fDir = None,fName = None):
        """save the model"""
        if fDir!= None:
            self.fileDir, self.fileName = fDir, fName
        filename = self.fileDir+os.sep+self.fileName + '.orti'
        darray = {}
        farrname = self.fileDir+os.sep+'compressdata.npz'
        f1 = file(filename,'w');str1 = '<ipht3ddoc>\n'
        for md in self.modelList:
            for t in ['val','type','zone','formula','array']:
                exec('dic = self.dic'+t+'[md]');
                str1+= '<dict>\n<name>'+md+'_'+t+'</name>\n'
                if t=='zone' :
                    for k in dic.dic.keys():
                        str1 += '<key><name>'+k+'</name><content>'+str(dic.dic[k])+\
                            '</content></key>\n'
                elif t=='array':
                    for k in dic.keys():
                        if dic[k] != None:
                            str1 += '<key><name>'+k+'</name><content>\'infile\'</content></key>\n'
                            darray[k]=dic[k] # consider only one array in that line
                else :
                    for k in dic.keys():
                        str1 += '<key><name>'+k+'</name><content>'+str(dic[k])+\
                            '</content></key>\n'                    
                str1+= '</dict>\n'
                
        str1+= '<dict>\n<name>dic_addin</name>\n'
        for k in self.dicaddin.keys():
            str1 += '<key><name>'+k+'</name><content>'+str(self.dicaddin[k])+\
                '</content></key>\n'
        str1+= '</dict>\n'
        str1+= '</ipht3ddoc>'
        f1.write(str1)
        f1.close()
        s = ' ' # will be a string giving the name of the keys for saving
        for k in darray.keys(): s += k.replace('.','')+'=darray[\''+k+'\'], '
        #print 'core 213',filename,farrname,s
        if s != ' ':exec('savez_compressed(r\''+farrname+'\','+s[:-1]+')') #r to get raw string for \ problem
        
    def writeModel(self,modName,info=True):
        """ writes the ascii file for modflow series, does nothing for fipy"""
        if modName  == 'Modflow':
            self.mfWriter = modflowWriter(self,self.fileDir,self.fileName)
            self.mfWriter.writeModflowFiles(self)
            self.flowReader = modflowReader(self.fileDir,self.fileName)
        if modName in ['Mt3dms','Pht3d']:
            self.mtWriter = mtphtWriter(self,self.fileDir,self.fileName)
            parmk = None
            if modName =='Pht3d':
                dicSpec = self.addin.pht3d.getDictSpecies()
                parmk = self.addin.pht3d.calcNbParm()
            else : 
                dicSpec ={'mcomp':1,'ncomp':1,'gcomp':1,'kim':[]}
            self.mtWriter.writeMtphtFiles(dicSpec,modName,parmk)
            self.transReader = mtphtReader(self.fileDir,self.fileName)   
        if modName[:5]  == 'Min3p':
            self.m3pWriter = min3pWriter(self,self.fileDir,self.fileName)
            self.m3pWriter.writeMin3pFiles(self,modName[5:])
            self.transReader=self.flowReader = min3pReader(self.fileDir,self.fileName)
        if modName[:5]  == 'Opgeo':
            self.ogWriter = ogWriter(self,self.fileDir,self.fileName)
            self.ogWriter.writeFiles(self,modName[5:])
            self.flowReader = ogReader(self.fileDir,self.fileName,'flow')
            self.transReader = ogReader(self.fileDir,self.fileName,'trans')
            self.flowReader.read = False
        if modName[:5]  == 'Sutra':
            self.sutraWriter = sutraWriter(self,self.fileDir,self.fileName)
            self.sutraWriter.writeSutraFiles()
            self.transReader=self.flowReader = sutraReader(self.fileDir,self.fileName)
            self.flowReader.read = False
        if info !=False :return 'files written'            
      
    def runModel(self,modName,info=True):
        tabRes, sep = [],os.sep
        lf = os.listdir(self.fileDir) 
        cfg = Config(self);#print cfg.typInstall
        if cfg.typInstall=='exe': self.baseDir += os.sep+'dist'
        if modName[:4] not in ['Opge','Min3','Sutr'] and self.fileName+'.nam' not in lf: 
            return 'Files not written'
        try : 
            b=unicode(self.baseDir).encode("utf-8")
            b=unicode(self.fileDir).encode("utf-8")
        except UnicodeEncodeError: return 'Bad caracters in folder name'
        if modName  == 'Modflow':
            mod = 'mf2k_PMwin'
            if 'NWT' in self.getUsedModulesList('Modflow'): mod = 'mfNWT_dev'
            if os.name == 'nt':
                exec_name = '"'+self.baseDir+sep+'bin'+sep+mod+'.exe"'
            else :
                exec_name = self.baseDir+sep+'mf2k '
            s=exec_name+' '+self.fileName+'.nam'
            os.chdir(self.fileDir)
            os.system(s)
            if info !=False :
                return self.getTxtFileLastLine(self.fileName+'.lst') #+'\nModflow run done'
        if modName == 'Mt3dms':
            mod1,mod2 = 'mt3dms5b','Mt3dms'
            if 'VDF' in self.getUsedModulesList('Mt3dms'): 
                mod1,mod2 ='swt_v4','Mt3dms'
            s=self.baseDir+sep+'bin'+sep+mod1+'.exe '+mod2+'.nam'
            os.chdir(self.fileDir)
            os.system(s)
            if info !=False :
                return self.getTxtFileLastLine('Mt3dms.out')#+'\n Mt3dms run done'
        if modName == 'Pht3d':
            s=self.baseDir+sep+'bin'+sep+'Pht3dv217.exe Pht3d.nam'
            os.chdir(self.fileDir)
            os.system(s)
            if info !=False :
                return self.getTxtFileLastLine('Pht3d.out')
        if modName == 'Sutra':
            s=self.baseDir+sep+'bin'+sep+'sutra_2_2.exe'
            os.chdir(self.fileDir)
            os.system(s)
            if info !=False :
                return self.getTxtFileLastLine(self.fileName+'.lst')
        if modName[:5] == 'Opgeo':
            s=self.baseDir+sep+'bin'+sep+'ogs.exe '+self.fileName+' >logfile.txt'
            os.chdir(self.fileDir)
            os.system(s)
            if info !=False :
                return self.getTxtFileLastLine('logfile.txt')
        if modName[:5] =='Min3p':
            s=self.baseDir+sep+'bin'+sep+'min3p.exe';#print s
            os.chdir(self.fileDir)
            pop = subprocess.Popen(s,stdin = subprocess.PIPE,stdout = subprocess.PIPE)
            #time.sleep(0.1)
            outp = pop.communicate(self.fileName+'\n')[0]
            if info !=False :
                return self.getTxtFileLastLine(self.fileName+'.log')
            
    def getTxtFileLastLine(self,fname):
        f1 = open(fname,'r')
        a= f1.read().split('\n')
        f1.close()
        return '\n'.join(a[-5:])
        
#********************** import and export functions *****************
    def importData(self,fileDir,fileName):
        importer = impFile(self.gui,self)
        dicData = importer.impTabFile(fileDir+os.sep+fileName+'.txt')
        self.data = dicData

    def importSolutions(self,fileDir,fileName):
        importer = impFile(self.gui,self)
        dicData = importer.impTabFile(fileDir+os.sep+fileName+'.txt')
        self.addin.pht3d.setImportedSolutions(dicData)
        
    def importZones(self,fileDir,fileName,modName,line):
        importer = impFile(self.gui,self)
        importer.impZones(fileDir,fileName,modName,line)
        
    def importLayerValues(self,fileName,spname):
        """import from existing txt files the concentrations of one given species 
        (this is for the restart option)
        """
        m0 = loadtxt(self.fileDir+os.sep+fileName) # first line layer numb from top to bott, 2nd :a value
        nlay,a = shape(m0)
        g = self.addin.getFullGrid();nx=g['nx'];dx=g['dx']
        m1 = tile(m0[-1::-1,1:],(1,nx));#print m1
        dim = self.addin.getDim()
        dictE = self.addin.pht3d.getDictSpecies();#print spname,dictE
        for kw in dictE.keys():
            if iterable(dictE[kw])==0: continue
            if spname in dictE[kw] : groupname = kw
        if dim =='Radial' and groupname in ['p','g','e','s']:
            for l in range(nlay): 
                m1[l] = m1[l]*(cumsum(dx)-dx/2.)*6.28;
        return m1
            
#********************* working with keywords and values***************            
    def createKwList(self):
        """creates a list of all keywords per model as a dict
        with the line and number for each kw
        """
        self.KwList={}
        for modName in self.modelList:
            self.KwList[modName]={}
            lines = self.dickword[modName].lines
            for ll in lines.keys():
                kw0=lines[ll]['kw']
                for ik in range(len(kw0)):
                    kw=kw0[ik].split('(')[0] # removes the dimension in ()
                    self.KwList[modName][kw]=(ll,ik)
        #print self.KwList
                    
    def setValue(self,modName,line,ik,value):
        """sets a value to a dicvalue place"""
        self.dicval[modName][line][ik] = value
        #print line,value
        if line in ['dis.6','dis.7'] : 
            self.Zblock = makeZblock(self);#print self.Zblock #top and bottom

    def getValueFromName(self,modName,vName):
        """returns a value from the name of the keyword"""
        #print modName,vName
        if (vName =='NLAY') and (self.addin.getDim() in ['Radial','Xsection']):
            return getNlayers(self)
        if vName in self.KwList[modName].keys(): # not needed
            line,ik = self.KwList[modName][vName]
            val = self.dicval[modName][line][ik];#print 'in getval',line,ik,val,type(val)
            return val
            
    def getSingleValueFromName(self,modName,vName):
        val = self.getValueFromName(modName,vName)
        if type(val)==type('r'): return float(val.split()[0])
        else : return float(val)
        
    def setValueFromName(self,modName,vName,value):
        if vName in self.KwList[modName]:
            line,ik=self.KwList[modName][vName]
            if type(value)==type([5]):
                self.dicval[modName][line] = value;#print vName,value
            else :
                dicv = self.dicval[modName][line]
                if ik<len(self.dicval[modName][line]):
                    self.dicval[modName][line][ik] = value
                else : 
                    self.dicval[modName][line].extend([0]*(ik-len(dicv)+1))
                    self.dicval[modName][line][ik] = value
        #print 'core setvn',vName,type(value),value,self.dicval[modName][line]

    def testCondition(self,modName,cond):
        """tests if a condition from the dictionnary is validated; 
        it allows to use several conditions in the same line"""
        a=True
        kwl=self.KwList[modName];#print kwl
        s1='self.getSingleValueFromName(modName,';
        if cond!='':
            cond=cond.replace(' and ',') and (')
            cond=cond.replace(' or ',') or (')
            for k in kwl:
                lk = len(k)
                if (cond[:lk]==k) or ('('+k in cond):
                    cond=cond.replace(k,s1+'\''+k+'\')')
            exec('a=('+cond+')')   
            #print 'core 415 cond',cond,a
        if a or cond=='': return True
        return False  

    def getSizeKw(self,modName,kw):
        """get the size of the object designed by a keyword (vector or array)"""
        if modName == 'Pht3d' : modName = 'Mt3dms' #the variables are located in mt3d
        size = [];
        a = kw.split('(')
        if len(a)==1 : return size
        b = a[1][:-1].split(',') # list of dimensions
        for s in b:
            n = self.getValueFromName(modName,s)
            size.append(int(n))
        return size

    def getValueLong(self,modName,line,ik):
        """get the vector or array of a keyword using the size of a vector, an array
        or a formula"""
        vtype = self.dictype[modName][line][0];#print 'core 422',vtype # type of value
        valIn = self.dicval[modName][line][ik]
        kw = self.dickword[modName].lines[line]['kw'][ik]
        cond = self.dickword[modName].lines[line]['cond']
        if self.testCondition(modName,cond)==False: return None
        size = self.getSizeKw(modName,kw)
        kw = kw.split('(')[0]
        numtype = self.dickword[modName].lines[line]['type'][ik];#int, float or lay
        #if line in ['dis.6','dis.7','btn.9','btn.10']: makeZblock(self), done in writers
        #print 'core 448',self.Zblock
        if line =='dis.6' : return self.Zblock[:-1] # several top
        if line =='btn.9' : return self.Zblock[0] # only the top        
        if line == 'dis.7': return self.Zblock[-1:] # one bottom
        if line == 'btn.10': return abs(self.Zblock[1:]-self.Zblock[:-1]) #[-1::-1]
        # generic writing
        if vtype=='one_value':
            if type(valIn)==type([5,6]): # case of a list
                value = array(valIn)
            else :
                if numtype[3:] in ['float','int']: # case of only one value
                    value = block(self,modName,line,intp=False) #value = ones(size)*valIn
        elif vtype in ['formula','interpolate']: # case of a formula
            exec(self.dicformula[modName][line][0])
            value = array(value,ndmin=3) # all spatial arrays are three dim
        elif vtype=='array':
            value = self.dicarray[modName][line]
            if type(value)==type([5]):value = value[0]
        elif vtype=='zone':
            value = block(self,modName,line,intp=False)
        else : #case of one string must be converted to float
            value = ones(size)*float(valIn)
        value = value.astype(numtype[3:])
        #print 'core',line,vtype,value
        return value
        
    def getUnits(self,modName,line,ik):   
        '''returns the units for a given line and keyword index'''
        s = ''
        if modName in ['Modflow','Mt3dms']:
            tlist = ['-','sec','min','hours','days','years']
            llist = ['-','ft','m','cm']
            tunit = tlist[self.dicval['Modflow']['dis.2'][4]]
            lunit = llist[self.dicval['Modflow']['dis.2'][5]]
            d0 = self.dickword[modName].lines[line];#print tunit,lunit
            if d0.has_key('units'): 
                s = d0['units'][ik];#print s
                s = s.replace('T',tunit)
                s = s.replace('L',lunit)
        return s
            
    def onPtObs(self,typ,iper,group,zname,esp,layers=0):
        """ get the values at observation zones, esp can be a list of species names"""
        # typ is breakthrough or profile  
        #print typ,iper,group,zname,esp,layers
        zlist=self.diczone['Observation'].dic['obs.1']
        nx,ny,xvect,yvect = getXYvects(self)
        grd = self.addin.getFullGrid()
        dim = self.addin.getDim();#print 'core 494',dim
        mtype = self.dicaddin['Model']['group'][:3]
        if typ[0]=='X': #XYplot
            ix=[];iy=[];typ='X0'
            for xy in zlist['coords']:
                x,y = zip(*xy)
                a,b,c = zone2index(self,x,y,x*1)
                ix.append(a[0]);iy.append(b[0])
            ix2=array(ix);iy2=array(iy);iz2=ix2*0.
            layers= [0]
        else:    
            ind = zlist['name'].index(zname)
            #print 'core l364',zlist['name'],zlist['coords'],ind
            x,y = zip(*zlist['coords'][ind])
            ix,iy,a,asin,acos = zone2index(self,x,y,x*1,'angle');#ix,iy are ipht indices (not modflow)
            if isclosed(self,x,y): # polygon
                iy,ix = where(fillZone(nx,ny,ix,iy,a));
            ix2,iy2,iz2,asin2,acos2=[],[],[],[],[]
            #add layers :can be '4','1,2','3-5'
            try: 
                layers=[int(layers)]
                ix2,iy2,iz2,asin2,acos2=ix*1,iy*1,layers*len(ix),asin,acos
            except ValueError:
                if '-' in layers :
                        l1 = layers.split('-')
                        layers = range(int(l1[0]),int(l1[1])+1)
                elif ',' in layers:
                    a = layers.split(',');layers = [int(x) for x in a]
                for il in layers: 
                    ix2.extend(ix);iy2.extend(iy);iz2.extend([il]*len(ix))
                    asin2.extend(asin);acos2.extend(acos)
        iym = [ny-y-1 for y in iy2] # transform to modflow coords
        t2 = self.getTlist2();#print 'core ptobs',layers,ix2,iy2,iz2,t2
        if typ[0]=='B': iper=range(len(t2)) # breakthrough
        else : iper = [iper]
        pt=[] # pt will be a list of tables (iper,irows) provided by the reader
        labels=['']
        ###### the cocnernend species (that can be head)
        if esp[0] in ['Head','Wcontent']: 
            for il in layers: # we may want data from several different layers
                if il!= -1: iz2=[il]*len(ix2)
                pt.append(self.flowReader.getPtObs(self,iym,ix2,iz2,iper,esp[0])); # irow,icol,ilay
                labels.append('lay'+str(il))
        elif group=='Transport':
            if mtype == 'Mod': opt ='Mt3dms'
            elif mtype =='Sut': opt = 'Tracer'
            for il in layers:
                if il!= -1: iz2=[il]*len(ix2)
                pt.append(self.transReader.getPtObs(self,iym,ix2,iz2,iper,opt)); # irow,icol,ilay
                labels.append('lay'+str(il))
        elif group=='Chemistry': 
            lesp = self.addin.chem.getListSpecies()
            for e in esp:
                iesp = lesp.index(e) 
                for il in layers:
                    if il!= -1: iz2=[il]*len(ix2)
                    pt.append(self.transReader.getPtObs(self,iym,ix2,iz2,iper,'Pht3d',iesp,e))
                    labels.append(e+'_lay'+str(il))
        else : pt=[1.] # for flux
        #print 'core 551',typ,esp,ix,ix2,iy,iy2
        ######## calculating the flux
        if typ[1]!='0' or esp[0]=='Flux': # to get the flux, shall be a matrix (nper,nrow)
            disx,disy = self.flowReader.getPtObs(self,iym,ix2,iz2,iper,'flux'); # provides the total flux from each cell
            disch = sqrt(disx**2+disy**2) # this is the discharge per cell
            thick = self.flowReader.getThicknessZone(self,iper,iz2,ix2,iym)
            dx,dy = grd['dx'][ix2],grd['dy'][iy2]; #print disx,ansin,dy,thick
            f1,f2 = disx*asin2/dy/thick,disy*acos2/dx/thick;#print disx,f1,disy,f2 # this is the flux
            flux = sqrt(f1**2+f2**2) #self.moyvect(f1)+self.moyvect(f2)) # flux shall be a vector
            flux[flux<1e-8]=1e-8
            #print dx,dy,iy2,asin2,acos2,disch,flux,thick
        if esp[0] in ['Head','Wcontent']: typ=typ[0]+'0'
        xzon=xvect[ix2];yzon=yvect[iy2];
        if typ[0]=='B':  ########### Breakthrough
            p1=zeros((len(t2),len(pt))) # p1 : to make a table of (ntimes,nspecies)
            labels[0]='time'; 
            for i in range(len(pt)):
                if typ[1]=='0': p1[:,i]=mean(pt[i],axis=1); #conc, pt[i] is a table (nper,nrow)
                elif typ[1]=='1': p1[:,i]=sum(pt[i]*flux,axis=1)/sum(flux,axis=1) # weighted conc
                elif typ[1]=='2': p1[:,i]=sum(pt[i]*disch,axis=1); #total discharge
                elif typ[1]=='3': p1[:,i]=mean(pt[i]*flux,axis=1); #average flux
            return t2,p1,labels
        elif typ[0]=='P':  ############ Profile
            d0=sqrt((xzon[1:]-xzon[:-1])**2.+(yzon[1:]-yzon[:-1])**2.)
            dist = concatenate((array(0.,ndmin=1),cumsum(d0)))
            p1=zeros((len(dist),len(pt)))
            labels[0]='distance'
            for i in range(len(pt)):
                if typ[1]=='0': p1[:,i]=pt[i]
                elif typ[1] in ['1','3']: p1[:,i]=pt[i]*flux # weigthed conc= darcy flux
                elif typ[1]=='2': p1[:,i]=pt[i]*disch #discharge or mass discharge
            return dist,p1,labels
        elif typ[0]=='X': # XY plot
            indCol = self.data['cols'].index(esp[0])
            mes=self.data['data'][:,indCol];
            p1=zeros((len(mes),1));p1[:,0]=pt[0];
            return mes,p1,'correl'
            
    def diffvect(self,v):
        v= v[1:]-v[:-1]
        return concatenate([v,v[-1:]])
        
    def moyvect(self,v):
        v1= (v[2:]+v[1:-1]+v[:-2])/3
        return concatenate([v[:1],v1,v[-1:]])
        
class dicZone:
    """it is a dictionnary of zones, ordered by lines, each model has one dic"""
    def __init__(self,parent,modName):
        self.dic = {}
        groups = parent.dickword[modName].groups
        lines = parent.dickword[modName].lines
        self.dicLines,self.dicLinesComm = {},{}
        for g in groups.keys():
            self.dicLines[g] = []
            self.dicLinesComm[g] = []
            for ll in groups[g]:
                if lines[ll]['type'][0][:3] == 'arr':
                    self.dicLines[g].append(ll)
                    self.dicLinesComm[g].append(lines[ll]['comm'][:25])
            if len(self.dicLines[g])==0 : 
                self.dicLines.pop(g,None)
                self.dicLinesComm.pop(g,None)
        #print 'core zones',self.dicLines
                
    def setDic(self,dic) :
        self.dic = dic           
    def getLinesDic(self):
        return self.dicLines
    def getLinesCommDic(self):
        return self.dicLinesComm    
        
    def getNbZones(self,line):
        if self.dic.has_key(line):
            return len(self.dic[line]['name'])
        else : return 0
        
    def setValueFromName(self,line,zname,val):
        for i,n in enumerate(self.dic[line]['name']):
            if n == zname : self.dic[line]['value'][i] = val
            
    def getIndexFromName(self,line,zname):
        for i,n in enumerate(self.dic[line]['name']):
            if n == zname : return i
            
    def getLineAndIndexFromName(self,zname):
        for line in self.dic.keys():
            for i,n in enumerate(self.dic[line]['name']):
                if n == zname : return line,i
                               
    def getValue(self,line,parameter,nb):
        return self.dic[line][parameter][nb]
    def setValue(self,line,parameter,nb,value):
        self.dic[line][parameter][nb] = value

    def getMediaList(self,line,nb):
        md =  self.dic[line]['media'][nb]
        if type(md)==type([5,6]): return md
        else : return [md]
                   
    def addZone(self,line):
        if line not in self.dic.keys():
            self.dic[line]={'number':[''],'name':[''],'coords':[''],'media':[''],'value':[''],'type':['']}
        else :
            for k in self.dic[line].keys():
                self.dic[line][k].append('')
        self.dic[line]['number'][-1] = self.getNbZones(line)
            
    def delZone(self,line,iz):
        for k in self.dic[line].keys():
            self.dic[line][k].pop(iz)
        nbz = self.getNbZones(line)
        self.dic[line]['number'] = range(nbz)
        
    def getTableOfZones(self,line):
        table = zip(self.dic[line]['name'],self.dic[line]['media'],self.dic[line]['value'])
        return table
