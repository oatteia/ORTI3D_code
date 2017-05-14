import os
from geometry import *

"""this class allows to create the dialog to enter parameter values
it uses the keyword dictionnaries to create the structure
and also to test conditions for entering some specific values"""

class valueDialog:
    def __init__(self,gui,title,core,modName):
        self.butNb,self.fDir,self.fName=500,None,None
        self.gui,self.core,self.modName = gui,core,modName
        self.Mkword = core.dickword[modName] # contains groups and lines
        self.val = core.dicval[modName];# initiate values to 0
        self.zone = core.diczone[modName]
        self.array = core.dicarray[modName]
        self.formula = core.dicformula[modName]
        self.initStoredValues();# to get the conditions from the dictionnary

        if self.gui.gtyp == 'qt':
            self.gtyp='qt'
            from qtValueDialog import *
            self.dialg = qtValueDialog(self,gui,core,modName)
        if self.gui.gtyp == 'wx':
            self.gtyp = 'wx'
            from wxValueDialog import *
            self.dialg = wxValueDialog(self,gui,core,modName)
        # some lines will not be shown (they are in the addin)
        self.blind=['DELR','DELC','TOP','BOTM','PERLEN','NROW','NCOL','NLAY','NPER',
                    'NCOMP','MCOMP','GCOMPN','KCOMPN','SP1','SP2','RC1','RC2',
                    'SWC','SDH']
        #print self.gtyp

    def show(self):
        if self.gtyp == 'wx':
            self.dialg.ShowModal()
        if self.gtyp == 'qt':
            self.dialg.exec_()
            
    def setDictionnaries(self,dicval,diczone,dicarray,dicformula):
        self.val = dicval
        self.zone = diczone
        self.array = dicarray
        self.formula = dicformula
        self.initStoredValues()
        
    def initStoredValues(self):
        """at the model loadings look into the self.val dictionnary
        and gets all value that need to be stored as keywords
        """
        for ll in self.Mkword.lines.keys():
            #print 'valdlg l47',ll
            lk=self.Mkword.lines[ll];
            for i,kwd in enumerate(lk['kw']):
                if ll not in self.val.keys(): continue
                if i<len(self.val[ll]): val=self.val[ll][i]
                else : val=0
                if type(val) in [type('r'),type(u'r')]: continue
                if lk['type'][0][:3]=='arr': continue # do not store array
                kwd=kwd.split('(')[0]
                exec('self.'+kwd+'='+str(val))
    
    def changeStoredValues(self):
        """change the value of the keywords stored in the model"""
        l=self.currentLine
        lname=self.Mkword.lines[l]['kw'];
        for i,kwd in enumerate(lname):
            a=kwd.split('(')
            if len(a)>=1: kwd=a[0]
            val=self.val[l][i]
            if type(val) not in [type('r'),type(u'r')]:
                exec('self.'+kwd+'='+str(val));#print 'valdlg 67',l,i,kwd,val,self.LAYWET

    def testConditions(self,lstL):
        """ test if the lines indices given in lstL satisfy the condition"""
        lstout=[];
        for l in lstL:
            cond = self.Mkword.lines[l]['cond']; #print 'valudiag 75',l,cond
            if self.core.testCondition(self.modName,cond):
                lstout.append(l); #print 'valudiag 75',l,cond, 'True'
        #print 'valdilg 80',lstout
        return lstout
                       
    def onChoiceGroup(self,name):
        '''action when a group is chosen, changes the line list'''
        groups,lines = self.Mkword.groups,self.Mkword.lines
        if name in groups: # make visible buttons for lines
            self.currentGroup = name
            lname=[]
            lst1=self.testConditions(groups[name]) #select lines that satisfy the conditions
            for l in lst1:
                lname.append(l+'- '+lines[l]['comm'])
            self.showBox(self.dialg.boxkeys,False)
            self.changeCombo(self.dialg.chlines,lname)
            
    def onChoiceLine(self,name):
        """ action when a line choice is clicked : change the interface"""
        lines=self.Mkword.lines
        name = name.split('-')[0]
        if name in lines.keys():
            n=str(name);
            self.currentLine = n
            if lines[n].has_key('detail'): details = lines[n]['detail']
            else : details = [None]*len(self.val[n])
            if len(details)==0: details = [None]*len(self.val[n])
            self.changeButtons(name,lines[n]['kw'],self.val[n],details,lines[n]['type'])

    def OnSetNewVal(self,evt=''):
        """sets the new values when user click on OK in key box"""
        values=self.dialg.boxkeys.getValues();#print 'vdialg, setnew',values
        for i in range(len(values)):
            self.val[self.currentLine][i]=values[i]
        names = []
        self.changeStoredValues();
        #readapt lines if condition modify them
        lst0=self.Mkword.groups[self.currentGroup]
        lst1=self.testConditions(lst0) #select lines that satisfy the conditions
        for l in lst1:
            names.append(l+'- '+self.Mkword.lines[l]['comm'])
        self.changeCombo(self.dialg.chlines,names)
        if self.gtyp == 'wx':
            self.dialg.boxkeys.grdSizer.DeleteWindows()
            self.dialg.boxkeys.grdSizer.Clear()
            self.dialg.boxkeys.Layout()
            self.dialg.boxkeys.butApply.Enable(False)

    def showBox(self,box,bool):
        if self.gtyp=='wx':
            box.Show(bool)
        if self.gtyp=='qt':
            box.setVisible(bool)    
            
    def changeCombo(self,comboName,names):
        if self.gtyp=='wx':
            comboName.Clear()
            for n in names: comboName.Append(n)
        if self.gtyp=='qt':
            comboName.clear()
            for n in names:
                comboName.addItem(n)

    def changeButtons(self,title,names,values,details,types):
        self.showBox(self.dialg.boxkeys,True)
        self.dialg.boxkeys.addButtons(names,values,details,types)
        if self.gtyp=='wx':
            self.dialg.boxkeys.title.SetLabel(title)
            self.dialg.boxkeys.bxSizer.Layout()
#        if self.gtyp=='qt':
#            self.dialg.boxkeys.title.SetLabel(n)        
    def makeButton(self,name,value,detail,typ):
        # find the dimension of the array
        txt = name
        a=txt.split('(')
        if len(a)>1:
            txt=str(a[0])+'('
            b=a[1][:-1].split(',')
            for s in b:
                exec('n=self.'+s)
                txt+=str(n)+','
            txt=txt[:-1]+')'
        #make the choice lists
        curVal = value
        bselect = None
        if detail not in [None,[]]: 
            if type(detail) == type([5]): #typ == choice doe snot work'
                txt+=' : '+detail[0]
                bcontent = detail[1:] #1st item is title line
                bselect = curVal
                typ = 'choice'
            elif typ == 'textlong' :
                txt+=' : '+detail
                bcontent = str(curVal)
            else :
                typ = 'text'
                txt+=' : '+detail
                bcontent = str(curVal)
        else :
            bcontent = str(curVal)
        return txt,typ,bcontent,bselect
