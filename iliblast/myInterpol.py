# -*- coding: utf-8 -*-
"""
Created on Thu Jan 26 05:19:46 2017

@author: oatteia
"""

#!/usr/bin/env python
import numpy as np
from numpy.linalg import solve
from scipy.stats import tvar as variance
from scipy.spatial import Delaunay
from geometry import *
from config import *

def invDistance(xpt,ypt,zpt,x,y,power=1.):
    """inverse distance interpolation on x,y points, and reference points
    xpt,wpt,zpt, with a given power"""
    n=len(x);z0=x*0.;#l=len(xpt)
    for i in range(n):
        d=maximum(sqrt((x[i]-xpt)**2.+(y[i]-ypt)**2.),1e-4)
        lb=1./(d**power)
        lb=lb/sum(lb)
        z0[i]=sum(zpt*lb)
    z0 = clip(z0,min(zpt)*0.9,max(zpt)*1.1)
    return z0
    
######################   kriging  ############################ 
def krige(xpt,ypt,zpt,rg,x,y,vtype='spher'):
    """ krige function to interpolate over a vector of points of x,y coords
    using the base points xpt ypt and the vario distance rg (range)"""
    #print 'geom kr l 522',len(xpt),rg
    n = len(x)
    z0=zeros(n)
    vari=0.5*variance(zpt);#print 'vari',vari
    if vtype in ['spher',None]:
        v_func='gam = 3/2.*d/rg-1/2.*(d/rg)**3.;gam[d>rg]=1'
    elif vtype=='gauss':
        v_func='gam=exp(-(d/rg)**2)'
    elif vtype=='gauss3':
        v_func='gam=exp(-(d/rg)**3)'
    for i in range(n):
        x0=x[i];y0=y[i];
        d=sqrt((x0-xpt)**2+(y0-ypt)**2);
        ind=argsort(d)
        x1,y1,z1=xpt[ind[:16]],ypt[ind[:16]],zpt[ind[:16]];# select closest 16 points
        xm1,ym1=meshgrid(x1,y1)
        d=sqrt((xm1-transpose(xm1))**2.+(ym1-transpose(ym1))**2.)
        exec(v_func)
        l1=len(x1)+1
        A=ones((l1,l1)); #starting the matrix
        A[:-1,:-1]=gam*vari
        A[-1,-1]=0.
        d = sqrt((x0-x1)**2.+(y0-y1)**2.)
        exec(v_func)
        B = ones((l1,1))
        B[:-1,0]=gam*vari#print i,j,len(A),len(B)
        lb=solve(A,B)
        z0[i]=sum(z1*transpose(lb[:-1]))
    z0 = clip(z0,min(zpt)*0.9,max(zpt)*1.1)
    return z0

import itertools
from numpy.linalg import lstsq
def polyfit2d(x, y, z, order=3):
    ncols = (order + 1)**2
    G = zeros((x.size, ncols))
    ij = itertools.product(range(order+1), range(order+1))
    for k, (i,j) in enumerate(ij):
        G[:,k] = x**i * y**j
    m, _, _, _ = lstsq(G, z)
    return m

def polyval2d(x, y, m):
    order = int(sqrt(len(m))) - 1
    ij = itertools.product(range(order+1), range(order+1))
    z = zeros_like(x)
    for a, (i,j) in zip(m, ij):
        z += a * x**i * y**j
    return z

###################################  VORONOI ##################""
def getPolyList(listP,xb,yb):
    polylist = []
    #add points on sides
#if 3>2:
    y=arange(yb[0],yb[1],yb[1]/4);x=zeros(4)+xb[0] # left
    x=r_[x,arange(xb[0],xb[1],xb[1]/4)];y=r_[y,zeros(4)+yb[1]] # top
    y=r_[y,arange(yb[1],yb[0],-yb[1]/4)];x=r_[x,zeros(4)+xb[1]] # right
    x=r_[x,arange(xb[1],xb[0],-xb[1]/4)];y=r_[y,zeros(4)+yb[0]] # botm
    listP.extend(zip(x,y))
    delauny = Delaunay(listP)
    segments = voronoi(delauny)
    for i in range(len(listP[:-16])): 
        p = findPoly(delauny,segments,listP,i,xb,yb);#print i,p
        polylist.append(p)
    return polylist
    

def findPoly(delauny,segments,listP,ipt,xb,yb):
    """finds a polygon around a point identified in the vt series (vertices)"""
    vt = delauny.vertices
    ltri = where(sum(vt==ipt,axis=1))[0]
    lseg = [] # will contain arrays (1,4) for each segment : x,y 1st pt and 2nd pt
    for tri in ltri:
        nghb = delauny.neighbors[tri]
        if -1 in nghb: continue
        for i,n in enumerate(nghb):
            if ipt not in vt[n]: continue
            s = segments[tri*3+i]
            seg=r_[s[0],s[1]]
            if any(seg[:,[0,2]]>xb[1]) or any(seg[:,[0,2]]<xb[0]) or any(seg[:,[1,3]]>yb[1]) or any(seg[:,[1,3]]<yb[0]):
                return None
            flag = 0
            for k in range(len(lseg)): 
                if all(sort(lseg[k])==sort(seg)): flag = 1# already here
            if flag == 0: lseg.append(seg)
    #find 1st point
    npt = len(lseg)
    if len(lseg)==0: return None
    poly=[lseg[0][:2],lseg[0][2:]];pt=poly[1];current = 0;nit = 0
    while (len(poly)<npt) and (nit<npt):
        nit += 1;
        for i in range(npt):
            if all(lseg[i][:2]==pt) and i!=current:
                pt=lseg[i][2:];poly.append(pt);current=i;
            if all(lseg[i][2:]==pt) and i!=current:
                pt=lseg[i][:2];poly.append(pt);current=i;
    if len(poly)<3: return None
    poly.append(poly[0])
    return poly

def voronoi(delauny):
    triangles = delauny.points[delauny.vertices]
    circum_centers = np.array([triangle_csc(tri) for tri in triangles])
    segments = []
    for i, triangle in enumerate(triangles):
        circum_center = circum_centers[i]
        for j, neighbor in enumerate(delauny.neighbors[i]):
            if neighbor != -1:
                segments.append((circum_center, circum_centers[neighbor]))
            else:
                ps = triangle[(j+1)%3] - triangle[(j-1)%3]
                ps = np.array((ps[1], -ps[0]))

                middle = (triangle[(j+1)%3] + triangle[(j-1)%3]) * 0.5
                di = middle - triangle[j]

                ps /= np.linalg.norm(ps)
                di /= np.linalg.norm(di)

                if np.dot(di, ps) < 0.0:
                    ps *= -1000.0
                else:
                    ps *= 1000.0
                segments.append((circum_center, circum_center + ps))
    return segments

def triangle_csc(pts):
    rows, cols = pts.shape

    A = np.bmat([[2 * np.dot(pts, pts.T), np.ones((rows, 1))],
                 [np.ones((1, rows)), np.zeros((1, 1))]])

    b = np.hstack((np.sum(pts * pts, axis=1), np.ones((1))))
    x = np.linalg.solve(A,b)
    bary_coords = x[:-1]
    return np.sum(pts * np.tile(bary_coords.reshape((pts.shape[0], 1)), (1, pts.shape[1])), axis=0)
    