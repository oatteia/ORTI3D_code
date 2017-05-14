# -*- coding: utf-8 -*-
"""
Created on Sun Oct 19 10:01:50 2014

@author: olive
""" 
grpList=['glo','spat','time','out','flow','inif','bcf','conf']
groups={
'glo':['glo.1'],
'spat':['spat.1','spat.2','spat.3'],
'time':['time.1'],
'out':['out.1'], #,'out.2','out.3'],
'flow':['flow.1','flow.2','flow.3','flow.4','flow.5'],
'inif':['inif.1'],
'bcf':['bcf.1','bcf.2','bcf.3'],
'conf':['conf.'+str(x) for x in range(1,8)]
}
longNames={'glo':'global control parameters',
           'spat':'spatial discretization',
           'time':'time step control - global system',
           'out': 'output control',
           'flow':'physical parameters - variably saturated flow',
           'inif':'initial condition - variably saturated flow',
           'bcf':'boundary conditions - variably saturated flow', 
           'conf':'control parameters - variably saturated flow',
}
lines={
#'global control parameters' 
'glo.1':{'comm':'Global','cond':'',
         'kw':['varsat_flow','steady_flow','fully_saturated','reactive_transport'],
        'detail':[['Flow','true','false'],['Steady flow','true','false'],['Saturated Flow','true','false'],['Reactions','true','false']],
        'type':['choice','choice','choice','choice']},
#'spatial discretization' 
'spat.1':{'comm':'x discretization','cond':'','kw':['NINTX','NX','Xmin','Xmax'],
                'detail':['nb of intervals','nb of cells','X minimum','X maximum'],
                'type':['int','int','float','float'],'default':[1,10,0.,1.],'units':['L']},
'spat.2':{'comm':'y discretization','cond':'','kw':['NINTY','NY','Ymin','Ymax'],
                'detail':['nb of intervals','nb of cells','Y minimum','Y maximum'],
                'type':['int','int','float','float'],'default':[1,1,0.,1.],'units':['L']},
'spat.3':{'comm':'z discretization','cond':'','kw':['NINTZ','NZ','Zmin','Zmax'],
                'detail':['nb of intervals','nb of cells','Z minimum','Z maximum'],
                'type':['int','int','float','float'],'default':[1,1,0.,1.],'units':['L']},
#'time step control' 
'time.1':{'comm':'time control','cond':'','kw':['Tunit','Tstart','Tfinal','Tmaxstep','Tminstep'],
          'detail':[['time unit','years','days','hours','minutes'],
                'time at start','final time','max time step','min time step'],
          'type':['choice','float','float','float','float'],
          'default':[0,0.,10.,.1,1e-4]},
#'output control
'out.1':{'comm':'output of spatial data','cond':'','kw':['Outs'],
          'detail':[],'type':['string'],'default':['']},
#'physical parameters – variably saturated flow'  
'flow.1':{'comm':'hydraulic conductivity in x-direction','cond':'','kw':['Kxx'],
          'detail':['Kx (m.s-1)'],'type':['arrfloat'],'default':[1e-4]},
'flow.2':{'comm':'hydraulic conductivity in y-direction','cond':'','kw':['Kyy'],
          'detail':['Ky (m.s-1)'],'type':['arrfloat'],'default':[1e-4]},
'flow.3':{'comm':'hydraulic conductivity in z-direction','cond':'','kw':['Kzz'],
          'detail':['Kz (m.s-1)'],'type':['arrfloat'],'default':[1e-4]},
'flow.4':{'comm':'specific storage coefficient','cond':'','kw':['Ss'],
          'detail':[],'type':['float'],'default':[1e-6]},
'flow.5':{'comm':'soil hydraulic function parameters','cond':'fully_saturated!=0',
          'kw':['Swr','a_vg','n_vg','l_vg','Pe'],
          'detail':['Residual saturation','alpha VG','n coeff VG','l coeff (k)','entry pressure'],
          'type':['float','float','float','float','float'],'default':[.1,25.,3.,.5,0.]},
#'initial condition – variably saturated flow' 
'inif.1':{'comm':'initial condition','cond':'','kw':['Hinit'],
          'detail':[],'type':['arrfloat'],'default':[10.]},
#'boundary condition – variably saturated flow' 
'bcf.1':{'comm':'first(BC head)','cond':'','kw':['BChead'],
          'detail':[],'type':['arrfloat'],'default':[10.]},
'bcf.2':{'comm':'second(BC flux)','cond':'','kw':['BCflux'],
          'detail':[],'type':['arrfloat'],'default':[0.]},
'bcf.3':{'comm':'third(seepage)','cond':'','kw':['BCseep'],
          'detail':[],'type':['arrfloat'],'default':[0.]},
#'control parameters – variably saturated flow' #optional
'conf.1':{'comm':'mass balance','cond':'','kw':['conf1'],
          'detail':[],'type':['string'],'default':['']},
'conf.2':{'comm':'input units for initial and boundary conditions','cond':'',
          'kw':['conf2'],'detail':[['type','hydraulic head','pressure head']],
        'type':['choice'],'default':[0]},
'conf.3':{'comm':'centered weighting','cond':'','kw':['conf3'],
          'detail':[],'type':['string'],'default':['']},
'conf.4':{'comm':'compute underrelaxation factor','cond':'','kw':['conf4'],
          'detail':['maximum update'],'type':['float'],'default':[10.]},
'conf.5':{'comm':'newton iteration settings','cond':'',
          'kw':['conf5a','conf5b','conf5c','conf5d'],
          'detail':['num increment','max nb of iteration','converg tolerance',
                    'saturation change'],
        'type':['float','int','float','float'],
        'default':[1e-4,15,1e-6,0.1]},
'conf.6':{'comm':'solver settings','cond':'',
          'kw':['conf6a','conf6b','conf6c','conf6d','conf6e'],
          'detail':['fact level','nb of iteration','info level',
                'residual tolerance','update tolerance'],
        'type':['int','int','float','float','float'],
        'default':[0,100,1,1e-7,1e-7]},
'conf.7':{'comm':'natural ordering','cond':'','kw':['conf7'],
          'detail':[],'type':['string'],'default':['']},
}
 
