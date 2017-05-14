"""PEST utility for iPht3D :
steps :
1. ipht3d seek for the pest_parm.txt file
the parameters have to start with MF, MT or PH for modflow, mt3d or pht3d
This file must be in the same folder than the ipht3d file
for permeability : use MFKz1 where z1 is the name of the zone of interest
for dispersivity : MTPaL or MTPaT MTPaZ
for source zone coordinates in transport : write MTx +name of the zone and MTy...
the format of each line is the same as in the pst file
observation model input are not read from this file
they will be produced

2. from this file ipht3d produces the template files (.tpl) for pest
and a batch file (runmod.bat)

3. ipht3d reads files starting as pest_obs that contain the observed values
one line per observation zone, can contain layer ($l7)  name :pest_obs.txt
start with line headers that are the zone namen, time and observed variables names


4. ipht3d writes in the same folder a script to read data and write them in a correct
format in a txt file (out_..)

5. then pest is run by the user in a cmd window (using runmod.bat)
for each pest run, the python script is run"""

# all imports
import os,sys
from pylab import loadtxt,savetxt
from config import *

class Pest:
    def __init__(self,core):
    # get all important parameters from the current model (names and timelist)
        self.tlist = core.getTlist2()
        d0,self.fname = core.fileDir,core.fileName
        d1=d0.split(os.sep)
        self.fdir = '//'.join(d1)
        d0=core.baseDir # main directory
        d1=d0.split(os.sep)
        self.mdir = '//'.join(d1)
        sys.path.append(self.mdir)
        
    def readPst(self):
    # reads the pest_parms.txt file
        f1=open(self.fdir+os.sep+'pest_parms.txt','r');
        ind=0;self.parm=[];self.pstring=''
        for l in f1:
            if len(l)>5: self.pstring+=l;self.parm.append(l.split())
        f1.close()
        #print self.parm

    def writeTpl(self):
        # change the values in the model to initial ones and writes the files
        dicMF={'K':'Permeabilite'}
        self.prtMF,self.prtMT,self.prtPH,self.nbgparm=False,False,False,0
        kparm=[];s='ptf @ \n'
        print 'reading parameters'
        for pl in self.parm:
            name=pl[0];v0=pl[3];grp=name[:2];catg=name[2];print name
            gp=pl[6];self.nbgparm=int(gp[1:])
            s+=name+' @'+name+'@ \n'
            if grp=='MF': self.prtMF=True
            elif grp=='MT': self.prtMT=True
            elif grp=='PH': self.prtPH=True
        f1=open(self.fdir+os.sep+'pest_tpl.txt','w')
        f1.write(s);f1.close()
        self.ntfiles=1
        
    def writeBat(self):
    # produce the runmod.bat file
        s='python scriptPest1.py \n'
        if self.prtMF: s+=self.mdir+'\\bin\\mf2k_Pmwin.exe '+self.fname+'\n'
        if self.prtMT: s+=self.mdir+'\\bin\\mt3dms5b.exe Mt3dms \n'
        if self.prtPH: s+=self.mdir+'\\bin\\pht3dv217.exe Pht3d \n'
        s+='python scriptPest2.py'
        f1=open(self.fdir+os.sep+'runmod.bat','w')
        f1.write(s);f1.close()
        print 'runmod.bat written'
        
    def getObsPt(self):
    # get the observation files and gathers data in one dict
        os.chdir(self.fdir)
        ldir=os.listdir(self.fdir);
        self.onames=[]; # list of observation points or zones
        self.ospec=[]; # list of observed species
        self.obs=[] #dict that will contain the observed data
        self.nbobs=0 #number of observation
        self.nifiles=0;self.fact=[]
        print 'reading observation'
        f1=open('pest_obs.txt','r') #a file with all obs, 1st col obs point, 2nd time, then variables
        titl=f1.readline().split()
        obs_old,nl,nc = '',0,len(titl)-2
        for l in f1:
            nl += 1
            l1 = l.split()
            if obs_old =='': somm=zeros((len(l1)-1))
            obs_new = l1[0]
            #print l1[1:]
            a1 = array([float(x) for x in l1[1:]],ndmin=2)
            if obs_new != obs_old:
                self.onames.append(obs_new)
                self.ospec.append(titl[2:])
                if obs_old !='':self.obs.append(arr)
                arr = a1*1
                obs_old = obs_new
            else : 
                arr = concatenate([arr,a1],axis=0)
            somm = somm+a1
        self.obs.append(arr) # last one
        f1.close()
        #self.nifiles = len(self.onames)
        self.nbobs = nl*nc
        self.fact = float(nl)/somm;#print 'pest',self.fact
        #print self.onames,self.ospec,self.obs
                    
    def writeInst(self):
    # write the instruction files
        os.chdir(self.fdir)
        s='pif @ \n'
        n=1
        f1=open('pest.ins','w')       
        for i in range(len(self.onames)):
            name=self.onames[i]
            a=shape(self.obs[i])
            if len(a)==1: nline,ncol=1,len(self.obs[i])
            else : nline,ncol = a
            for j in range(nline):
                s+='l1 '
                for k in range(ncol-1):
                    s+='['+self.ospec[i][k]+str(n)+']'+str((k+1)*10+1)+':'+str((k+2)*10)+' '
                s+=' \n';n+=1
        f1.write(s);f1.close()
        print 'instruction file written'
            
    def writePyscript(self):
    # writes the pyton script to write data before model run
        os.chdir(self.mdir+os.sep+'ilibq')
        f1=open('tplPestScript1.txt','r')
        s=f1.read();f1.close()
        os.chdir(self.fdir)
        s=s.replace('ppmdir',self.mdir)
        s=s.replace('ppfdir',self.fdir)
        s=s.replace('ppfname',self.fname)
        f1=open(self.fdir+os.sep+'scriptPest1.py','w')
        f1.write(s);f1.close()
    # writes the pyton script to retrieve data after model run
        os.chdir(self.mdir+os.sep+'ilibq')
        f1=open('tplPestScript2.txt','r')
        s=f1.read();f1.close()
        os.chdir(self.fdir)
        s=s.replace('ppmdir',self.mdir)
        s=s.replace('ppfdir',self.fdir)
        s=s.replace('ppfname',self.fname)
        tlist=[]
        for i in range(len(self.obs)):
            if len(shape(self.obs[i]))==1:
                tlist.append(list(self.obs[i]))
            else :
                tlist.append(list(self.obs[i][:,0]))
        s=s.replace('pptime',str(tlist))
        s=s.replace('pponames',str([str(a) for a in self.onames]))
        s=s.replace('ppospec',str(self.ospec))
        f1=open(self.fdir+os.sep+'scriptPest2.py','w')
        f1.write(s);f1.close()
        print 'pyscripts written'
        
    def writePst(self):
    # rewrites the pst file
        nbgroup,nifiles=1,1
        s='pcf \n* control data \n restart estimation\n'
        s+=str(len(self.parm))+' '+str(self.nbobs)+' '+str(self.nbgparm)+' 0 1 \n'
        s+=str(self.ntfiles)+' '+str(nifiles)+' single point 1 0 0 \n'
        s+='5.0 2.0 0.3 0.01 10\n'
        s+='5.0 5.0 0.001 \n.1 \n30 .005 3 3 .005 3 \n 1 1 1 \n'
        s+='* group definitions and derivative data \n'
        for i in range(self.nbgparm):  # nb of groups of parameters
            s+='G'+str(i+1)+' relative  .01  0 always_2  1 parabolic \n'
        s+='* parameter data \n'
        s+= self.pstring +'\n'
        s+='* observation groups \n  Gro1  \n'
        s+='* observation data \n'
        n=0;#print self.fact
        for i in range(len(self.onames)):
            a=shape(self.obs[i])
            if len(a)==1 : #just 1 line
                for isp in range(len(self.ospec[i])):
                    n+=1
                    s+=str(self.ospec[i][isp])+str(n)+' '+str(self.obs[i][isp+1])+' '
                    #s+=str(self.fact[isp])+' Gro1 \n'
                    s+='1 Gro1 \n'
            else : 
                nlines,c = a
                for il in range(nlines):
                    n+=1
                    for isp in range(len(self.ospec[i])):
                        s+=self.ospec[i][isp]+str(n)+' '+str(self.obs[i][il,isp+1])+' '
                        #s+=str(self.fact[0,isp+1])+' Gro1 \n'
                        s+='1 Gro1 \n'
        s+='* model command line \n runmod.bat \n'
        s+='* model input/output \n'
        s+='pest_tpl.txt  pest_run.txt \n'
        s+= 'pest.ins pest_out.txt \n'
        s+='* prior information'
        f1=open(self.fdir+os.sep+self.fname+'.pst','w')
        f1.write(s);f1.close()
        print 'Pst file written \n Pest ready to run'
