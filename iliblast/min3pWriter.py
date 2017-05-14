# -*- coding: utf-8 -*-
"""
Created on Sun Oct 19 12:54:49 2014

@author: olive
"""
from array import array as arr2
import os
from pylab import savetxt,loadtxt
import min3pFlowKeywords as Fkey
import min3pTransKeywords as Tkey
import min3pChemKeywords as Ckey
#from core import *
from geometry import *
from timeperiod import *

class min3pWriter:
    
    def __init__(self, core,fDir, fName):
        self.core = core
        self.fDir,self.fName = fDir,fName
        self.fullPath = fDir+os.sep+fName;#print self.fullPath
        self.fileKeys = {'poro.1':['porosity field','por'], # to write in files
                'flow.1':['hydraulic conductivity field','hyc'],
                'flow.4':['specific storage coefficient','spstor']}

    def writeMin3pFiles(self, core, option):
        #option Flow, Trans or Chem
        self.core = core
        self.chem = self.core.addin.chem
        f1=open(self.fullPath +'.dat','w')
        self.ttable = core.makeTtable();#print 'mfw',self.ttable
        tlist = array(self.ttable['tlist'])
        self.per = tlist[1:]-tlist[:-1]
        self.nper = len(self.per)
        self.core.Zblock = makeZblock(self.core);#print 'mfw,zb',shape(self.core.Zblock)
        self.xsect = False
        if self.core.addin.getDim() == 'Xsection': self.xsect = True
        self.domn=[]
        for n in ['Xmin','Xmax','Ymin','Ymax','Zmin','Zmax']:
            self.domn.append(self.core.getValueFromName('Min3pFlow',n))
        self.grid = self.core.dicaddin['Grid']
        s=''
        lgrp=['glo','spat','time','out','poro','flow','inif','bcf','conf']
        if option == 'Trans': lgrp.extend(['cont','trans','trac','init','bct'])
        elif option == 'Chem': lgrp.extend(['cont','trans','conc','inic','bcc'])
        for grp in lgrp:
            #print 'group',grp
            if grp in Fkey.grpList:
                if grp not in self.core.addin.getUsedModulesList('Min3pFlow'):continue
                self.dicval = core.dicval['Min3pFlow']
                s+='!-------------------------\n\''+Fkey.longNames[grp]+'\'\n'
                s+=self.writeBlock('Min3pFlow',Fkey,grp,Fkey.groups[grp])
            elif grp in Tkey.grpList:
                self.dicval = core.dicval['Min3pTrans']
                s+='!-------------------------\n\''+Tkey.longNames[grp]+'\'\n'
                s+=self.writeBlock('Min3pTrans',Tkey,grp,Tkey.groups[grp])
            elif grp in Ckey.grpList:
                self.dicval = core.dicval['Min3pChem']
                s+='!-------------------------\n\''+Ckey.longNames[grp]+'\'\n'
                s+=self.writeBlock('Min3pChem',Ckey,grp,Ckey.groups[grp])
        if option == 'Chem': 
            s+= self.writeGeochem()
            self.writeDatabases()
        f1.write(s)
            
    def writeBlock(self,mod,Dict,grp,llist):
        if grp in ['glo','spat','time','out','trac','conf','cont','conc']: 
            s = self.writeGeneral(mod,Dict,grp,llist)
        else :
            s = self.writeByZones(mod,Dict,grp,llist)
        return s
            
    def writeGeneral(self,mod,Dict,grp,llist):
        s = '';#print llist
        for l in llist:
            line = l*1;#print line
#            if self.xsect and l == 'spat.2': line = 'spat.3' # for coords inversion
#            if self.xsect and l == 'spat.3': line = 'spat.2'
            cond=Dict.lines[line]['cond'];#print line
            if self.core.testCondition(mod,cond)==False : continue
            kwlist=Dict.lines[line]['kw']
            ktyp=Dict.lines[line]['type'];#print 'mfw',ktyp
            lval=self.dicval[line]
            name = Dict.lines[line]['comm']
            name=name.split('(')[0]
            if line[:4] not in ['spat','time']: 
                s += '\''+name+'\'\n'
            for ik in range(len(kwlist)):
                value=lval[ik];#print line,value
                if ktyp[ik]=='choice': # where there is a choice print the nb othe choice not value
                    choi = Dict.lines[line]['detail'][ik][value+1]
                    sep = '\''
                    if choi in ['true','false']: sep='.'
                    s += sep+choi+sep+'\n'
                elif ktyp[ik]=='title': # case of a title line
                    s += '#'+str(value)+'\n'
                else : # values with strings
                    if line in ['trac.2']: 
                        value = '\''+self.core.gui.mainDir+os.sep+'utils\''
                    if line == 'out.1':
                        value = self.getTimeList()
                    s += str(value)+'\n'
        return s+'\n\'done\'\n\n'
        
    def writeByZones(self,mod,Dkeys,grp,llist):
        s=''
        #write total nb of zones
        nbztot = self.getNbZones(mod,llist) # total nb of zones for list of lines
        zandaquif = llist[0][:3]=='ini'
        nbz = zandaquif*1
        s+= str(max(nbztot+nbz,1))+'\n\n'
        if nbztot==0 or zandaquif:
            s += '\'number and name of zone\'\n1\n\'aquifer\'\n'
            for line in llist:
                #print grp,line
                info = Dkeys.lines[line]['comm'].split('(')[0]
                if info != 'porosity': 
                    s += '\''+info+'\'' + '\n'
                s += self.getValue(Dkeys,mod,line,None,0,'whole')
                if line == 'trans.1': s+= self.getDiffusion()
            s += '\'extent of zone\'\n\n'
            s += self.getDomainCoords()
            s += '\n\'end of zone\'\n'
        for line in llist:
            #print line
            if line not in self.core.diczone[mod].dic.keys(): continue
            dicz = self.core.diczone[mod].dic[line]
            nbzline = len(dicz['value'])# nb of zones for this line
            if line[:2] in ['bc','in']: # only boundary and initial conditions have zone here
                for iz in range(nbzline):
                    #for this zone write nb and name
                    nbz += 1
                    s += '\'number and name of zone\'\n'+ str(nbz) +'\n'
                    s += '\''+dicz['name'][iz]+'\''  + '\n'
                    # for this zone write type of information and value
                    info = Dkeys.lines[line]['comm'].split('(')[0]
                    if line[:2] =='bc': s += '\'boundary type\'\n'
                    s += '\''+info+'\''  + '\n'
                    s += self.getValue(Dkeys,mod,line,dicz,iz,'zone')
                    # for this zone write extent
                    s += '\'extent of zone\'\n'
                    s += self.getCoords(dicz['coords'][iz],line) +'\n'
                    s += '\'end of zone\'\n\n'
            else : # spatial data must be stored in a file
                if line in ['flow.2','flow.3']: continue #already written with flow1
                self.writeDistributedFile(line,self.getFileKwd(line,1))
                s += '\'read '+self.getFileKwd(line,0)+' from file\'\n'
                nbztot=0
        s += '\'done\'\n\n'
        return s
        
    def getValue(self,Dkeys,mod,line,dicz,iz,opt):
        """get the values for zones or for the wole domain
        allow to get the chemistry from solutions too
        """
        prefx=''
        if Dkeys.lines[line].has_key('prefx'): prefx = Dkeys.lines[line]['prefx']
        suffx=''
        if Dkeys.lines[line].has_key('suffx'): suffx = Dkeys.lines[line]['suffx']
        s = ''
        if opt =='whole':
            for v in self.core.dicval[mod][line]:
                if line.split('.')[0] in ['bcc','inic']:
                    v = self.getStringFromSolution(line,0) # here, this is the background
                else :
                    v = ' %+11.4e' %float(v)
                    v = v.replace('e','d')
                s += prefx + v +' '+ suffx +'\n'
        elif opt == 'zone':
            dicz = self.core.diczone[mod].dic[line];
            if line.split('.')[0] in ['bcc','inic']: # this is the only place where solutions are required
                v = self.getStringFromSolution(line,int(dicz['value'][iz]))
            else :
                v = ' %+11.4e' %float(dicz['value'][iz])
                v =  v.replace('e','d')
            s += prefx +v +' '+ suffx + '\n'
        return s
        
    def getStringFromSolution(self,line,value):
        """provide the string for the solution (or mineral) composition
        given by value as 1000 (like for pht3d) or 1210
        for initial and boundary conditions
        """
        if line[:4]=='inic':
            nsol,nmin = value/1000,mod(value,1000)/100 #,mod(value,100)/10,mod(value,10)
        else :
            nsol = value
        #lgrp = ['comp','mineral','sorption','sorption']
        #lnames = ['concentration input','mineral input','sorption parameter input','sorption parameter input']
        # solutions
        dChem = self.core.addin.chem.Base['MChemistry']['comp']
        s = ''
        if line[:3] == 'bcc': s = '\'concentration input\' \n'
        for ir,row in enumerate(dChem['rows']):
            if dChem['data'][ir][0]: #the species is ticked
                s += str(dChem['data'][ir][nsol+1]).replace('e','d')+'  \''+\
                    dChem['data'][ir][-1]+'\'  ;'+row+'\n' # last columns contains 'free', 'ph'...
        if line[:3] == 'bcc': return s
        # linear sorption
        dChem = self.core.addin.chem.Base['MChemistry']['linear sorption']
        sl = ''
        for ir,row in enumerate(dChem['rows']):
            if dChem['data'][ir][0]: #the species is ticked
                sl += '\''+row+'\'  '+str(dChem['data'][ir][nsol+1])+' \n' 
        if sl != '': s += '\'linear sorption input\' \n' + sl +'\n'
        #minerals
        dChem = self.core.addin.chem.Base['MChemistry']['mineral']
        s += '\'mineral input\' \n'
        for ir,row in enumerate(dChem['rows']):
            if dChem['data'][ir][0]: #the species is ticked
                data = dChem['data'][ir]
                s += str(data[nmin+1]).replace('e','d')
                s += '  '+data[5]+' \''+data[6]+'\' ; '+dChem['rows'][ir]+'\n'
                s1 = ' '.join([str(a) for a in data[7:]])
                s += s1.replace('e','d')+'\n'
        return s
        
    def getNbZones(self,mod,llist):
        nbz=0
        dicz = self.core.diczone[mod]
        for line in llist:
            if dicz.dic.has_key(line):
                nbz += dicz.getNbZones(line) # nb of zones
        return nbz
        
    def getDomainCoords(self):
        s = ''
        for i in range(6):
            s+= str(self.domn[i])+'  '
        return s

    def getCoords(self,coolist,line):
        #returns a formatted string of coords from the ipht3d list
        # only for 2D up to now
        if line[:2]=='bc': coolist = self.coord2BC(coolist)
        xl,yl = zip(*coolist)
        s0 = str(min(xl))+' '+str(max(xl))+' '
        s1 = str(min(yl))+' '+str(max(yl))+' '
        s2 = str(self.domn[4])+'  '+str(self.domn[5])+'  '
        if self.xsect : s = s0+s2+s1
        else : s = s0+s1+s2
        return s
        
    def coord2BC(self,coolist):
        dx,dy = float(self.grid['dx'][0]),float(self.grid['dy'][0])
        coo2 = range(len(coolist))
        cooy = self.domn[2:4]
        if self.core.addin.getDim() == 'Xsection': cooy = self.domn[4:6]
        for i,c in enumerate(coolist):
            x,y = c; 
            if abs(x-self.domn[0])<dx : x = self.domn[0]
            if abs(x-self.domn[1])<dx : x = self.domn[1]
            if abs(y-cooy[0])<dy : y = cooy[0]
            if abs(y-cooy[1])<dy : y = cooy[1]
            coo2[i]=(x,y)
        #print 'mpw l244', self.domn,cooy,coolist,coo2
        return coo2
        
    def getTimeList(self):
        tlist = self.core.getTlist2()
        s = str(len(tlist))+'\n'
        for i in range(len(tlist)):
            if mod(i,4)==0: s+='\n'
            s += str(tlist[i])+' '
        return s
        
    def getFileKwd(self,line,i):
        return self.fileKeys[line][i]
        
    def writeGeochem(self):
        #creates the geochemical system block from chem database
        # ! redox are only considered as kinetics up to now
        lgrp = ['comp','complex','redox','gases','sorption','mineral']
        lnames = ['components','secondary aqueous species','intra-aqueous kinetic reactions','gases',
                  'sorbed species','minerals']
        s = '!-----------------------------\n\'geochemical system\'\n'
        s += '\'use new database format\'\n\n\'database directory\'\n'
        s += '\''+self.fDir+'\'\n\n'
        for a in zip(lgrp,lnames):
            group,name = a;#print a,group,name
            l = self.chem.getListSpecies(group)
            if group == 'comp': l.remove('ph');l.remove('pe')
            if len(l)>0 :
                s += '\''+name + '\'\n' # name of process
                s += str(len(l)) +'\n\'' # nb of solutes
                s += '\'\n\''.join(l)
                s += '\'\n\n'
        # add linear sorption
        l = self.chem.getListSpecies('linear sorption')
        if len(l)>0:
            s += '\'linear sorption\'\n' +str(len(l))+'\n'
            for n in l:
                s += '\''+n+'\' \n'
            s += '\n'
        # add non aqueous conc for surface (it's name)
        l = self.chem.getListSpecies('sorption')
        if len(l)>0:
            s += '\'non-aqueous components\'\n' +str(len(l))+'\n'
            for n in l:
                s += '\''+n+'\' \n'  
            s += '\n'
        # add scaling for kinetics
        l = self.chem.getListSpecies('redox')
        if len(l)>0:
            s += '\'scaling for intra-aqueous kinetic reactions\'\n'
            dChem = self.chem.Base['MChemistry']['redox']
            for n in l:
                indx = dChem['rows'].index(n)
                s += dChem['data'][indx][1] +'\n'
        # add complexes
        s += self.findComplexes()
        return s+'\n\'done\'\n'
        
    def getDiffusion(self):
        diffChoice = self.core.getValueFromName('Min3pTrans','Diff_choice')
        if diffChoice==0: # no dusty gas
            return ''
        elif diffChoice==1 : s = '\n\'binary gas diffusion coefficients\' \n'
        elif diffChoice==2 : s = '\n\'dusty gas model\' \n'
        base = self.chem.Base['MChemistry']['gases']
        glist = base['rows']
        ng = len(glist)
        if diffChoice==1:
            for ig in range(ng):
                for i2 in range(ig+1,ng):
                    diff = self.calcDij(base['data'][ig][3:],base['data'][i2][3:])
                    suff = '  ;'+glist[ig]+'-'+glist[i2] # just the names for comments
                    s += str(diff).replace('e','d')+suff+'\n'
        # writes gas couples for dusty gas, data: wilke visco(2), LJ sigma and LJ e/K
        elif diffChoice==2:
            for ig in range(ng):
                for i2 in range(ig+1,ng):
                    diff = base['data'][ig][1]
                    if diff =='LJ': diff = 1e-7
                    suff = '  ;'+glist[ig]+'-'+glist[i2] # just the names for comments
                    s += str(diff).replace('e','d')+suff+'\n'
            # writes wilke viscosisty
            for ig in range(ng):
                visco = base['data'][ig][2]
                s += str(visco).replace('e','d')+'  ;'+glist[ig]+'\n'
            # writes lennard and jones parameters
            s += '\n\'lennard-jones\'\n'
            for ig in range(ng):
                LJ = base['data'][ig][3:]
                s += str(LJ[0])+'  '
                s += str(LJ[1])+'  ;'+glist[ig]+'\n'
        return s + '\n'
        
    def calcDij(self,data1,data2):
        """cal coeff diffusion in cm2/s for two species from chapman enskog theroy"""
        sig1,eK1,m1 = [float(a) for a in data1]
        sig2,eK2,m2 =  [float(a) for a in data2]
        sig_12 = (sig1+sig2)/2 # collision diameter in angstrom
        eps12_K = sqrt(eK1*eK2) # it is eps/kb for each species
        T = 293 # temperature K
        p = 1 # pressure atm
        kbT_e = T/eps12_K # kboltz*Temp/epsilon
        Omega = 0.9 + 0.5/kbT_e-log10(kbT_e)/4.8 # approcimation from table 2.1
        D12 = 0.00186*T**1.5*sqrt(1/m1+1/m2)/(p*sig_12**2*Omega)*1e-4
        return D12
             
    def findComplexes(self):
        """ finds the potential list of complexes by looking into the complex.dbs file"""
        lsp = self.chem.getListSpecies('comp')
        lsp1 = ['oh']
        for sp in lsp: # find the charge and the species without charge
            if '+' in sp: 
                sp1 = sp.split('+');lsp1.append(sp1[0]) #,int('+'+sp1[1])))
            elif '-' in sp: 
                sp1 = sp.split('-');lsp1.append(sp1[0]) #,int('-'+sp1[1])))
        #print lsp1
        if 'complex' not in self.chem.temp['Dbase'].keys():
            self.chem.importDB(self.chem.Base['MChemistry'])
        lcplx,a = zip(*self.chem.temp['Dbase']['complex'])
        #for each complex try to remove the existing species: if nothing left the complex is correct
        l = []
        for cp in lcplx :
            cp0,count = cp *1,0
            for sp in lsp1:
                if sp in cp0: 
                    cp0 = cp0.replace(sp,'');count += 1;
            if len(cp0)==0 : l.append(cp)
            else :
                if count ==2 and sum(a.isalpha() for a in cp0)==0: l.append(cp)
        if len(l)==0: return ''
        s = '\n\'secondary aqueous species\'\n'
        s += str(len(l))+'\n\''
        s += '\'\n\''.join(l)
        return s+'\'\n'
        
    def writeDatabases(self):
        """writes the databases locally using only species used"""
        for name in ['comp','gases','complex','sorption','redox','mineral']:
            fil1 = self.core.gui.mainDir+os.sep+'utils'+os.sep+name+'.dbs'
            fil2 = self.fDir+os.sep+name+'.dbs'
            os.system('copy '+fil1+' '+fil2)
        for name in ['redox','mineral']:
            if len(self.chem.Base['MChemistry'][name]['rows'])>0:
                f1 = open(self.fDir+os.sep+name+'.dbs','w')
                f1.write(self.chem.writeDb(name))
                f1.close()

    def writeDistributedFile(self,line,extension):
        """ to write a file with values distributed on the grid, 
        get the object from zone and call write function for external file"""
        if line[:4] in ['poro','trans']: modn = 'Min3pTrans'
        else : modn = 'Min3pFlow'
        coords =  getMesh3D(self.core) # in x,y,z order
        mat = [self.core.getValueLong(modn,line,0)]
        if line=='flow.1':
            mat.append(self.core.getValueLong(modn,'flow.2',0))
            mat.append(self.core.getValueLong(modn,'flow.3',0))
        self.writeExtFile(self.fullPath+'.'+extension,coords,mat)
        
    def writeExtFile(self,name,coords,mat):
        # formats and write the object
        f1=open(name,'w')
        s = 'title 1 \n title 2 \n title 3 \n'
        nvar = len(mat)
        nz,ny,nx = shape(mat[0])
        X,Y,Z = coords
        for iz in range(nz):
            for iy in range(ny):
                for ix in range(nx): 
                    s += str(X[iz,iy,ix])+' '+str(Y[iz,iy,ix])+' '+str(Z[iz,iy,ix])
                    for iv in range(nvar): 
                        s += ' '+str(mat[iv][iz,iy,ix])
                    s += '\n'
        f1.write(s)
        f1.close()
            
class min3pReader:
    
    def __init__(self,fDir, fName):
        self.fDir,self.fName = fDir,fName
        self.fullPath = fDir+os.sep+fName;#print self.fullPath
        
    def readOutput(self,ext):
        """reads an output file from Min3p, with three head lines
        and retrieves a matrix of correct shape (nvar,z,y,x)
        gst : total conc, gsm : general (pH, Alk...), gsc : ion conc (incl complex)
        gsp : pressure wcontent"""
        f1 = open(self.fullPath+ext)
        a = f1.readline();a = f1.readline();a = f1.readline()
        f1.close()
        b = a.split('=')
        self.makeNcells()
        nz,ny,nx = self.ncells;#print 'mpwrite l327',nz,ny,nx
        if ext[-3:]=='vel': # velocity have diff shape
            nx,ny,nz = max(nx-1,1),max(ny-1,1),max(nz-1,1)
        mat = loadtxt(self.fullPath+ext,skiprows = 3)
        nr,nc = shape(mat);#print nr,nc
        mat2 = zeros((nc-3,nz,ny,nx));
        for iv in range(nc-3):
            mat2[iv] = reshape(mat[:,iv+3],(nz,ny,nx))
        #print 'mnpw l330',shape(mat2),mat2
        return mat2
        
    def readHeadFile(self,core,iper):
        self.core = core
        hd = self.readOutput('_'+str(iper+1)+'.gsp')[0] # first variable is head
        return hd

    def readWcontent(self,core,iper):
        self.core = core
        wc = self.readOutput('_'+str(iper+1)+'.gsp')[3] # 3rd variable is theta_w
        return wc

    def readFloFile(self,core,iper):
        self.core = core
        vel = self.readOutput('_'+str(iper+1)+'.vel')[0:2];
        nv,nz,ny,nx = shape(vel);#print 'redflo',shape(vel)
        # velocity have diff shape
        vel = concatenate((vel[:,:,:,:1],vel,vel[:,:,:,-1:]),axis=3);#print 'redflo',shape(vel)
        vel = vel[:,:,:,1:]/2+vel[:,:,:,:-1]/2;#print 'redflo',shape(vel)
        if ny>1:
            vel = concatenate((vel[:,:,:1,:],vel,vel[:,:,-1:,:]),axis=2);#print 'redflo',shape(vel)
            vel = vel[:,:,1:,:]/2+vel[:,:,:-1,:]/2;#print 'redflo',shape(vel)
        if nz>1:
            vel = concatenate((vel[:,:1,:,:],vel,vel[:,-1:,:,:]),axis=1);#print 'redflo',shape(vel)
            vel = vel[:,1:,:,:]/2+vel[:,:-1,:,:]/2;#print 'redflo',shape(vel)
        return vel

    def readUCN(self,core,option,iper,ispec,specname):
        self.core = core
        if specname =='ph':
            cnc = self.readOutput('_'+str(iper+1)+'.gsm')[0] #pH first species
            return cnc
        if specname =='pe':
            cnc = self.readOutput('_'+str(iper+1)+'.gsm')[1] #pH first species
            return cnc
        lgrp = ['comp','gases','mineral']
        suff = ['t','g','v'] # totals, gases, mineral vol fraction
        for i,grp in enumerate(lgrp): 
            slist = self.core.addin.chem.getListSpecies(grp)
            if specname in slist:
                indx = slist.index(specname);#print 'mnpw l 401',specname,slist,indx
                cnc = self.readOutput('_'+str(iper+1)+'.gs'+suff[i])[indx] 
        return cnc
        
    def makeNcells(self):
        mat = self.core.getValueLong('Min3pFlow','flow.1',0) # just to get dimensions
        self.ncells = shape(mat)
        
    def getPtObs(self,core,irow,icol,ilay,iper,option,ispec=0,specname=''):
        """get an observation point or a list of obs points for one period
        up to now, no different periods"""
        if core.addin.getDim() in ['Xsection','Radial']:
            ilay=irow*1;irow=[0]*len(ilay)
        if option in ['Mt3dms','Pht3d']: # transport or chemistry
            obs = self.readUCN(core,option,iper[0],ispec,specname)[ilay,irow,icol]
        elif option == 'head':
            obs = self.readHeadFile(core,iper[0])[ilay,irow,icol]
        elif option == 'Wcontent':
            obs = self.readWcontent(core,iper[0])[ilay,irow,icol]
        elif option == 'flux': 
            obs = self.readFloFile(core,iper[0])[:,ilay,irow,icol]
        return obs
        
