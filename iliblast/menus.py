import os
from config import *
from importExport import *
import zipfile as zp
import urllib as url
import shutil

class Menus:
    def __init__(self, gui, core):
        self.gui,self.core = gui,core
        self.cfg = Config(core)
        self.dialogs = self.cfg.dialogs
        self.gtyp = self.cfg.gtyp

    def OnNew(self,evt):
        """creates a new file"""
        #self.askSave(evt)
        dlg = self.dialogs.myFileDialog()
        self.core.fileDir,self.core.fileName = dlg.getFile(self.gui,evt,'New Model',"*.iqpht")
        if self.core.fileDir == None: return
        self.core.addin.initAddin()
        self.core.initAll()
        if self.gtyp =='wx':
            self.gui.visu.setVisu(self.core)
            self.gui.updateTitle()

    def OnOpen(self,evt=None):
        """opens a file"""
        if self.core.fileDir!=None:
            self.askSave(evt)
        dlg = self.dialogs.myFileDialog()
        fDir,fName =dlg.getFile(self.gui,evt,'Open','*.iqpht;*.orti');#print fDir,fName
        if fDir == None: return
        self.gui.guiShow.init()
        self.core.openModel(fDir,fName)
        a = self.core.makeTtable()
        tl2 = self.core.getTlist2()
        listSpec = self.core.addin.chem.getListSpecies() # just the names
        self.core.addin.set3D()
        mtype = self.core.dicaddin['Model']['group']
        if self.gtyp =='wx':
            if self.core.diczone['Observation'].dic.has_key('obs.1'):
                onames = self.core.diczone['Observation'].dic['obs.1']['name']
                self.gui.guiShow.setNames('Observation_Zone_L',onames)
            self.gui.visu.setVisu(self.core)
            self.gui.updateTitle()
            self.gui.varBox.chooseCategory(mtype)
        if self.gtyp=='qt':
            self.gui.visu.initDomain()
            self.gui.visu.zonesCore2qgs()
        self.gui.guiShow.setNames('Model_Tstep_L',tl2)
        self.gui.guiShow.setChemSpecies(listSpec)
        self.dialogs.onMessage(self.gui,'file opened')
            
    def OnSave(self,evt=None):
        if self.core.fileDir!=None:
            if self.gtyp=='qt':
                self.gui.visu.zonesQgs2core()
            self.core.saveModel()
            self.dialogs.onMessage(self.gui,'file saved')
        else :
            self.OnSaveAs(evt)
            
    def OnSaveAs(self,evt=None):
        dlg = self.dialogs.myFileDialog()
        fDir,fName = dlg.getFile(self.gui,evt,'Save',"*.iqpht")
        self.core.saveModel(fDir,fName)
        if self.gtyp =='wx':
            self.gui.updateTitle()
        
    def OnImportVersion1(self,evt):
        dlg = self.dialogs.myFileDialog()
        fDir,fName =dlg.getFile(self.gui,evt,'Open',"*.ipht");#print fDir,fName
        importer = impFile(self.gui,self.core)
        importer.impVersion1(fDir,fName)
        
    def OnImportModflowAscii(self,evt):
        dlg = self.dialogs.myFileDialog()
        fDir,fName =dlg.getFile(self.gui,evt,'Open',"*.nam");#print fDir,fName
        importer = impAsciiModflow(self.core,fDir,fName)
        importer.readAll()
        
    def askSave(self,evt=None):
        message = self.dialogs.onQuestion(self.gui,"Do you want to save the project?")
        if message == 'OK':
            self.OnSave(evt)
        else : return
        #message.Destroy()
                
    def OnImportData(self,evt):
        """import external data to be used for representation"""  
        dlg = self.dialogs.myFileDialog()
        fDir,fName =dlg.getFile(self.gui,evt,'Open data file',"*.txt")
        if fDir == None: return
        else : 
            self.core.importData(fDir,fName)
        
    def OnImportSolutions(self,evt):
        """import a text file to store solutions"""
        dlg = self.dialogs.myFileDialog()
        fDir,fName =dlg.getFile(self.gui,evt,'Open solutions',"*.txt")
        if fDir == None: return
        else : 
            self.core.importSolutions(fDir,fName)
            #self.gui.OnMessage("Fichier donnees importe")
            
    def OnImportUserSpecies(self,evt):
        dlg = self.dialogs.myFileDialog()
        fDir,fName =dlg.getFile(self.gui,evt,'Open solutions',"*.txt")
        if fDir == None: return
        else : 
            f1= open(fDir+os.sep+fName+'.txt')
            dicSp = {}
            for l in f1:
                if '=' in l: 
                    a,b=l.split('=');dicSp[a]=b
            self.gui.guiShow.setUserSpecies(dicSp)    
            nameBox = 'Chemistry_User_L'
            self.gui.guiShow.setNames(nameBox,dicSp.keys())
            
    def OnExportParm(self,evt): # OA added 28/3/17
        model,line,media = self.gui.currentModel,self.gui.currentLine,self.gui.currentMedia
        name = line.replace('.','')
        fname = self.core.fileDir+os.sep+ name
        data = self.core.getValueLong(model,line,0)[media]
        savetxt(fname+'.txt',data)  
        self.dialogs.onMessage(self.gui,'file '+name+' saved')

    def OnExportResu(self,evt): # OA modif 28/3/17 for correct name
        name = self.gui.guiShow.curName+self.gui.guiShow.curSpecies;# OA modified 10/5/17
        fname = self.core.fileDir+os.sep+ name
        data = self.gui.guiShow.data[-1]
        savetxt(fname+'.txt',data)  
        self.dialogs.onMessage(self.gui,'file '+name+' saved')
            
    def OnHelp(self,evt): #,lang):
        """calling help file"""
        os.startfile(self.gui.mainDir+os.sep+'doc'+os.sep+"iPht3dDoc_En.chm")
            
    def OnDownloadLast(self,evt):
        self.onDownload('iliblast')
        
    def OnDownloadDev(self,evt):
        self.onDownload('ilibdev')
        
    def onDownload(self,fname):
        if self.cfg.typInstall=='python': 
            maindir=self.gui.mainDir
            dirlib=maindir+os.sep+'ilibq'
        else : 
            maindir=self.gui.mainDir+os.sep+'dist'
            dirlib=maindir+os.sep+'library.zip'
        dirutil=maindir+os.sep+'utils'
        dirdoc=maindir+os.sep+'doc'
        lfu=os.listdir(dirutil)
        if 'newlib.zip' in lfu:
            os.system('copy '+dirutil+os.sep+'newlib.zip '+dirutil+os.sep+'oldlib.zip')
        f2=dirutil+os.sep+'newlib.zip'
        lb=url.urlretrieve('http://oatteia.usr.ensegid.fr/iPht3d/Files/'+fname+'.zip',f2)
        znew=zp.ZipFile(f2,'r')
        if self.cfg.typInstall=='python': #the python version
            znew.extractall(dirlib)
            for n in os.listdir(dirlib):
                if ('.chm' in n) or ('.pdf' in n): 
                    os.system('move '+dirlib+os.sep+n+' '+dirdoc)
                if ('.gif' in n) or ('.dbs' in n): 
                    os.system('move '+dirlib+os.sep+n+' '+dirutil)
        else : # the windows version
            zlib=zp.ZipFile(dirlib,'r'); #print 'menu dwnload 157', dirlib
            zlib.extractall(maindir+os.sep+'temp')
            zlib.close()
            shutil.rmtree('temp'+os.sep+'ilibq')
            znew.extractall(maindir+os.sep+'temp'+os.sep+'ilibq')
            self.zip_folder(maindir+os.sep+'temp',maindir+os.sep+'zout.zip')
            os.chdir(maindir)
            os.system('del '+dirlib)
            os.system('rename zout.zip library.zip')
            shutil.rmtree('temp')
        znew.close()
        self.dialogs.onMessage(self.gui,'lib changed, iPht3D will stop, then restart it')
        self.gui.Destroy()
        
    def zip_folder(self,folder_path, output_path):
        parent_folder = os.path.dirname(folder_path)
        # Retrieve the paths of the folder contents.
        contents = os.walk(folder_path)
        zip_file = zp.ZipFile(output_path, 'w', zp.ZIP_DEFLATED)
        for root, folders, files in contents:
            for folder_name in folders:
                absolute_path = os.path.join(root, folder_name)
                relative_path = absolute_path.replace(parent_folder + '\\', '')
                relative_path = relative_path.replace('temp\\','')
                zip_file.write(absolute_path, relative_path)
            for file_name in files:
                absolute_path = os.path.join(root, file_name)
                relative_path = absolute_path.replace(parent_folder + '\\', '')
                relative_path= relative_path.replace('temp\\','')
                zip_file.write(absolute_path, relative_path)
        
    def OnBackVersion(self,evt):
        dirutil=self.gui.mainDir+os.sep+'utils'
        lf=os.listdir(dirutil)
        if 'oldlib.zip' not in lf: self.dialogs.onMessage('sorry no old lib')
        zin=zp.ZipFile(dirutil+os.sep+'oldlib.zip','r')
        zin.extractall(self.gui.mainDir+os.sep+'ilibq')
        self.dialogs.onMessage(self.gui,'lib changed, iPht3D will stop, then restart')
        self.gui.Destroy()
