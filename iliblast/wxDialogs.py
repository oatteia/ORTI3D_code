import wx,os
import wx.lib.colourselect as csel
import wx.grid as wgrid
from wx.lib import plot
import  wx.lib.scrolledpanel as scrolled
from pylab import savetxt
from scipy import clip
from config import *
            

class onMessage(wx.Dialog):
    '''creates a box with a message, with unique or multiple lines'''
    def __init__(self, gui,text):
        if text==None: return
        if type(text)==type([3,4]): #OA if else modif to get all cases 10/5/17
            h=len(text);w=80
            for i in range(len(text)): w=max(w,len(text[i])*5)
        else:
            w=max(len(text)*5,80);h=1;text=[text]
        wx.Dialog.__init__(self,gui, -1, "",size=(min(w+30,450),min(h*30+80,450)));
        dlgSizer = wx.BoxSizer(wx.VERTICAL)
        for i in range(len(text)):
            dlgSizer.Add(wx.StaticText(self,-1,text[i]))
        dlgSizer.Add(self.CreateButtonSizer( wx.OK ), -1, wx.ALIGN_BOTTOM|wx.ALIGN_CENTER)
        self.SetSizer(dlgSizer)
        self.ShowModal()
        self.Destroy()
        
def onQuestion(gui,text):
    dial = wx.MessageDialog(None, text, 'Question',wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
    retour = dial.ShowModal()
    if retour == wx.ID_YES : return 'OK'
    else : return None

class genericDialog(wx.Dialog):
    """it creates a dialog from data: a list of input containing triplets :
    name, type, value for each button"""
    def __init__(self, gui, title, data, helpstring=''):
        self.gui,self.title,self.data,self.color,self.helpstring = gui,title,data,wx.Color(0,0,0),helpstring
        mysize=(200,300) #max(280,min(400,(len(data)+2)*15-20)))
        wx.Dialog.__init__(self, gui, -1, title,size=mysize)
        dlgSizer = wx.BoxSizer(wx.VERTICAL)
        p = wxGenericPanel(self,gui,data)
        dlgSizer.Add(p,0)
        dlgSizer.AddSpacer((0,5), 0)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonS1 = self.CreateButtonSizer( wx.OK | wx.CANCEL )
        butHelp = wx.Button(self, -1, 'Help')
        self.Bind(wx.EVT_BUTTON, self.onHelp, butHelp)
        buttonSizer.AddMany([(buttonS1,0),(butHelp,0)])
        dlgSizer.Add(buttonSizer, 0, wx.ALIGN_CENTER|wx.ALIGN_BOTTOM)
        self.SetSizerAndFit(dlgSizer)

    def onHelp(self,evt): 
        ddir = self.gui.mainDir+os.sep+'doc'+os.sep
        if self.helpstring != '': helpstr = self.helpstring
        else : helpstr = self.title
        os.system('start hh '+ddir+"iPht3dDoc_En.chm::iPht3dDoc_En.htm#"+helpstr)
        
    def getValues(self): 
        val =[]
        retour = self.ShowModal()
        if retour == wx.ID_OK:
            for i in range(len(self.data)):
                typ = self.data[i][1]
                if typ in ['Text','Check']: 
                    val.append(self.items[i].GetValue())
                elif typ=='Textlong':
                    v0 = self.items[i].GetValue()
                    val.append(v0.split('\n'))
                elif typ=='Choice':
                    val.append(self.items[i].GetStringSelection())
                elif typ=='Color':
                    val.append(self.color)
            return val
        else :
            return None

class wxGenericPanel(scrolled.ScrolledPanel):
    def __init__(self,parent,gui,data):
        self.parent = parent
        mysize=(200,max(140,min(400,(len(data)+2)*20-20)))
        scrolled.ScrolledPanel.__init__(self,parent,-1,size=mysize)
        grdSizer = wx.FlexGridSizer(len(data),2,vgap=3,hgap=5)
        parent.items =[]
        for name,typ,value in data:
            txt = wx.StaticText(self,-1,name)
            if typ == 'Text': 
                parent.items.append(wx.TextCtrl(self,-1,str(value)))
            elif typ == 'Textlong': 
                if type(value)==type([5,6]): 
                    value = '\n'.join([str(v) for v in value]) # cretaes a text with line returns
                parent.items.append(wx.TextCtrl(self,-1,value,style=wx.TE_MULTILINE))
            elif typ=='Check':
                parent.items.append(wx.CheckBox(self,-1))
            elif typ == 'Choice':
                ch = wx.Choice(self,-1,choices=value[1])
                ch.SetStringSelection(value[0])
                parent.items.append(ch)
            elif typ == 'Color':
                butC=csel.ColourSelect(self,-1,label='color',colour=value)
                parent.items.append(butC)
                csel.EVT_COLOURSELECT(butC, butC.GetId(), self.onSelectColour)                
            grdSizer.AddMany([(txt,0),(parent.items[-1],0)])

        self.SetSizer(grdSizer)
        self.SetAutoLayout(1)
        self.SetupScrolling()
        
    def onSelectColour(self, event): self.parent.color=event.GetValue()
        
class largeTextDialog(wx.Dialog):
    """ a dialog to get a list of values"""
    def __init__(self, parent, title, header,txtIn=''):
        size=(400,400);
        self.txtIn=txtIn;self.parent = parent
        wx.Dialog.__init__(self, parent, -1, title,size=size)
        dlgSizer = wx.BoxSizer(wx.VERTICAL)
        hd=wx.StaticText(self,-1,header, style = wx.ALIGN_CENTER)
        dlgSizer.Add(hd,0);dlgSizer.AddSpacer((0,5), 0)
        size2=(300,320);
        self.txt = wx.TextCtrl(self,-1,txtIn,size=size2,style=wx.TE_MULTILINE)
        dlgSizer.Add(self.txt,0);dlgSizer.AddSpacer((0,5), 0)
        buttonSizer = self.CreateButtonSizer( wx.OK | wx.CANCEL ) 
        dlgSizer.Add(buttonSizer, 0, wx.ALIGN_CENTER|wx.ALIGN_BOTTOM)
        self.SetSizer(dlgSizer)
        self.retour = self.ShowModal()
    def GetTextAsList(self):
        lst = self.txt.GetValue().split("\n");
        return lst
    def GetText(self):
        if self.retour == wx.ID_OK : return self.txt.GetValue()
        else : return None
        
class checkDialog(wx.Dialog):
    def __init__(self, parent, title, data):
        """data is a list with tuples (name, value)"""
        wx.Dialog.__init__(self, parent, -1, title)
        dlgSizer = wx.BoxSizer(wx.VERTICAL)
        self.lcheck=[]
        for i in range(len(data)):
            #txt = wx.StaticText(self,-1,data[i][0])
            self.lcheck.append(wx.CheckBox(self,-1,label=data[i][0]))
            self.lcheck[i].SetValue(data[i][1])
            dlgSizer.Add(self.lcheck[i],0)
            #dlgSizer.AddMany([(txt,0),(self.lcheck[i],0)])
        dlgSizer.AddSpacer((0,5), 0)
        buttonSizer = self.CreateButtonSizer( wx.OK | wx.CANCEL ) 
        dlgSizer.Add(buttonSizer, 0, wx.ALIGN_CENTER|wx.ALIGN_BOTTOM)
        self.SetSizerAndFit(dlgSizer)
        
    def getValues(self):
        retour = self.ShowModal()
        if retour == wx.ID_OK:
            lname,lval=[],[]
            for ch in self.lcheck:
                lname.append(str(ch.GetLabelText()))
                lval.append(ch.GetValue())
            return (lname,lval)
        else :
            return None
        
class myFileDialog:
    def __init__(self):
        a=3
    def getFile(self,gui,evt,title,typF):
        dlg = wx.FileDialog(gui,title,"","",typF,wx.OPEN)
        retour = dlg.ShowModal();
        if retour == wx.ID_OK : 
            fDir = dlg.GetDirectory()
            s = dlg.GetFilename()
            fName = s.split('.')[0]
            return fDir,fName
        else : return None,None
    
class textDialog(wx.Dialog):
    def __init__(self, parent, title, mysize,txtIn=''):
        wx.Dialog.__init__(self, parent, -1, title, size = mysize)
        dlgSizer = wx.BoxSizer(wx.VERTICAL)
        size2=(mysize[0]-40,mysize[1]-80);
        self.txt = wx.TextCtrl(self,-1,txtIn,size=size2,style=wx.TE_MULTILINE)
        dlgSizer.Add(self.txt,0)
        dlgSizer.AddSpacer((0,5), 0)
        buttonSizer = self.CreateButtonSizer( wx.OK | wx.CANCEL ) 
        dlgSizer.Add(buttonSizer, 0, wx.ALIGN_CENTER|wx.ALIGN_BOTTOM)
        self.SetSizer(dlgSizer)
        
    def getText(self):
        return self.txt.GetValue()

class zoneDialog(wx.Dialog):
    def __init__(self, parent, core,model,line, curzones, nb):
        self.parent,self.core,self.model,self.line,self.curzones,self.nb = parent,core,model,line,curzones,nb
        self.gui = parent.gui
        dOptions = {}
        for n in core.modelList: dOptions[n]=[]
        dOptions['Modflow']=['mnwt.2a'];dOptions['OpgeoFlow']=['flow.5']     # lines htat contian optional detials
        wx.Dialog.__init__(self, parent, -1, "Zone", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,size=(400,320))
        dlgSizer = wx.BoxSizer(wx.VERTICAL)
        if line in dOptions[model]: self.typO=1
        else : self.typO = 0
        self.zpanel = zonePanel(self, curzones, nb, self.typO)
        dlgSizer.Add(self.zpanel,0)
        buttonSizer = self.CreateButtonSizer( wx.OK | wx.CANCEL ) 
        dlgSizer.Add(buttonSizer, 0, wx.ALIGN_CENTER|wx.ALIGN_BOTTOM)
        self.SetSizer(dlgSizer)
        
    def saveCurrent(self):
        # saving the previously entered zone
        p = self.zpanel
        self.curzones['name'][self.nb]=p.name.GetValue()
        media = p.media.GetValue()
        if '-' in media :
            m1 = media.split('-')
            m2 = range(int(m1[0]),int(m1[1])+1)
        else :
            m2 = int(media)
        self.curzones['media'][self.nb] = m2
        self.curzones['coords'][self.nb]= self.corrCoords(p.coords.GetValue()['data'])
        val0 = ''
        if self.typO: val0 = self.getOpt()
        val = p.valBox.GetValue()
        if type(val)==type({'a':1}): # a dict for cases of temporal values
            v0 = val['data']
            val = ''
            for b in v0 : val+=str(b[0])+' '+str(b[1])+'\n'
        first = val.split('\n')[0]
        if first.count('.')>2:   #for pht3d zones 1.0.0.0
            val = val.replace('.','')
            val = val.replace(' ','')
            val = val.replace('\n','')
        self.curzones['value'][self.nb]= val0+val

    def corrCoords(self,lcooI):
        '''change coordinates if they are out of the domain'''
        g = self.core.dicaddin['Grid']
        ex = (float(g['x1'])-float(g['x0']))/1e5
        ey = (float(g['y1'])-float(g['y0']))/1e5
        lcoord = []
        for b in lcooI:
            try : x = clip(float(b[0]),float(g['x0'])+ex,float(g['x1'])-ex)
            except ValueError : continue
            try: y = clip(float(b[1]),float(g['y0'])+ey,float(g['y1'])-ey)
            except ValueError : continue
            if len(b)==2: lcoord.append((x,y))
            else : lcoord.append((x,y,float(b[2])))
        return lcoord
        
    def getOpt(self):
        data = self.zpanel.GOdata.GetValue()['data']; #print 'wxdialog 248',data
        s = '$'
        for i in range(len(data)):
            s += data[i][0]+' \n'
        return s+'$'
     
class zonePanel(wx.Panel):
    def __init__(self,parent,curzones, nb, typO):
        self.parent = parent
        wx.Panel.__init__(self, parent, -1)
        # zone name
        txtName=wx.StaticText(self,-1,'  Zone name  ')
        self.name = wx.TextCtrl(self,-1,curzones['name'][nb])
        s = '       '
        lineName=wx.StaticText(self,-1,s+parent.core.dickword[parent.model].lines[parent.line]['comm'])
        # zone media
        txtMedia=wx.StaticText(self,-1,'  Zone media  ')
        zm = '0'
        if curzones['media'][nb]!='': 
            zm = curzones['media'][nb]
            if type(zm)==type([5]): zm=str(zm[0])+'-'+str(zm[-1])
        self.media = wx.TextCtrl(self,-1,str(zm))
        if parent.core.addin.getDim() !='3D': self.media.Enable(False)
        # zone transient or not
        txtTransient=wx.StaticText(self,-1,'  Temporal  ')
        self.transient = wx.Choice(self, -1,choices=['Steady','Transient'])
        self.Bind(wx.EVT_CHOICE,self.onTransient,self.transient)
        # zone units
        units = wx.StaticText(self,-1,s+parent.core.getUnits(parent.model,parent.line,0))
        #zone coords
        txtCoords=wx.StaticText(self,-1,'  Zone coords ')
        #size2=(150,mysize[1]-140);
        coo = curzones['coords'][nb]
        data = [list(x) for x in coo]
        nrow = len(data)
        cols = ['X','Y']
        if len(data[0])==3: cols = ['   X   ','  Y   ','Z']
        dicCoo = {'cols':cols,'rows':['']*nrow,'data':data}
        self.coords = myNBpanelGrid(parent.gui,self,dicCoo,size=(120,140))
        # zone value
        val = str(curzones['value'][nb]);
        if '$' in val : val = val.split('$')[-1]
        self.value = val
        typS = 0 # classical
        if len(val.split('\n'))>1: typS = 1 # transient
        if parent.line in ['ph.3','inic.1']: # for chemical solutions
            a = str(val).rjust(5,'0')
            val =  str(int(a[:2]))+'.'+a[-3]+'.'+a[-2]+'.'+a[-1]
            units = wx.StaticText(self,-1,s+'solution . mineral . exchange . surface')
        #gathering
        namSizer = wx.FlexGridSizer(2,2,vgap=2,hgap=3)
        namSizer.AddMany([(txtName,0),(self.name,0),
                (txtMedia,0),(self.media,0),
                (txtTransient,0),(self.transient,0)]) #,(txtType,0),(self.type,0)])
        optSizer = wx.BoxSizer(wx.VERTICAL)
        optSizer.AddMany([(lineName,0),(units,0)])
        if typO:
            self.GOtitles,self.GOdata = self.gridOpt(parent.line,str(curzones['value'][nb]))
            optSizer.Add(self.GOdata)
        cooSizer = wx.FlexGridSizer(1,2,vgap=0,hgap=3)
        cooSizer.AddMany([(txtCoords,0),(self.coords,0)])
        self.valSizer = wx.FlexGridSizer(1,2,vgap=5,hgap=3)
        self.transient.SetSelection(typS)
        self.valBox = self.changeValueBox(typS)
        dlgSizer =  wx.FlexGridSizer(2,2,vgap=0,hgap=3)
        dlgSizer.AddMany([(namSizer,0),(optSizer,0),(cooSizer,0),(self.valSizer,0)])
        dlgSizer.AddSpacer((0,5), 0)
        self.SetSizer(dlgSizer)
        
    def onTransient(self,evt):
        item = self.FindWindowById(evt.GetId());
        self.valBox = self.changeValueBox(item.GetSelection())
        
    def changeValueBox(self,typS):
        '''changes the value sizer btw one value (permanent) and a list (transient)'''
        self.valSizer.DeleteWindows();self.valSizer.Clear()
        txtValue=wx.StaticText(self,-1,'  Zone value  ')
        if typS == 0: # text
            valDlg = wx.TextCtrl(self,-1,self.value,style=wx.TE_MULTILINE) #size=size3)
        elif typS == 1: # grid
            if self.value[0]=='$': a,b,val1 = self.value.split('$')
            else : 
				val1 = self.value.split('\n');#print val1
				while '' in val1: val1.remove('')
				#print val1
            if len(val1)>1: data = [v.split() for v in val1]
            else : data = [[i,0] for i in range(3)]# no values
            dicV = {'cols':['t','val'],'rows':'','data':data}
            valDlg = myNBpanelGrid(self.parent.gui,self,dicV,size=(120,180))

        valDlg.Bind(wgrid.EVT_GRID_SELECT_CELL,self.current)
        self.valSizer.AddMany([(txtValue,0),(valDlg,0)])
        self.Layout();self.parent.Layout()
        return valDlg
        
    def gridOpt(self,line,val):
        dTitles = {'mnwt.2a':['Nnodes','Losstype','','','','','',''],
                   'flow.5':['K. Hydraul','Storage','Porosity']}
        titles = dTitles[line]
        if line == 'mnwt.2a': return titles,self.gridMNW(titles, val)
        elif line == 'flow.5': return titles,self.gridSimple(titles, val)

    def gridSimple(self,titles,val):
        '''creates specific dialog part for serveal values in a zone'''
        if '$' in val:
            a,P1,P2 = val.split('$')
            Parm1 = [[x] for x in P1.split('\n')];#print 'Nwell',Parm1
        else : 
            Parm1 = [['0'] for x in titles]
        dicV = {'cols':[' '*20],'rows':titles,'data':Parm1}
        self.gopt = myNBpanelGrid(self.parent.gui,self,dicV,size=(180,20*len(titles)))
        return self.gopt

    def gridMNW(self,titles,val):
        '''creates specific dialog parts for multi node wells
        now no implementation of Qlimit, pumploc, ppflag, pumpcap'''
        #print val
        #Parm1 = [[0]*len(t.split(',')) for t in titles]
        if '$' in val:
            a,P1,P2 = val.split('$')
            Parm1 = [[x] for x in P1.split('\n')];#print 'Nwell',Parm1
        else : 
            Parm1 = [['0'] for x in titles]
        lossV = Parm1[1][0] # store the value of lossV
        Parm1[1][0]=['NONE','THIEM','SKIN','GENERAL','SPECIFYcwc']
        dicV = {'cols':[' '*20],'rows':titles,'data':Parm1}
        self.gopt = myNBpanelGrid(self.parent.gui,self,dicV,size=(180,180))
        self.gopt.setChoice(1,0,lossV)
        if '$' in val:
            self.changeCellR(0)
            self.changeCellR(1) # to see the effect of the current selection
        self.Bind(wgrid.EVT_GRID_CELL_CHANGE,self.changeCell)
        return titles,self.gopt
        
    def changeCell(self,evt):
        ir = evt.GetRow();#self.curRow = ir
        self.changeCellR(ir)
        
    def changeCellR(self,ir):
        """different data input for type of MN well"""
        if self.gopt.GetRowLabelValue(ir)=='Losstype': # Loss Type
            for i in range(2,6): self.gopt.SetRowLabelValue(i,' ')
            Ltype = self.gopt.GetCellValue(ir,0).strip()
            dlist = {'NONE':[],'THIEM':['Rw'],'SKIN':['Rw','Rskin','Kskin'],\
                'GENERAL':['Rw','B','C','P'],'SPECIFYcwc':['CWC']}
            #print tlist.keys()
            r = dlist[str(Ltype)]
            for i in range(len(r)):
                self.gopt.SetRowLabelValue(2+i,r[i])
        elif self.gopt.GetRowLabelValue(ir)=='Nnodes': # nnodes
            for i in range(6,8): self.gopt.SetRowLabelValue(i,' ')
            Nnodes = int(self.gopt.GetCellValue(ir,0))
            if Nnodes >0 : self.gopt.SetRowLabelValue(6,'LAY')
            elif Nnodes <0 : 
                self.gopt.SetRowLabelValue(6,'Ztop')
                self.gopt.SetRowLabelValue(7,'Zbot')
        self.gopt.Refresh()
        
    def current(self,evt):
        #print  evt.GetRow()
        if evt.GetRow()==self.valBox.GetNumberRows()-1:
            self.valBox.AppendRows();self.valBox.rowString.append('')
        evt.Skip()

##################### a note book to have cheks
class myNoteBookCheck(wx.Dialog):
    def __init__(self,gui,title,dic):
        # dic is a dictionnary of lists
        self.gui=gui
        wx.Dialog.__init__(self,gui,-1,title,size=(550,500))
        self.pages,self.dicIn ={},dic
        sizer= wx.GridSizer(2,1)
        self.SetSizer(sizer)
        siz1 = wx.BoxSizer(wx.VERTICAL)
        nb = wx.Notebook(self,-1,size=(450,400))
        for n in dic.keys():
            if len(dic[n])==0: continue
            pg = myPanelCheck(nb,dic[n])
            self.pages[n] = pg
            nb.AddPage(pg,n)
        siz1.Add(nb);sizer.Add(siz1)
        buttonSizer = self.CreateButtonSizer( wx.OK | wx.CANCEL) 
        sizer.Add(buttonSizer,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM)
        self.retour = self.ShowModal()
        
    def onCancel(self): pass #return None  
    def onOK(self): pass # return 'OK'
    
    def getValues(self):
        dic = {}
        if self.retour == wx.ID_OK:
            for k in self.pages.keys():
                dic[k] = self.pages[k].getValues()
            return dic
        else : return None
        
class myPanelCheck(scrolled.ScrolledPanel):
    def __init__(self,parent,listChk):
        """listChk is a list of tuples with first value as name and 2nd bool"""
        #size=(235,min(440,(len(listIn)+2)*22-20))
        scrolled.ScrolledPanel.__init__(self,parent,-1,size=(340,300))
        list2=zip(*listChk)[0]
        nChk=len(listChk)
        self.listCtrl = []
        contentSizer = wx.FlexGridSizer(nChk/4,8,vgap=4,hgap=5)
        for n in sort(list2):
            i=list2.index(n)
            chk = wx.CheckBox(self, -1, '',name=n)
            self.listCtrl.append(chk)
            chk.SetValue(listChk[i][1])
            contentSizer.Add(chk, 0)
            text = wx.StaticText(self, -1,listChk[i][0])
            contentSizer.Add(text, 0)
        self.SetSizer(contentSizer)
        self.SetAutoLayout(1)
        self.SetupScrolling()
        
    def getValues(self):
        l0=self.listCtrl;nChk = len(l0);l1=[]
        for i in range(nChk):
            b=l0[i].GetValue();name=l0[i].GetName()
            l1.append((name,b))
        return l1
        
################ this note book takes chem dictionnary ###################"""        
class myNoteBook(wx.Dialog):    
    def __init__(self,gui,title,dic):
        self.gui=gui
        wx.Dialog.__init__(self,gui,-1,title,size=(550,500))
        self.pages,self.dicIn ={},dic.copy()
        sizer= wx.GridSizer(2,1)
        self.SetSizer(sizer)
        siz1=wx.BoxSizer(wx.VERTICAL)
        nb=wx.Notebook(self,-1,size=(450,400))
        for n in dic.keys():
            if dic[n]==None:continue
            if len(dic[n]['rows'])==0 and n!='Species': continue
            if len(dic[n]['cols'])>0: pg = myNBpanelGrid(gui,nb,dic[n])
            else : pg = myNBlist(gui,nb,dic[n])
            self.pages[n]=pg;nb.AddPage(pg,n)
        siz1.Add(nb);sizer.Add(siz1)
        buttonSizer = self.CreateButtonSizer( wx.OK | wx.CANCEL) 
        sizer.Add(buttonSizer,0,wx.ALIGN_LEFT|wx.ALIGN_BOTTOM);
        self.ShowModal()
        
    def onCancel(self): pass #return None  
    def onOK(self): pass # return 'OK'
    
    def getValues(self):
        dic=self.dicIn.copy();#print dic
        for n in self.pages.keys():
            dic[n]=self.pages[n].GetValue()
            if self.dicIn[n].has_key('text'): dic[n]['text']=self.dicIn[n]['text']
        return dic
    
class myNBlist(wx.Panel):
    def __init__(self,gui,parent,dic):
        wx.Panel.__init__(self,parent,-1, size=(400,300))
        self.dic=dic
        listIn=dic['rows']
        dlgSizer = wx.BoxSizer(wx.VERTICAL)
        list2=""
        for n in listIn: list2 = list2+str(n)+"\n"
        #if list2=="":list2="\n \n \n"
        self.txt = wx.TextCtrl(self,-1,list2,style=wx.TE_MULTILINE)
        dlgSizer.Add(self.txt,0)
        self.SetSizer(dlgSizer)
        
    def getValues(self) :
        txt=self.txt.GetValue().strip().split('\n')
        self.dic['rows']=[n.strip() for n in txt]
        self.dic['data']=[]
        for i in range(len(txt)):
            self.dic['data'].append(['True',0.])
        return self.dic
        
class myNBpanelGrid(wgrid.Grid):
    def __init__(self,gui,parent,dic,**kwargs):
        wgrid.Grid.__init__(self,parent,-1,**kwargs)
        self.rowString,self.colString,data=dic['rows'],dic['cols'],dic['data']
        if dic['rows']=='': self.rowString=['']*len(dic['data'])
        nrow, ncol = len(self.rowString),len(self.colString)
        self.chk = zeros((nrow,ncol))
        ln=[len(x) for x in self.rowString]
        self.SetRowLabelSize(min(max(ln)*8,170))
        lent = sum([len(x.replace(' ','')) for x in self.colString])
        if lent==0 : self.SetColLabelSize(0) # if all '', remove col headers
        self.CreateGrid(nrow,ncol);#print data
        for j,col in enumerate(self.colString):
            self.SetColLabelValue(j,col);
        for i,row in enumerate(self.rowString):
            self.SetRowLabelValue(i,row)
            ln = len(data[i])
            for j,col in enumerate(self.colString[:ln]):
                d = data[i][j]
                if type(d)==type([5,6]):
                    choice_editor = wgrid.GridCellChoiceEditor(d,False)
                    #choice_editor.SetCellAttr()
                    self.SetCellEditor(i,j, choice_editor)  
                    #self.SetCellValue(i, j, 1)
                elif type(d)==type(True):
                    e_boo = wgrid.GridCellBoolEditor()                       
                    self.SetCellEditor(i,j, e_boo)    
                    r_boo = wgrid.GridCellBoolRenderer()                       
                    self.SetCellRenderer(i,j, r_boo) 
                    self.chk[i,j] = 1
                    self.SetCellValue(i, j, str(d*1))
                else : 
                    # limit size cell if float
                    try : 
                        float(d)
                        #if 'e' not in d: d1 = d[:6]
                        d1 = str(d)[:9] #a real
                    except ValueError: 
                        d1 = str(d)
                    self.SetCellValue(i, j, d1)
                #self.SetCellSize(i,j,8,len(col)*4)

        self.AutoSizeColumns(True)
        self.AutoSizeRows(True)
        wx.EVT_KEY_DOWN(self, self.OnKey)
        
    def setChoice(self,i,j,txt):
        self.SetCellValue(i,j,txt)
        
    def GetValue(self) :
        dicV = {'rows':self.rowString,'cols':self.colString}
        data = []
        for i in range(len(self.rowString)):
            d = []
            for j in range(len(self.colString)):
                val = self.GetCellValue(i,j);#print self.rowString[i],j,val
                if len(self.chk)>i:
                    if self.chk[i,j] == 1:
                        val = (val=='1')
                d.append(val)
            data.append(d)
        dicV['data'] = data
        #print dicV
        return dicV
        
    #below : code to have direct check of checkboxes
    def onMouseLeft(self,evt):
        if self.chkTrue[evt.Col]:
            cb = self.GetCellValue(evt.Row,evt.Col)
            sleep(0.1);
            self.SetCellValue(evt.Row,evt.Col,bool(1-cb))
        #evt.Skip()
#  
    def OnKey(self, event):
        #print event.ControlDown(),event.GetKeyCode()
        if event.ControlDown() and event.GetKeyCode() == 67: # If Ctrl+C is pressed...
            self.copy()
        elif event.ControlDown() and event.GetKeyCode() == 86: # If Ctrl+V is pressed...
            self.paste()
        else : event.Skip()
        return

    def copy(self):
        # Number of rows and cols
        rtop, ctop = self.GetSelectionBlockTopLeft()[0]
        rbot, cbot = self.GetSelectionBlockBottomRight()[0]
        rows = rbot - rtop + 1
        cols = cbot - ctop + 1
        #print 'copy'
        # data variable contain text that must be set in the clipboard
        data = ''
        # For each cell in selected range append the cell value in the data variable
        # Tabs '\t' for cols and '\r' for rows
        for r in range(rows):
            for c in range(cols):
                data += str(self.GetCellValue(rtop + r,ctop + c))
                if c < cols - 1: data = data + '\t'
            data = data + '\n'
        #print data
        # Create text data object
        clipboard = wx.TextDataObject()
        # Set data object value
        clipboard.SetText(data)
        # Put the data in the clipboard
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(clipboard)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Can't open the clipboard", "Error")
			
    def paste(self):
        clipboard = wx.TextDataObject()
        if wx.TheClipboard.Open():
            wx.TheClipboard.GetData(clipboard)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Can't open the clipboard", "Error")
        data = clipboard.GetText()
        table, y = [],-1
        # Convert text in a array of lines
        for r in data.splitlines():
            y = y +1
            y_pos = self.GetGridCursorRow() + y
            if y_pos==self.GetNumberRows()-1: 
                self.rowString.append('')
                self.AppendRows()
            x = -1
            for c in r.split('\t'):
                x = x +1
                self.SetCellValue(y_pos,self.GetGridCursorCol() + x, c)

#//////////////////////////////////////////////////////////////////////
class dialogContour(wx.Dialog):
    ID_COLOR1 = 307
    ID_COLOR2 = 308
    ID_COLOR3 = 309

    def __init__(self, parent, title, valeur, col):
        """ liste contient les attributs actuels des contours : val : [0]min, 1:max,
        2: intervalles, [3]decimales, 4:log, 5:user puis couleurs et transparence"""
        self.listCtrl,self.valeur,self.parent = [], valeur,parent;
        size=(150,10*35+50)
        wx.Dialog.__init__(self, parent, -1, title,size=size)
        sizeTextCtrl = (40,20)        
        dlgSizer = wx.BoxSizer(wx.VERTICAL)        
        Sizer1 = wx.GridSizer(5,2,vgap=10,hgap=10)
        # boite pour calcul automatique
        Sizer1.Add(wx.StaticText(self, -1, 'Automatic'), 0, wx.ALIGN_CENTER)
        self.auto = wx.CheckBox(self, -1, '');self.auto.SetValue(True)
        if valeur!=None:
            self.auto.SetValue(valeur[4]=='auto')
            self.listuser=valeur[5]
        Sizer1.Add(self.auto, 0, wx.ALIGN_CENTER)
        # intervalles
        label = ['Mini', 'Maxi', 'Interval','Decimals']
        if col==None : col=[(0,0,255),(0,255,0),(255,0,0),10]
        self.coul = [wx.Color(col[0][0],col[0][1],col[0][2]),
                     wx.Color(col[1][0],col[1][1],col[1][2]),
                     wx.Color(col[2][0],col[2][1],col[2][2]),col[3]]
        if valeur==None: valeur=[0.,10.,1.,2,False,False]
        for i in range(4):
            text = wx.StaticText(self, -1, label[i], style = wx.ALIGN_LEFT)
            self.listCtrl.append(wx.TextCtrl(self, -1, str(valeur[i]), style = wx.TE_RIGHT, size = sizeTextCtrl))
            Sizer1.Add(text, 0, wx.ALIGN_CENTER)
            Sizer1.Add(self.listCtrl[i], 0, wx.ALIGN_CENTER)
            
        Sizer1.Add(wx.StaticText(self, -1, 'log'), 0, wx.ALIGN_CENTER)
        self.log = wx.CheckBox(self, -1, '')
        self.log.SetValue(valeur[4]=='log')
        Sizer1.Add(self.log, 0, wx.ALIGN_CENTER)
        self.butlist = wx.Button(self,-1,'List of values')
        Sizer1.Add(self.butlist,0)
        self.user = wx.CheckBox(self, -1, '')
        self.user.SetValue(valeur[4]=='fix')
        Sizer1.Add(self.user, 0, wx.ALIGN_CENTER)
        # dialogue couleurs
        Sizer3 = wx.GridSizer(3,2,vgap=10,hgap=10)
        but0=csel.ColourSelect(self,-1,label='color',colour=col[0],size=sizeTextCtrl)
        but1=csel.ColourSelect(self,-1,label='color',colour=col[1],size=sizeTextCtrl)
        but2=csel.ColourSelect(self,-1,label='color',colour=col[2],size=sizeTextCtrl)
        Sizer3.Add(wx.StaticText(self, -1,'Color 1'),0,wx.ALIGN_CENTER)
        Sizer3.Add(but0,0)
        Sizer3.Add(wx.StaticText(self, -1,'Color 2'),0,wx.ALIGN_CENTER)
        Sizer3.Add(but1,0)
        Sizer3.Add(wx.StaticText(self, -1,'Color 3'),0,wx.ALIGN_CENTER)
        Sizer3.Add(but2,0)
        Sizer3.Add(wx.StaticText(self, -1,'Opacity '),0,wx.ALIGN_CENTER)
        self.transp=wx.TextCtrl(self, -1, str(col[3]), size = sizeTextCtrl)
        Sizer3.Add(self.transp,0)
        
        wx.EVT_BUTTON(self.butlist,self.butlist.GetId(),self.OnListUser)
        csel.EVT_COLOURSELECT(but0, but0.GetId(), self.OnSelectColour0)
        csel.EVT_COLOURSELECT(but1, but1.GetId(), self.OnSelectColour1)
        csel.EVT_COLOURSELECT(but2, but2.GetId(), self.OnSelectColour2)

        dlgSizer.Add(Sizer1, 0, wx.ALIGN_CENTER|wx.EXPAND)
        dlgSizer.Add(wx.StaticLine(self, -1), 0, wx.ALIGN_CENTER|wx.EXPAND)
        dlgSizer.Add(Sizer3, 0, wx.ALIGN_CENTER|wx.EXPAND)
        dlgSizer.AddSpacer((0,0), -1)
        buttonSizer = self.CreateButtonSizer( wx.OK | wx.CANCEL ) 
        dlgSizer.Add(buttonSizer, 0, wx.ALIGN_CENTER|wx.ALIGN_BOTTOM)
        self.SetSizer(dlgSizer);self.valeur=valeur

    def GetStrings(self):
        """renvoie les valeurs des boites et ajoute la liste user a la fin """
        v=self.valeur
        if v==None: v=[0.,10.,1.,2,'auto',None]
        for i in range(4):
            v[i]=self.listCtrl[i].GetValue()
            try: float(v[i])
            except ValueError:
                self.parent.OnMessage('erreur de type');return self.valeur
        v[4]='lin'
        if self.user.GetValue():
            v[4]='fix';v[5]=self.listuser
        if self.log.GetValue(): v[4]='log'
        if self.auto.GetValue(): v[4]='auto'
        self.coul[3]=self.transp.GetValue();
        return v
    
    def OnListUser(self,event):
        """ ouvre un dialogue pour rentrer plusieurs valeurs et les renvoie"""
        if self.user.GetValue()==False: return
        data  =[('values','Textlong',[''])]
        if self.valeur!=None:
            if type(self.valeur[5])==type([1]): 
                data =[('values','Textlong',self.valeur[5])]
        #dialg = MyListDialog(self.parent,"",lst1)
        dialg = genericDialog(self.parent,'List of values',data)
        ls = dialg.getValues()[0];#print 'lstuser',self.listuser
        self.listuser = [float(x) for x in ls]
        return
        
    def OnSelectColour0(self, event): self.coul[0]=event.GetValue()
    def OnSelectColour1(self, event): self.coul[1]=event.GetValue()
    def OnSelectColour2(self, event): self.coul[2]=event.GetValue()

#----------------------------------------------------
class plotxy(wx.Frame):
    ID_AXES = 306
    ID_EXPORT = 308
    
    def __init__(self,parent,id,title="plot",pos=wx.DefaultPosition):
        self.gui = parent
        self.toglX= 0; self.toglY = 0
        wx.Frame.__init__(self,parent, id, title,pos=wx.DefaultPosition,size=(350,450))
        self.SetBackgroundColour('#EDFAFF');self.CenterOnScreen()
        hautSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.butAxes = wx.Button(self, self.ID_AXES, label = "Axes")
        self.butExport = wx.Button(self,self.ID_EXPORT, label = "Export")
        self.cnv = plot.PlotCanvas(self);
        self.cnv.SetInitialSize(size=(300, 400))
        hautSizer.AddMany([(self.butAxes,0),(self.butExport,0)])
        plotSizer = wx.BoxSizer(wx.VERTICAL)
        plotSizer.AddMany([(hautSizer,0),(self.cnv,0,wx.EXPAND)])
        #plotSizer.SetSizeHints(self)
        self.SetSizer(plotSizer)
        
        wx.EVT_BUTTON(self, self.ID_AXES, self.OnAxes)    
        wx.EVT_MENU(self, wx.ID_EXIT, self.OnExit)
        wx.EVT_BUTTON(self, self.ID_EXPORT, self.OnExport)
        
    def draw(self,x,arry,legd,title,Xtitle,Ytitle,typ='-',axes=None):
        x,arry=transpose(array(x,ndmin=2)),array(arry) # x en vertical
        self.x, self.arry, self.legd, self.title = x, arry, legd, title
        self.Xtitle,self.Ytitle,self.typ = Xtitle, Ytitle,typ
        self.xlog, self.ylog = False, False
        self.lignes = [];cols=['red','blue','green','orange','cyan','black']*5
        # verifier dimensions des vecteurs entree
        if len(shape(x))==1:
            x1 = ones((len(x),1))+0.;
        if len(shape(arry))==1:
            arry1 = ones((len(arry),1))+0.; arry1[:,0]=arry; arry=arry1*1.;ny=1
        else :
            [nt,ny] = shape(arry)
        if axes!=None: a,b,self.xlog,c,d,self.ylog = axes
        x2 = x*1.; arry2 = arry*1.;
        if self.xlog:
            x2[x2<=0.]=1e-7;x2 = log10(x)
        if self.ylog:
            arry2[arry2<=0.]=1e-7;arry2 = log10(arry)
        # creer les lignes
        if ny==1:
            dataL = concatenate([x2,arry2],axis=1)
            if typ=='-': gobj = plot.PolyLine(dataL,colour='red')
            else : gobj = plot.PolyMarker(dataL,colour='red')
            self.lignes.append(gobj)
        else :
            #print 'mydlg',ny,cols,legd
            for i in range(ny):
                dataL = concatenate([x2,arry2[:,i:i+1]],axis=1)
                if typ=='-': gobj = plot.PolyLine(dataL,colour=cols[i],legend=legd[i])
                else : gobj = plot.PolyMarker(dataL,colour=cols[i],legend=legd[i])
                self.lignes.append(gobj)
        drawObj = plot.PlotGraphics(self.lignes,title,Xtitle,Ytitle)
        # limite des axes
        if axes==None or self.xlog:
            xmn = amin(amin(x2)); xmx = amax(amax(x2));
            dmx = xmx-xmn; self.xmx=xmx+dmx/20.; self.xmn=xmn-dmx/20.
        else :
            self.xmn,self.xmx,a,b,c,d = axes
        if axes==None: # or self.ylog:
            ymn = amin(amin(arry2));ymx = amax(amax(arry2));#print 'dlg',ymn,ymx
            dmy = ymx-ymn; self.ymx=ymx+dmy/20.; self.ymn=ymn-dmy/20. 
        else :
            a,b,c,self.ymn,self.ymx,d = axes
        if self.ymn==self.ymx:
            #print arry
            self.ymn=self.ymn*.99;self.ymx=self.ymx*1.01
        #self.ymn = max(self.ymn,0.);self.xmn = max(self.xmn,0.)
        self.cnv.SetEnableLegend(True);self.cnv.SetEnableGrid(True)
        self.cnv.Draw(drawObj,xAxis=(float(self.xmn),float(self.xmx)),
            yAxis=(float(self.ymn),float(self.ymx)))
        
    def OnAxes(self,evt):
        lst = [('X_min',self.xmn),('X_max',self.xmx),('X_log',self.xlog),
               ('Y_min',self.ymn),('Y_max',self.ymx),('Y_log',self.ylog)]
        dlg = MyGenericCtrl(self.gui,'Axes',lst)
        if dlg.ShowModal() == wx.ID_OK:
            axes = zip(*dlg.GetValues())[1];
        else : return
        self.draw(self.x,self.arry,self.legd,self.title,self.Xtitle,
                self.Ytitle,typ=self.typ,axes=axes)

    def OnExport(self,evt):
        arr = self.lignes[0].points[:,:1]
        for i in range(len(self.lignes)):
            arr=c_[arr,self.lignes[i].points[:,1:2]]
        c=self.gui.core
        fname = c.fileDir+os.sep+c.fileName+self.title+'.txt'
        dlg = wx.FileDialog(self.gui,"Save","",fname,"*.txt",wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:            
            fname = dlg.GetDirectory()+os.sep+dlg.GetFilename()
            f1 = open(fname,'w')
            f1.write(self.Xtitle)
            for n in self.legd: f1.write(' '+n)
            f1.write('\n')
            savetxt(f1,arr)
            f1.close()
            
    def OnExit(self,evt):
        pass
        #print 'bye' #marche pas

