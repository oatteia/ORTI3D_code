import scipy.sparse as sp
from scipy.sparse.linalg import *
from scipy.special import erf,erfc
from scipy.stats import norm
from config import *
#import rflowC
import os,time
 
class instantFit():
    
    def __init__(self,core):
        self.core,self.gui = core,core.gui
        grd = self.core.dicaddin['Grid'];#print grd
        self.domain = [grd['x0'],grd['x1'],grd['y0'],grd['y1']]
        self.dx, self.dy = float(grd['dx'][0]),float(grd['dy'][0])
        self.nrow,self.ncol = len(grd['dy']),len(grd['dx'])

    def calculate(self,dic_options,obs_value):
        # get current zone and changes its value
        #print obs_value,dic_options
        if obs_value=='dialog': #means that the value was returned by the dialog, change the K of the zone
            if dic_options['zvalue']!=0:
                delta = 1; #dic_options['zvalue']-old_value
                dicz = self.core.diczone['Modflow'];#print dicz.dic
                line = self.gui.modifBox.parent.currentLine
                iz = self.gui.modifBox.izone#dicz.getIndexFromName(line,zname);
                val  = float(dicz.getValue(line,'value',iz)) # just one value
                #print 'line,iz',line,iz,val,delta
                dicz.setValue(line,'value',iz,val*1.5**delta)
        self.K = self.core.getValueLong('Modflow','lpf.8',0)[0]  # here its 2D
        self.Darcy()
        if dic_options['type']=='Tracer':
            self.aL,self.aT = dic_options['dispersion']
            self.Sourcexy = self.core.diczone['Mt3dms'].getValue('btn.13','coords',0)
            self.SourceC = float(self.core.diczone['Mt3dms'].getValue('btn.13','value',0))
            xp1,yp1,tp1,cu1,cu2,V,Large,Cinf = self.calcTubes2D();#print shape(xp1),shape(Cinf)
            #to put in the cneter of the cells
            xp1, yp1 = (xp1[:,1:]+xp1[:,:-1])/2,(yp1[:,1:]+yp1[:,:-1])/2
            cu1, tp1 = (cu1[:,1:]+cu1[:,:-1])/2,(tp1[:,1:]+tp1[:,:-1])/2
            t = float(self.gui.guiShow.getCurrentTime())
            C = self.calcTime(xp1,yp1,tp1,cu1,Cinf,t);#print C
            self.xp1,self.yp1,self.C = xp1,yp1,C
        
    def Darcy(self):
        '''K is the Hyd cond matrix, H_bc is a matrix of initial H values with BC on sides
        size of marices : K (nl, nc), bc nl or nc, H nl-2, nc-2 : no bc cells
        M the preconditioner'''
        #pass
        K,H_bc = self.K,self.H_bc;#print 'in darcy', K[20:25,20:25]
        nr,nc = shape(K)
        ncell = (nc-2)*(nr-2)
        Kr = sqrt(K[:-1,1:-1]*K[1:,1:-1])/self.dy; # K interpolated in y dir top-bottom (rows)
        Kc = sqrt(K[1:-1,:-1]*K[1:-1,1:])/self.dx; # K interpolated in x dir left-right (columns)
        Kc1, Kc2 = Kc[:,:-1]*1,Kc[:,1:]*1
        Kr1, Kr2 = Kr[:-1,:]*1,Kr[1:,:]*1
        Kr1[0,:]=0;Kr2[-1,:]=0 
        Kc1[:,0]=0;Kc2[:,-1]=0 
        sK = Kr[:-1,:]+Kr[1:,:]+Kc[:,:-1]+Kc[:,1:]
        r1,r2 = r_[ravel(-Kr1)[nc-2:],zeros(nc-2)],r_[zeros(nc-2),ravel(-Kr2)[:2-nc]]
        lK = [ravel(sK),r_[ravel(-Kc1)[1:],0],r_[0,ravel(-Kc2)[:-1]],r1,r2]
        diags=[0,-1,1,-nc+2,nc-2]
        KM = sp.spdiags(lK,diags,ncell,ncell) # put Kv in first diagonal
        BC = zeros((nr-2,nc-2))#Q + Boundary Conditions
        BC[0,:] = Kr[0,:]*H_bc[0,1:-1]
        BC[-1,:] = Kr[-1,:]*H_bc[-1,1:-1]
        BC[:,0] += Kc[:,0]*H_bc[1:-1,0]
        BC[:,-1] += Kc[:,-1]*H_bc[1:-1,-1]
        Hout = spsolve(sp.csr_matrix(KM),ravel(BC)); #gmres(KM,ravel(BC),tol=1e-16,M=M)[0] # M=M
        H = H_bc*1
        H[1:-1,1:-1] = reshape(Hout,(nr-2,nc-2))
        self.Q = [-sqrt(K[:,:-1]*K[:,1:])*(H[:,1:]-H[:,:-1])/self.dx,
                  -sqrt(K[:-1,:]*K[1:,:])*(H[1:,:]-H[:-1,:])/self.dy]
        self.H = H

    def calcTubes2D(self,opt=0,ls1=None):
        """ methode pour calculer l'avancement des particules, necessite la position
        de la source, les dimensions de la grille et les vitesses, contenues dans model
        et les donnees de erfmat.
        La focntion retourne la position des particules pour un temps infini :
        XP0,YP0 les coordonnees des particules
        TP et CU: temps de la particule en chaque point XP,YP et CU distance depuis la source
        ???on ne tient pas compte de variation epaissseur dans calc vitesses
        donc pas necessaire ensuite pour calc de concentration???"""
        #initialisation des valeurs
        q = self.Q # darcy velocities
        x0,x1,y0,y1 = [float(a) for a in self.domain]
        dx,dy = self.dx,self.dy
        aL,aT  =  self.aL,self.aT
        poro = 0.25
        vx,vy = q[0]/poro, q[1]/poro
        xy  =  self.Sourcexy;x, y = zip(*xy); x=list(x); y=list(y);
        yp0=array([0,.08,.2,.3,.4,.5,.58,.65,.7,.75,.8,.85,0.89,.92,.94,.96,0.985,0.999])
        # inverse the source if necessary
        jp = ((x[0]+x[1])/2-x0)/dx;jp =int(jp);jp=max(jp,0)
        ip = ((y[0]+y[1])/2-y0)/dy;ip =int(ip);ip=max(ip,0)
        vx1 = vx[ip,jp]; vy1 = vy[ip,jp]
        if abs(vx1)>abs(vy1) :
            if sign(y[0]-y[1])<>sign(vx1):
                x.reverse(); y.reverse()
        else :
            if sign(x[1]-x[0])<>sign(vy1):
                x.reverse(); y.reverse()
        # assemble data for the calculation
        data = (x0,dx,y0,dy,aT,aL,0.);# print data
        ypi=r_[-yp0[-1:0:-1],yp0]/2.
        xpi=ypi*0.;
        xpin = (x[0]+x[1])/2.+ypi*(x[0]-x[1]) # 
        ypin = (y[0]+y[1])/2.+ypi*(y[0]-y[1]);
        np=len(xpin)
        clm = None # seems that it is not used
        tstart=time.time()
        alph0=-sign(ypi)*norm.isf(.5+abs(ypi),0.,.25); # distribution of starting point along the source line
        #alph0[abs(alph0)>.5]=alph0[abs(alph0)>.5]*1.5 # pour avoir conc faibe plus sur le cote
        alph0=(exp(abs(alph0))-1)*sign(alph0) # correction for the sides
        [xp0,yp0,tp0,cua,cub]=rflowC.calcTube1(data,alph0,vx,vy,xpin,ypin,clm);
        #print 'xp,yp,tp,cua,cub',xp0,yp0,tp0,cua,cub
        [xp1,yp1,tp1,cu1,cu2,V,Large,Cinf] = self.calcConc(xp0,yp0,tp0,cua,cub); 
        dt=time.time()-tstart;#print 'xp1b',xp1[0,:]#print dt
        return [self.smoo(xp1),self.smoo(yp1),tp1,cu1,cu2,V,Large,self.smoo(Cinf)]
    
    def smoo(self,v):
        """ fonction qui permet de lisser une matrice par des moyennes mobiles
        """
        [l,c] = shape(v)
        v1 = concatenate([v[:1,:],(v[:-2,:]+v[1:-1,:]+v[2:,:])/3,v[l-1:l,:]],axis=0)
        v2 = concatenate([v1[:,:1],(v1[:,:-2]+v[:,1:-1]+v1[:,2:])/3,v1[:,c-1:c]],axis=1)
        return v2
    
        
    def calcTime(self,xp1,yp1,tp1,cu1,Cinf,t):
        """starting from concentraitons at an infinite time, calculate conc for a given time
        inj : liste [periodes,conc], k cinet 1o, rf retard
        tf temps de la simulation
        """
        putmask(tp1,tp1<=0,1)
        vmoy=cu1/tp1;putmask(vmoy,vmoy<=0,1)
        t2=t+self.aL/200*(1-exp(-3*t));  #a correciton factor 
        a = sqrt(4*self.aL*vmoy*t);
        c1 = erfc((cu1-vmoy*t2)/a)
        c2 = exp(minimum(cu1/self.aL,500))*erfc((cu1+vmoy*t2)/a)
        c3 = (c1+c2)*Cinf/2.;
        return c3
    
    def calcConc(self,xp0,yp0,tp0,cua,cub):
        """ on part des positions des particules limitant les tubes de flux et on calcule
        la concentration le long de chauqe tube pour un temps infini. On va produire de nouvelles
        positions (XP1, YP1) qui sont en fait le centre des cellules irregulieres cree
        par CalculP. en chaque point on aura une concentration
        """
        #calcul du rapport entre cu2 (chemin reel) et cu (chemin sans disp lat)
    #if 3>2:
        [nt,np]=shape(cua);r=cub[-1,:]/cua[-1,:]; 
        x0,x1,y0,y1 = self.domain
        dx,nx = self.dx,self.ncol
        dy,ny = self.dy,self.nrow
        poro = 0.25
        epais = 10
        dc0=min(dx,dy); #sqrt(dx**2.+dy**2.)*1.01
        ntmx=int(max(cua[-1,:]/dc0))+1; # nbre d'intervalle
        dc=cua[-1,:]/ntmx;#dc=clip(dc,dc0*.98,dc0*1.02)
        tet0=[0.];ind=array((ntmx,nt,np));
        [xp1,yp1,tp1,cu1,cu2]=rflowC.ptsLigne(ind,tet0,dc,xp0,yp0,tp0,cua,cub)
        # on va chercher la largeur d'interbandes avec cercles inscrits dans les segments
        # calcul du point d'intersection x0 des segments
        xp1=array(xp1);yp1=array(yp1);tp1=array(tp1);cu1=array(cu1); ## pb de compatiblite ancien et new Array??
        a1=yp1[1:,:]*xp1[:-1,:]-yp1[:-1,:]*xp1[1:,:]
        xa1=xp1[1:,:]-xp1[:-1,:];ya1=yp1[1:,:]-yp1[:-1,:];putmask(xa1,xa1==0,1)
        b1=xa1[:,1:]*a1[:,:-1]-xa1[:,:-1]*a1[:,1:]
        b2=xa1[:,:-1]*ya1[:,1:]-xa1[:,1:]*ya1[:,:-1];putmask(b2,b2==0,1)
        x0=-b1/b2
        y0=(yp1[1:,1:]*(x0-xp1[:-1,1:])-yp1[:-1,1:]*(x0-xp1[1:,1:]))/xa1[:,1:]
         # distances entre pts et x0 et calcul des points finaux
        d1=sqrt((xp1[:-1,:-1]-x0)**2+(yp1[:-1,:-1]-y0)**2)
        d2=sqrt((xp1[1:,:-1] -x0)**2+(yp1[1:,:-1] -y0)**2)
        d3=sqrt((xp1[:-1,1:] -x0)**2+(yp1[:-1,1:] -y0)**2)
        d4=sqrt((xp1[1:,1:]  -x0)**2+(yp1[1:,1:]  -y0)**2)
        dmx=maximum(d1,d3);dmn=minimum(d2,d4);d=dmn/2+dmx/2
        xc1=x0+(xp1[:-1,:-1]-x0)*d/d1;yc1=y0+(yp1[:-1,:-1]-y0)*d/d1
        xc2=x0+(xp1[:-1,1:] -x0)*d/d3;yc2=y0+(yp1[:-1,1:] -y0)*d/d3
        # xp2, tp2 calcules au point centre de la bande size:np-1,nt-1
        xp2=xc1/2+xc2/2;d1b=d2-d1
        yp2=yc1/2+yc2/2;d3b=d4-d3
        putmask(xp2,xp2==0,1);putmask(d1b,d1b==0,1);putmask(d3b,d3b==0,1)
        a1=(d-d1)/d1b;a3=(d-d3)/d3b
        tp2=tp1[:-1,:-1]*(1-a1)+ tp1[1:,:-1]*a1+ tp1[:-1,1:]*(1-a3)+ tp1[1:,1:]*a3;tp2=tp2/2
        cu3=cu1[:-1,:-1]*(1-a1)+ cu1[1:,:-1]*a1+ cu1[:-1,1:]*(1-a3)+ cu1[1:,1:]*a3;cu3=cu3/2
        a=arange(np);a1=compress(a!=round(np/2),a)
        a2=take(tp1[1:,:],a1,axis=1);putmask(tp2,a2==0,0);putmask(cu3,a2==0,0)
        # largeur de la bande
        dyp=sqrt((xc1-xc2)**2+(yc1-yc2)**2)
        # calcul vloc
        [l,c]=shape(xp2);a2=a2[1:,:]
        tp3=tp2[1:l,:]-tp2[:l-1,:];putmask(tp3,tp3<=0,1.)
        vloc=(cu3[1:l,:]-cu3[:l-1,:])/tp3
        vloc=concatenate([vloc,vloc[l-2:l,:]],axis=0);#vloc=vloc/vloc[1,:];
        Fo=sqrt((xp0[0,:-1]-xp0[0,1:])**2+(yp0[0,:-1]-yp0[0,1:])**2)
        angl1=arctan((yp0[0,np/2+1]-yp0[0,np/2])/(xp0[0,np/2+1]-xp0[0,np/2]))
        angl2=arctan((yp0[1,np/2]-yp0[0,np/2])/(xp0[1,np/2]-xp0[0,np/2]))
        Fo=Fo*vloc[1,:] *sin(abs(angl1-angl2));
        # CY global
        F=Fo*(dyp*0.+1.);Cy=F/dyp/vloc
        #putmask(Cy,(vloc<=0.)|(dyp==0.)|(Cy<0.),0.)#|(indx2[1:,:]==0)|(Cy>1.)
        #print xp1[-1,:],yp1[-1,:],tp1[:,-1],cu1[-1,:],cu2[-1,:],vloc[-1,:],dyp[-1,:],Cy[-1,:];
        # technique brutale
        for i in range(5,ntmx-1):
            Cy[i,:]=minimum(Cy[i,:],Cy[i-1,:])
        Cy=concatenate((ones((1,np-1)),Cy),axis=0);Cy=clip(Cy,0.,1.)
        vloc=concatenate((vloc[:1,:],vloc),axis=0)
        dyp=concatenate((dyp[:1,:],dyp),axis=0)
        #print 'vdyp',vloc[:,np/2-3:np/2+3],Cy[:,np/2-3:np/2+3]
        return [xp1,yp1,tp1,cu1,cu2,vloc,dyp,self.smoo(Cy)]
