from config import *
from matplotlib import pylab as pl
from myInterpol import *

"""all geometrical operations are performed here
all coordinates are in real world ones. so matrices have index 0 for rows
at x=0. As modflow work the other way round, the transformation are done
by the modflow writer"""

def makeGrid(core,gIn):
    """ from a dictionnary returned by the addin dialog, creates a grid
    linear or irregular, x0, x1, y0,y1 are kept from the original
    """
    grd={}
    for n in ['x0','x1','y0','y1'] : exec(n+'=float(gIn[\''+n+'\'])')
    grd['x0'],grd['x1'],grd['y0'],grd['y1']=x0,x1,y0,y1;
    dx, dy = calcDx(core,gIn,x0,x1,'dx'),calcDx(core,gIn,y0,y1,'dy')
    grd['dx'],grd['dy'],grd['nx'],grd['ny']=dx,dy,len(dx),len(dy)
    return grd

def calcDx(core,gIn,x0,x1,name): 
    """calculates the grid fixed or variable on one dimension (always called dx in there"""     
    if name == 'dx' and gIn[name]=='fixed': dx=core.dicval['Modflow']['dis.4']
    elif name == 'dy' and gIn[name]=='fixed': dx=core.dicval['Modflow']['dis.5']
    elif len(gIn[name])==1 or gIn[name][1] in ['',' ']: # linear case
        dx = float(gIn[name][0])
        nx = int(round((x1-x0)/dx))
        dx = ones((nx))*dx
    else:
    # variable list dxi values at point xi
        dxIn = gIn[name] # a list of values
        ldx=linspace(0,0,0) # vect vides
        xi,dxi=[],[]
        for i in range(len(dxIn)):
            sxi=dxIn[i].split()
            if len(sxi)>1: 
                xi.append(float(sxi[0]));dxi.append(float(sxi[1]))
        for i in range(1,len(xi)):
            g2 = calcGriVar(xi[i-1],xi[i],dxi[i-1],dxi[i]);#print shape(ldx),shape(g2),g2
            ldx=concatenate([ldx,g2],axis=0)
        dx = ldx*1.
    return dx
    
def calcGriVar(x0,x1,dx0,dx1):
    """calculates variables grid between two points"""
    a=logspace(log10(dx0),log10(dx1),100);#print 'aq calcgriv',a
    n=round(100*(x1-x0)/sum(a))
    if n<=1:
        return [x1-x0]
    else :
        dxv=logspace(log10(dx0),log10(dx1),n);#print x0,x1,dx0,dx1,dxv
        if abs((dxv[0]-(x1-x0))) < dxv[0]/1000: return dxv[:1] # added 28/3/17 oa for fixed grids
        dxv[dxv==max(dxv)]+=x1-x0-sum(dxv) # to fit the total
        return dxv
    
def getNmedia(core):
    return len(core.addin.get3D()['topMedia'])
    
def makeLayers(core):
    """returns a list containing for each media the number of layers
    the list layers can have 3 possiblities : 
        - one value the same nb of layers in each media
        - a series of numbers : the nb of layers in each media
        - or two numbers for each media : the relative thickness of the first and last layer
    all oriented from bottom to top"""
    #zmin = core.addin.get3D()['zmin']
    litop = core.addin.get3D()['topMedia']
    nbM = len(litop) # nb of media may be string list
    lilay = core.addin.get3D()['listLayers']*1 # may be string list
    if core.addin.getDim()=='3D':
        if len(lilay)== 1:  
            lilay = [lilay[0]]*getNmedia(core)
        dzL = []
        for im in range(nbM):
            dzL.append([])
            if type(lilay[im]) in [type('a'),type(u'a')]: 
                if len(lilay[im].split())>1:
                    dz0, dz1 = lilay[im].split(); #[:2]
                    dzL[im] = calcGriVar(0,1,float(dz0),float(dz1))
                    lilay[im] = len(dzL[im])
                else : 
                    lilay[im]=int(lilay[im]); dzL[im] = [1./lilay[im]]*lilay[im]
            else :
                dzL[im] = [1./lilay[im]]*lilay[im]
    elif core.addin.getDim()=='2D':
        lilay=[1]
        dzL = [1.]
    else : # xsection radial
        nx,ny,xvect,yvect = getXYvects(core)
        lilay=[ny];dzL=[1.]
    #print 'geom 87 dzL',lilay,dzL
    return sum(lilay), lilay, dzL  #lilay : nb of layer per media, dzL relative thickness of a layer in a media 

def getNlayersPerMedia(core):    
    nbL, lilay, dzL = makeLayers(core)
    return lilay
def getNlayers(core):
    nbL, lilay, dzL = makeLayers(core)
    return nbL
    
def media2layers(core,media):
    nbL, lilay, dzL = makeLayers(core); #print 'geom', nbL,lilay,dzL,media
    if type(media)==type([5]):
        if len(media)>1:
            lay1 = sum(lilay[:media[0]])
            lay2 = sum(lilay[:media[-1]+1])
        else :# just one media in list
            m = int(media[0])
            lay1 = sum(lilay[:m])
            lay2 = sum(lilay[:m+1]) 
    else : # jsut one media (not in list)
        lay1 = sum(lilay[:media])
        lay2 = sum(lilay[:media+1]) 
    return arange(lay1,lay2).astype(int)   
    
def mediaInlayers(core):
    nbL, lilay, dzL = makeLayers(core)
    lim = [0]
    for nb in lilay: lim.append(lim[-1]+nb)
    return lim[:-1]

def makeZblock(core):
    """to create the block of cells in 3D, it is a 3D matrix"""
    nlay, lilay, dzL = makeLayers(core);#print 'geom l 113',nlay, lilay, dzL
    nbM = len(lilay)
    nx,ny,xvect,yvect = getXYvects(core); #print 'geom 118',nx,ny,xvect,yvect
    if core.dicaddin['Model']['group'][:5]=='Opgeo': return ones((1,1,1))
    if core.addin.getDim() not in ['Radial','Xsection']: # 2 or 3D case
        Zblock = zeros((nlay+1,ny,nx)) # it has a value on bottom and one on top
        intFlagT,intFlagB,option = False,False,''
        if core.dictype['Modflow']['dis.6'][0] =='formula': 
            formula = core.dicformula['Modflow']['dis.6'][0]
            if 'interp' not in formula: # in top all values are given by one formula
                exec(formula.replace('self','core'))
                return value # returns the whole block
            else : #case of interpolation, try to get the parameters
               for2 = formula.split('\n')
               for n in for2 : # to go only to opt but not until the calculation of value (not to do it twice)
                   exec(n.replace('self','core'))
                   if 'opt' in n: break
               intFlagT, optionT = True, opt
        #for bottom
        if core.dictype['Modflow']['dis.7'][0]=='formula':
            formula = core.dicformula['Modflow']['dis.7'][0]
            if 'interp' in formula: 
                for2 = formula.split('\n')
                for n in for2 : # to go only to opt but not until the calculation of value (not to do it twice)
                    exec(n.replace('self','core'))
                    if 'opt' in n: break
                intFlagB, optionB = True, opt
            # creates the first layer
        if intFlagT: 
            top = zone2interp(core,'Modflow','dis.6',0,optionT)
        else : 
            top =  zone2grid(core,'Modflow','dis.6',0,None,iper=0)
        Zblock[0] = top
        i = 0
        for im in range(nbM): # im is the media number
            if im<nbM-1:
                if intFlagT:
                    botm = zone2interp(core,'Modflow','dis.6',im+1,optionT,refer=top)
                else : 
                    botm = zone2grid(core,'Modflow','dis.6',im+1,None,iper=0)
            else :
                if intFlagB:
                    botm = zone2interp(core,'Modflow','dis.7',im,optionB,refer=top)
                else : 
                    botm = zone2grid(core,'Modflow','dis.7',im,None,iper=0)
            #creates the sublayers
            if lilay[im]==1: # just one sublayer
                dff = top-botm;#print 'geom 156 dff',shape(top),shape(botm),shape(Zblock[i+1]),dzL[im]
                limit = amax(amax(dff))/25 # limit the thick not to be 0
                Zblock[i+1] = top - maximum(dff,limit)*dzL[im]
                i+=1
            else: #dzL[im] is a list
                dz = array(dzL[im]);#print i,nbM,nlay,lilay,dzL
                for il in range(lilay[im]):
                    dff = top-botm
                    limit = amax(amax(dff))/100
                    Zblock[i+1] = top - maximum(dff,limit)*sum(dz[:il+1])
                    i += 1
            top = botm
    else : # radial and Xsection cases
        Zblock = ones((ny+1,1,nx));#print yvect
        for i in range(len(yvect)):
            Zblock[i] = yvect[ny-i];#print i,yvect[ny-i]
    #print Zblock
    return Zblock
    
def getXYvects(core):
    g = core.addin.getFullGrid()
    xvect=concatenate([array(g['x0'],ndmin=1),g['x0']+cumsum(g['dx'])],axis=0)
    yvect=concatenate([array(g['y0'],ndmin=1),g['y0']+cumsum(g['dy'])],axis=0)
    #print 'geom 180 grid',g, xvect
    return g['nx'],g['ny'],xvect,yvect

def getXYmeshCenters(core,plane,section):
    '''returns the center of each cell for a given plane and orientation'''
    a,b,xv0,yv0 = getXYvects(core);#print 'geom l 141',plane,layer
    xv1, yv1 = (xv0[1:]+xv0[:-1])/2, (yv0[1:]+yv0[:-1])/2
    nlay = getNlayers(core)
    zb = core.Zblock
    if core.addin.getDim() not in ['Radial','Xsection']: # 2 or 3D case
        if plane=='Z': return meshgrid(xv1,yv1)
        elif plane == 'Y':
            return xv1*ones((nlay,1)),zb[:,section,:]
        elif plane == 'X':
            return yv1*ones((nlay,1)),zb[:,:,section]
    else : # radial or cross section
        return meshgrid(xv1,yv1)

def getXYmeshSides(core,plane,section):
    '''returns the sides of the cells for a given plane and orientation'''
    a,b,xv1,yv1 = getXYvects(core);#print 'geom l 141',plane,layer
    nlay = getNlayers(core)
    zb = core.Zblock
    if core.addin.getDim() not in ['Radial','Xsection']: # 2 or 3D case
        if plane=='Z': return meshgrid(xv1,yv1)
        elif plane == 'Y':
            zb1 = zb[:,section,:]
            return xv1*ones((nlay+1,1)), c_[zb1[:,:1],(zb1[:,:-1]+zb1[:,1:])/2, zb1[:,-1:]]
        elif plane == 'X':
            zb1 = zb[:,:,section]
            return yv1*ones((nlay+1,1)), c_[zb1[:,:1],(zb1[:,:-1]+zb1[:,1:])/2, zb1[:,-1:]]
    else : # radial or cross section
        return meshgrid(xv1,yv1)
        
def getMesh3D(core):
    '''returns the coordinates of the cell sides in 3D'''
    x1,y1=getXYmeshSides(core,'Z',0);ny,nx=shape(x1)
    z1=core.Zblock;nz,a,b=shape(z1)
    z2=concatenate([z1[:,:,:1],z1],axis=2)
    z2=concatenate([z2[:,:1,:],z2],axis=1)
    x2=x1*ones((nz,ny,nx))
    y2=y1*ones((nz,ny,nx))
    return x2,y2,z2
    
def getMesh3Dcenters(core):
    '''returns the coordinates of the cell centers in 3D'''
    x1,y1=getXYmeshCenters(core,'Z',0)
    z1=core.Zblock
    z2=z1[1:,:,:]/2+z1[:-1,:,:]/2
    x2=x1*ones(shape(z2))
    y2=x2*ones(shape(z2))
    return x2,y2,z2
    
def block(core,modName,line,intp=False,opt=None,iper=0):
    if core.addin.getModelGroup()=='Fipy':
        #if core.dicval['FipyFlow']['domn.1'][0] == 1:
        return blockUnstruct(core,modName,line,intp,opt,iper)
    else :
        return blockRegular(core,modName,line,intp,opt,iper)
        
def blockUnstruct(core,modName,line,intp,opt,iper):
    '''returns data for a 3D unstructured block'''
    if modName=='Fipy':
        return zone2mesh(core,modName,line)
    elif modName[:5]=='Opgeo':
        if intp==0:
            return zone2mesh(core,modName,line)
        else : 
            return zone2interp(core,modName,line,0,opt)
        
def zone2mesh(core,modName,line,media=None,opt=None,iper=0):
    """return a vector of values for one property over a mesh, values are given
    through zones but only rectangle zones work"""
    vbase = core.dicval[modName][line][0]
    mod0 = modName[:-4].lower()
    exec('mesh = core.addin.'+mod0)
    xc, yc = mesh.getCellCenters()
    nbc = mesh.getNumberOfCells()
    value = array([vbase]*nbc)
    dicz = core.diczone[modName].dic
    if dicz.has_key(line)==False:
        return value
    dicz = dicz[line]
    for iz in range(len(dicz['coords'])):
        coo = dicz['coords'][iz];#print coo
        if len(coo)==1: # one point
            d = sqrt((coo[0][0]-xc)**2+(coo[0][1]-yc)**2)
            ind = nonzero(equal(d, amin(d)))[0]
        else : # a polygon but up to now only rectangular
            x,y = zip(*coo)
            ind = where((xc>min(x))&(xc<max(x))&(yc>min(y))&(yc<max(y)))[0]
        if core.ttable.has_key(line):zv0=float(core.ttable[line][iper,iz])
        else : zv0 = float(dicz['value'][iz])
        if opt=='zon' : value[ind] = iz
        else : value[ind] = zv0
    return value
    
def blockRegular(core,modName,line,intp,opt,iper):
    """creates a block for one variable which has a size given by the x,y,z 
    given by addin
    intp : flag for interpolation can be one bool (for all layers) or a list of bool"""
    nx,ny,xvect,yvect = getXYvects(core)
    nmedia = getNmedia(core)
    nlayers = getNlayers(core)
    lilay = getNlayersPerMedia(core)
    g = core.addin.getFullGrid()
    if type(intp)!=type([5,6]): intp=[intp]*nmedia # to create a list of interpolation
    if core.addin.getDim() in ['2D','3D']:
        m0 = ones((nlayers,ny,nx))
        lay = 0
        for im in range(nmedia): # 3D case, includes 2D
            if intp[im] :
                a = zone2interp(core,modName,line,im,opt)
            else :
                a = zone2grid(core,modName,line,im,opt,iper)
            for il in range(int(lilay[im])): # several layers can exist in each media
                m0[lay]=a
                lay +=1
    else : #X section and radial
        a = zone2grid(core,modName,line,0,opt,iper)
        m0 = reshape(a,(ny,1,nx))
        m0 = m0[-1::-1]
    linesRadial = ['bcf.4','bcf.6','bcf.7','bcf.8','lpf.8','lpf.10','lpf.11',
        'btn.11','rct.2a','rct.2b']
    dx = array(g['dx'])
    if (core.addin.getDim()=='Radial') & (line in linesRadial):
        for i in range(ny): m0[i] = m0[i]*(cumsum(dx)-dx/2.)*6.28
    if line=='lpf.9' and core.getValueFromName('Modflow','CHANI')==0:  # ratio Kh/Kv shall not be scaled
        for i in range(ny): m0[i] = m0[i]*(cumsum(dx)-dx/2.)*6.28
    return m0

def zone2grid(core,modName,line,media,opt,iper):
    """ put zone information on the correct grid
    if the grid is 3D then looks for information of layers
    zone keys 'number','name','coords','media','value','type'
    shall work with regular and vairable grids, but does not provide filled zone 
    if the zone contains z values (variable polygon)"""
    lval = core.dicval[modName][line]
    if media<len(lval): vbase=float(lval[media])
    else : vbase =float(lval[0])
    if opt in['BC','zon']: vbase=0
    nx,ny,xvect,yvect = getXYvects(core)
    m0=ones((ny,nx))*vbase
    #print 'geom 322',line,core.dictype[modName][line],#core.diczone[modName].dic
    if core.dictype[modName][line][0]=='array': # type of array, dont calculate
        arr = core.dicarray[modName][line];#print 'geom zone2g type arr',line
        if len(shape(arr))==3: arr = arr[media]
        return arr
    elif core.diczone[modName].dic.has_key(line):
        diczone = core.diczone[modName].dic[line]
    else : 
        return array(m0) # returns an array of vbase
    lz = len(diczone['name'])
    #print 'geo z2g',line,core.ttable[line]
    
    for i in range(lz):  # loop on zones
        if diczone['value'][i]=='': continue
        xy = diczone['coords'][i]#;core.gui.onMessage(str(xy))
        zmedia = diczone['media'][i] # a media or a list of media for the zone
        if type(zmedia)!=type([5]): zmedia=[zmedia]
        zmedia = [int(a) for a in zmedia]
        if int(media) not in zmedia: continue # the zone is not in the correct media
        if core.ttable.has_key(line):zv0=float(core.ttable[line][iper,i])
        else : zv0 = float(diczone['value'][i])
        if len(xy)==1:  # case point
            x,y=zip(*xy)
            ix,iy = minDiff(x[0],xvect),minDiff(y[0],yvect)
            m0[iy,ix] = zv0
            
        else: # other shapes
            #print xy
            ndim=len(xy[0])
            if ndim==3: x,y,z = zip(*xy) # there are z values (variable polygon)
            else :
                x,y = zip(*xy)
                z=[zv0]*len(xy)
            nxp,nyp,nzp=zone2index(core,x,y,z);
            put(m0,nyp*nx+nxp,nzp)
            if ndim==3: continue # a zone with z value is not filled!!
            ind = fillZone(nx,ny,nxp,nyp,nzp)
            putmask(m0, ind==1, [zv0])
    #print 'zonemat',line,m0 
    return array(m0)

def fillZone(nx,ny,nxp,nyp,nzp):
    # fill zone with vertical lines
    js = argsort(nxp);
    nxs, nys = take(nxp,js), take(nyp,js)            
    lls = len(nxs)
    ind1 = zeros((ny,nx))
    mn, mx = int(nys[0]),int(nys[0])
    for j in range(1,lls):
        if nxs[j]<>nxs[j-1]:
            ind1[mn:mx+1,int(nxs[j-1])] = [1]*(mx-mn+1)
            mn,mx = int(nys[j]),int(nys[j])                    
        mn,mx = int(min(mn,nys[j])),int(max(mx,nys[j]))
    ind1[mn:mx+1,int(nxs[lls-1])] = [1]*(mx-mn+1)
    # fill zone with horizontal lines
    js = argsort(nyp)
    nxs, nys = take(nxp,js),take(nyp,js)
    ind2 = zeros((ny,nx))
    mn, mx = int(nxs[0]),int(nxs[0])
    for j in range(1,lls):
        if nys[j]<>nys[j-1]:
            ind2[int(nys[j-1]),mn:mx+1] = [1]*(mx-mn+1)
            mn,mx = int(nxs[j]),int(nxs[j])                    
        mn,mx = int(min(mn,nxs[j])),int(max(mx,nxs[j]))                
    ind2[int(nys[lls-1]),mn:mx+1] = [1]*(mx-mn+1)
    ind = ind1*ind2  ## both indices must equal 1 to fill the zone
    return ind

def zone2index(core,x,y,z,opt=None):
    """ returns indices of cells below a poly zone"""
    nx,ny,xvect,yvect = getXYvects(core)
    nxp,nyp,nzp=array(minDiff(x[0],xvect)),array(minDiff(y[0],yvect)),array(z)
    #print 'zoneindex',nxp,nyp,nzp
    if len(x)==1:
        if opt==None: return nxp,nyp,nzp
        elif opt=='angle': return nxp,nyp,nzp,[0],[0]
    nxp=array([],dtype='int');nyp=nxp*1;
    nzp=array([],dtype='float');nsn=nzp*1;ncs=nzp*1
    for j in range(1,len(x)):
        ix1=minDiff(x[j-1],xvect);ix2=minDiff(x[j],xvect);
        iy1=minDiff(y[j-1],yvect);iy2=minDiff(y[j],yvect);#print y[0],yvect
        if ix1==ix2 and iy1==iy2: continue
        sensx,sensy=sign(ix2-ix1),sign(iy2-iy1);
        lx,ly=abs(ix2-ix1),abs(iy2-iy1)
        ll=max(lx,ly)
        dz=z[j]-z[j-1];#print ix1,ix2,iy1,iy2,sensx,xvect
        if lx>=ly:
            ixp=arange(ix1,ix2+sensx,sensx);
            iyp=ixp*0;xv2=xvect[ixp]
            yv2=y[j-1]+(xv2-xv2[0])*(yvect[iy2]-yvect[iy1])/(xv2[-1]-xv2[0]);
            for k in range(ll+1): iyp[k]=minDiff(yv2[k],yvect)
            zp=z[j-1]+dz*(xv2-x[j-1])/(x[j]-x[j-1]);#print ixp,xv2,iyp,yv2,zp
        else:
            iyp=arange(iy1,iy2+sensy,sensy);
            ixp=iyp*0;yv2=yvect[iyp];
            xv2=x[j-1]+(yv2-yv2[0])*(xvect[ix2]-xvect[ix1])/(yv2[-1]-yv2[0]);
            for k in range(ll+1): ixp[k]=minDiff(xv2[k],xvect)
            zp=z[j-1]+dz*(yv2-y[j-1])/(y[j]-y[j-1]);
        nxp=concatenate([nxp,clip(ixp,0,nx-1)],axis=0)           
        nyp=concatenate([nyp,clip(iyp,0,ny-1)],axis=0)
        nzp=concatenate([nzp,zp],axis=0)     
        dx,dy = x[j]-x[j-1],y[j]-y[j-1]
        sn0,cs0 = dy/sqrt(dx**2+dy**2),dx/sqrt(dx**2+dy**2)
        sn,cs = ones((ll+1))*sn0,ones((ll+1))*cs0
        nsn,ncs = concatenate([nsn,sn],axis=0),concatenate([ncs,cs],axis=0)                   
    #nyp=ny-nyp-1
    if len(nxp)<1:
        nxp,nyp,nzp=array(minDiff(x[0],xvect)),array(minDiff(y[0],yvect)),array(z)
    mix=nxp*1000+nyp;a,ind=unique(mix,return_index=True);ind=sort(ind)
    #print 'geom zoneind',nxp,nyp,nzp
    if opt==None:
        return nxp[ind].astype(int),nyp[ind].astype(int),nzp[ind]
    elif opt=='angle':
        return nxp[ind].astype(int),nyp[ind].astype(int),nzp[ind],nsn[ind],ncs[ind]

def minDiff(x,xvect):
    d=x-xvect; d1=d[d>0.];
    if len(d1)==0: return 0
    else :
        a=where(d==amin(d1));return a[0]
        
def isclosed(core,x,y):
    nx,ny,xv,yv=getXYvects(core)
    ix,iy = minDiff(x[0],xv),minDiff(y[0],yv)
    dmin=min(xv[ix+1]-xv[ix],yv[iy+1]-yv[iy]) # modified 22/3/2017 for variable grid
    d0=sqrt((x[0]-x[-1])**2+(y[0]-y[-1])**2);
    if d0<dmin[0]: return True
    else : return False
    
##########################Gmesh ########################
def gmeshString(dicD,dicM):
    """creates a gmesh string to use in gmesh to generate the mesh
    dicD is the domain zones, containing points, lines and domain
    dicM is the media zones dict, they will be used to build the grid"""
    s,p_list,p_link = '',[],[]
    i_domn = dicD['name'].index('domain') # search for the line called domain
    dcoords = dicD['coords'][i_domn]
    dens=  dicD['value'][i_domn]
    ldom=len(dcoords)
    # domain points
    for i,pt in enumerate(dcoords):
        s+='Point('+str(i+1)+')={'+str(pt[0])+','+str(pt[1])+',0,'+dens+'}; \n'
        p_list.append(pt)
    npt = i+1
    # domain line
    s+= stringLine(p_link,range(ldom),1,opt='close')
    #other points: present in domain, name shall start by point
    indx = [dicD['name'].index(b) for b in dicD['name'] if b[:5]=='point']
    p_coord = [dicD['coords'][iz] for iz in indx]
    p_dens = [dicD['value'][iz] for iz in indx]
    if len(p_coord)>0:
        p_list,p_link,spt,s1 = stringPoints(p_list,p_coord,p_dens,npt)
        s+=s1
        npt += len(p_coord)
    # other lines present in the domain
    for iz,n in enumerate(dicD['name']):
        if n[:4]=='line':
            p_coord = dicD['coords'][iz]
            p_dens = dicD['value'][iz]
            p_list,p_link,spt,s1 = stringPoints(p_list,p_coord,p_dens,npt)
            s+=s1
            p_range = range(npt,npt+len(p_coord))
            s+= stringLine(p_link,p_range,npt)
            npt += len(p_coord)
            #for p in p_list:
            #    s+='Line{'+str(p+1)+'} In Surface{1}; \n'
            #npt += 1
    # add the K zones, but don't add points twice!!
    isurf = 2
    for iz in range(1,len(dicM['name'])): # the 1st zone is the domain
        p_coord = dicM['coords'][iz]
        x,y = zip(*p_coord); #dns = min(max(y)-min(y),max(x)-min(x))/2
        if len(p_coord)>2: # don't take points, just lines
            p_list,p_link,spt,s1 = stringPoints(p_list,p_coord,dens,npt)
            s+=s1
            p_range = range(npt,npt+len(p_coord))
            s+= stringLine(p_link,p_range,isurf,'close')
            npt += len(p_coord)
            s+='Plane Surface('+str(isurf)+')={'+str(isurf)+'}; \n';
            s+='Physical Surface('+str(isurf)+')={'+str(isurf)+'}; \n';
            #for p in p_range:
            #    s+='Line{'+str(p+1)+'} In Surface{1}; \n'
            isurf+=1
    if isurf ==2 : a=''
    else : a = ','+','.join([str(x) for x in range(2,isurf)])
    s+='Plane Surface(1)={1'+a+'}; \n';
    s+='Physical Surface(1)={1}; \n';
    for ip in range(npt):
        s+='Point{'+str(ip+1)+'} In Surface{1}; \n'
    return s
            
def stringPoints(p_list,p_coord,p_dens,istart):    
    '''creates lines of points from coordinates and returns the point list'''
    s,spt,p_link='','',[]
    if type(p_dens) != type([5]): 
        p_dens = [p_dens]*len(p_coord)
    for ip,coo in enumerate(p_coord):
        prf =''
        if coo in p_list: 
            p_link.append([istart+ip,p_list.index(coo)]) # make th elink btw the presnet pt and the existing one with same doords
            prf='//' # don't add twice the same point
        p_list.append(coo) # store the point
        dens = p_dens[ip]
        if type(coo[0])==type((5,6)): coo = coo[0]
        s+=prf+'Point('+str(istart+ip+1)+')={'+str(coo[0])+','+str(coo[1])+',0,'+dens+'}; \n'
        spt+= str(istart+ip+1)+','
    return p_list,p_link,spt,s
    
def stringLine(p_link,p_range,il,opt='None'):
    '''creates a line string from a list of points number'''
    s,pnew,pold='',[],[]
    if len(p_link)>0: pnew,pold = zip(*p_link) # get the new and old ref of the same points
    s+='// p '+str(pnew)+'  '+str(pold)+'\n'
    l_link = []
    #print pnew,pold
    for i in p_range[:-1]:
        prf='';#print i
        if (i in pnew) and (i+1 in pnew):
            if pold[pnew.index(i+1)]==pold[pnew.index(i)]+1: # the line must be in the same order
                l_link.append((i,pold[pnew.index(i)]))
                prf='//' # don't write an existing line
        a,b = ptreplace(pold,pnew,i,i+1)
        s+=prf+'Line('+str(i+1)+')={'+str(a)+','+str(b)+'}; \n'
    if opt=='close':
        a,b = ptreplace(pold,pnew,p_range[-1],p_range[0])
        s+='Line('+str(p_range[-1]+1)+')={'+str(a)+','+str(b)+'}; \n'
    if opt=='None': p_range = p_range[:-1]
    v,lnew,lold='',[],[]
    if len(l_link)>0:lnew,lold = zip(*l_link)
    s+='// l'+str(lnew)+'  '+str(lold)+'\n'
    for ip in p_range:
        if ip in lnew: v+=str(lold[lnew.index(ip)]+1)+','
        else : v+=str(ip+1)+','
    s+='Line Loop('+str(il)+')={'+v[:-1]+'};\n'
    return s
    
def ptreplace(pold,pnew,i,j):
    a = i+1
    if i in pnew: a = pold[pnew.index(i)]+1
    b = j+1
    if j in pnew: b = pold[pnew.index(j)]+1
    return a,b
###################### INTERPOLATION ####################

def zone2interp(core,modName,line,media,option,refer=None):
    """ interpolation case from points or zones to matrix
    option interp. ID or interp. Kr
    for interp. Kr, you can add range and type : 'interp. Kr;vrange=2.;vtype=\'spher\''
    type are presently spher for spherical and gauss for gaussian
    if refer is not None, it is a reference grid and the interpolation will be done
    on the difference btw th epresent variable and the reference"""
    #print 'interp 512', line,media, option
    # find the interpolation options
    vrange,vtype = None,None
    if ';' in option: 
        op = option.split(';')
        option  = op[0]
        for i in range(1,len(op)): exec(op[i].replace('@','\''))
    #get the zones
    vbase=float(core.dicval[modName][line][media])
    # create teh vector of points on which interpolation will be done
    if modName[:5] == 'Opgeo':
        mod0 = modName[:-4].lower()
        exec('mesh = core.addin.'+mod0)
        xc, yc = mesh.elcenters
    else :
        nx,ny,xv,yv = getXYvects(core);nz=0
        xv,yv = (xv[1:]+xv[:-1])/2.,(yv[1:]+yv[:-1])/2.;#print 'xv',xv,yv
        xm,ym = meshgrid(xv,yv)
        xc, yc = ravel(xm),ravel(ym)
        if refer != None : refer = ravel(refer)
    m = zeros(len(xc)) + float(vbase)
    if core.diczone[modName].dic.has_key(line):
        diczone = core.diczone[modName].dic[line]
        coords = diczone['coords']
        nz = len(coords)
    else : 
        if modName[:5] != 'Opgeo':
            m = reshape(m,(ny,nx))
        return m # strange!!
    #creates the list of point values
    xpt,ypt,zpt=[],[],[];
    for i in range(nz):  # loop on zones to get coordinates
        #print diczone['media'][i]
        if type(diczone['media'][i]) in [type(5),type('5')]:
            if int(diczone['media'][i])!=media : continue
        else : #list of media for one zone
            if media not in diczone['media'][i]: continue
        xy = coords[i]
        if len(xy[0])==2: #normal zone
            x,y = zip(*xy)
            z = float(diczone['value'][i])
            z = [z]*len(x);#print i,z
        elif len(xy[0])==3: # variable polygon
            x,y,z = zip(*xy)
        xpt.extend(list(x));ypt.extend(list(y));zpt.extend(list(z))            
    xpt,ypt,zpt = array(xpt),array(ypt),array(zpt);#print 'geom, xpt',xpt,ypt,zpt

    if len(xpt)==0: 
        if modName[:5] != 'Opgeo': m = reshape(m,(ny,nx))
        return m
    #makes the difference if refer is not none
    #print shape(xc),shape(yc)
    """if refer != None:
        for i in range(len(xpt)):
            d = sqrt((xpt[i]-xc)**2+(ypt[i]-yc)**2)
            ix = where(d==amin(d))[0];#print ix
            zpt[i] = refer[ix[0]]-zpt[i]"""

    #print 'geom 503',modName,line,option
    if option=='interp. ID':
        pol=polyfit2d(xpt,ypt,zpt,order=1)
        z0=polyval2d(xpt,ypt,pol);#print 'z0',z0
        dz=zpt-z0;#print 'dz',xpt,ypt,zpt,z0,dz
        m0=polyval2d(xc,yc,pol);#print 'm0',m0
        m1 = invDistance(xpt,ypt,dz,xc,yc,power=0.66);#print 'm1',m1
        m2 = m0+m1 

    elif option =='interp. Kr':
        mxdist = sqrt((max(xc)-min(xc))**2+(max(yc)-min(yc))**2)
        if vrange==None: rg = mxdist/4.
        else : rg = vrange
        if len(xpt)<5: m2 = m
        else : m2 = krige(xpt,ypt,zpt,rg,xc,yc,vtype=vtype)
        
    elif option=='interp. Th': # Thissen polygons
        listP = zip(xpt,ypt)
        xb,yb = [min(xc),max(xc)],[min(yc),max(yc)]
        polylist = getPolyList(listP,xb,yb);#print polylist
        m2 = ones(len(xc))*vbase
        for i,poly in enumerate(polylist):
            if poly==None: continue
            x,y = zip(*poly);z=[0]*len(x)
            nxp,nyp,nzp=zone2index(core,x,y,z);
            ind = fillZone(nx,ny,nxp,nyp,nzp)
            putmask(m2, ind==1, [zpt[i]]);#print 'geom 611',xpt[i],ypt[i],zpt[i],poly
        
    #m2 = clip(m2,amin(zpt),amax(zpt));#print amin(amin(m2))
    #if refer != None:
        #m2 = refer - m2#
    if modName[:5] != 'Opgeo':
        m2 = reshape(m2,(ny,nx))
        if option=='interp. Th':   #smoothing of thiessen polys     
            for n in range(vrange): m2 = smoo2d(m2)

    return m2
    
def smoo2d(m):
    m1=m*1
    m1[1:-1,1:-1]=m1[1:-1,:-2]/5+m1[1:-1,1:-1]/5+m1[1:-1,2:]/5+m1[:-2,1:-1]/5+m1[2:,1:-1]/5
    return m1
############################# IMPORT MODFLOW ASCII FILES ###################
def mat2zones(varname,zones,mat,layer):
    """a method that finds zones from matrices, it is based on contour
    function from matplotlib followed by a simplification of the contours
    xc : centers of """
    zval = sort(unique(mat)) # values present in the matrix
    vbase,zval = getvbase(mat,zval)
    mat,pts = getpoints(mat,zval,vbase)
    # remove points
    if len(zval)<30: # calculates the levels of the contours
        zlev = zval*1.001;zlev[-1]=zval[-1]*.999;#print 'zlev',zlev
    else : 
        zlev = linspace(zval[0]*.999,zval[-1]*1.001,num=25)
    c = pl.contour(mat,levels=zlev)
    coll=c.collections
    
    def getvbase(mat,zval):
        """ vbase is search as the most frequent value"""
        lmax=0
        zv2 = list(zval)
        for v in zv2:
            lr,lc=where(mat==v)
            if len(lr)>lmax: 
                lmax=len(lr);vb = v
        zv2.remove(vb)
        return vb, array(zv2)
        
    def getpoints(mat,zval,vbase):
        nr,nc = shape(mat)
        pts = []
        for v in zval:
            lr,lc=where(mat==v)
            mat1= ([mat==v])*1
            for i in range(len(lr)):
                lr1,lr2 = max(lr[i]-1,0),min(lr[i]+2,nr)
                lc1,lc2 = max(lc[i]-1,0),min(lc[i]+2,nc)
                s1 = sum(mat1[lr1:lr2,lc1:lc2])
                if s1 == 1:
                    mat[lr[i],lc[i]]=vbase
                    pts.append((lr[i],lc[i]))
        return mat,pts
            
    def incenters(centers,xm,ym):
        d=min(abs(xm)/100.,abs(ym)/100.)
        for coo in centers:
            if abs(xm-coo[0])<d and abs(ym-coo[1])<d: return True
        return False

    def listcenters(coll,zlev,vbase):
        # make a list of centers keeping only the usefull ones
        centers=[];zlev=array(zlev)
        ind1,ind2=where(zlev<vbase)[0],where(zlev>vbase)[0]
        #zlev1,zlev2=zlev[zlev<vbase],zlev[zlev>vbase]
        for i in ind1:
            for p in coll[i]._paths:
                x,y = p.vertices[:,0],p.vertices[:,1];
                xm,ym=mean(x),mean(y)
                if incenters(centers,xm,ym)==False:
                    centers.append((xm,ym,zlev[i]))
        ind2=ind2[-1::-1] # reverse
        for i in ind2:
            for p in coll[i]._paths:
                x,y = p.vertices[:,0],p.vertices[:,1];
                xm,ym=mean(x),mean(y)
                if incenters(centers,xm,ym)==False:
                    centers.append((xm,ym,zlev[i]))
        return centers
                
    def simplify(x,y):
        # starts from one contour and simplifies: removes points in lines
        d=sqrt((x[1:]-x[:-1])**2.+(y[1:]-y[:-1])**2.)
        #print x,y
        med_d=median(d);#print 'in simp',x,y,med_d
        ind=where(d<med_d/2.) # there are points very close one to the other in the angles
        x2,y2=x[ind],y[ind];# first coords of the zone
        # removing the segments that are in the same alignment
        dx2,dy2=x2[1:]-x2[:-1],y2[1:]-y2[:-1]
        angl=arctan(dy2/dx2)
        x3,y3=[],[];angl0=-100;lx=len(x2)-1;#print len(x),len(x2)
        for i in range(lx):
            if abs(angl[i]-angl0)>1e-2:
                x3.append(x2[i])
                y3.append(y2[i])
                angl0=angl[i]
        return x3,y3
    
    def incenters2(centers,xm,ym,z):
        for coo in centers:
            if xm==coo[0] and ym==coo[1] and z==coo[2]: return True
        return False
    
    centers = listcenters(coll,zlev,vbase);#print centers
    nb=1
    if zones=='':
        zones={'number':[],'name':[],'coords':[],'media':[],'value':[],'type':['']}
    for i in range(len(coll)):
        for p in coll[i]._paths :
            x,y = p.vertices[:,0],p.vertices[:,1];
            xm,ym=mean(x),mean(y)
            if incenters2(centers,xm,ym,zlev[i])==True:
                if len(x)>5: x,y=simplify(x,y)
                zones['coords'].append(zip(x,y))
                zones['value'].append(zlev[i])
                zones['media'].append(layer)
                zones['number'].append(nb)
                zones['name'].append(varname+str(nb))
                nb+=1
    return zones
    
#def findConnected(mat):
#    zlev = unique(mat)
#    lrow,lcol = where(mat==zlev[0])
#    if len(lrow)==1 : point
#    # if more than 80% of the points -> the background, don't treat
#    mnr,mnc = min(lrow),min(lcol)
#    #search all neighbors of one points and store them in one zone
#    # go to the next 