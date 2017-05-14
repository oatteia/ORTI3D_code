# -*- coding: utf-8 -*-
"""
Created on Sun Oct 19 10:01:50 2014

@author: olive
""" 
grpList=['poro','trans','trac','init','bct','cont']
groups={
'poro':['poro.1'],
'trans':['trans.1','trans.2','trans.3','trans.4'],
'trac':['trac.1','trac.2','trac.3'],
'init':['init.1'],
'bct':['bct.1','bct.2','bct.3','bct.4'],
'cont':['cont.'+str(x) for x in range(1,12)]
}
longNames={'poro':'physical parameters - porous medium',
           'trans':'physical parameters - reactive transport',
           'trac':'geochemical system',
           'init':'initial condition - reactive transport',
           'bct':'boundary conditions - reactive transport', 
           'cont':'control parameters - reactive transport',
}
lines={
#'physical parameters – porous medium'  
'poro.1':{'comm':'porosity','cond':'','kw':['Poro'],'detail':[],'type':['arrfloat'],'default':[0.25]},
#'physical parameters – reactive transport'  
'trans.1':{'comm':'diffusion coefficients','cond':'','kw':['Diff_w','Diff_a','Diff_choice'],
          'detail':['Diff in water (m2/s)','Diff in air (m2/s)',['Diffusion type','Original','Binary','Dusty gas']],
           'type':['float','float','choice'],
           'default':[1e-10,1e-5,0]},
'trans.2':{'comm':'longitudinal dispersivity','cond':'','kw':['DspL'],
          'detail':[],'type':['float'],'default':[1.]},
'trans.3':{'comm':'transverse horizontal dispersivity','cond':'','kw':['DspT'],
          'detail':[],'type':['float'],'default':[.1]},
'trans.4':{'comm':'transverse vertical dispersivity','cond':'','kw':['DspTV'],
          'detail':[],'type':['float'],'default':[.1]},
#tracer geochemistry
'trac.1':{'comm':'use new database format','cond':'','kw':['Trac1'],
          'detail':[],'type':['string'],'default':['\n']},
'trac.2':{'comm':'database directory','cond':'','kw':['Trac2'],
          'detail':[],'type':['string'],'default':['\'\'']},
'trac.3':{'comm':'components','cond':'','kw':['Trac3'],
          'detail':[],'type':['string'],'default':['1 \n\'tracer\'']},
#'initial condition – reactive transport' 
'init.1':{'comm':'concentration input','cond':'','kw':['Cinit'],
          'detail':[],'type':['arrfloat'],'default':[1e-9],
        'suffx': '\'free\''},
#'boundary condition – reactive transport' 
'bct.1':{'comm':'first(BC fixed)','cond':'','kw':['BCfix'],
          'detail':[],'type':['arrfloat'],'default':[0.],
        'prefx':'\'concentration input\'\n','suffx': '\'free\''},
'bct.2':{'comm':'second(free exit)','cond':'','kw':['BCfree'],
          'detail':[],'type':['arrfloat'],'default':[0.],
        'prefx':'\'concentration input\'\n','suffx': '\'free\''},
'bct.3':{'comm':'third(mass flux)','cond':'','kw':['BCmass'],
          'detail':[],'type':['arrfloat'],'default':[0.],
        'prefx':'\'concentration input\'\n','suffx': '\'free\''},
'bct.4':{'comm':'mixed(gas...)','cond':'','kw':['BCmix'],
          'detail':[],'type':['arrfloat'],'default':[0.],
        'prefx':'\'concentration input\'\n','suffx': '\'free\''},
#control parameters reactive transport
'cont.1':{'comm':'mass balance','cond':'','kw':['cont1'],
          'detail':[],'type':['string'],'default':['']},
'cont.2':{'comm':'spatial weighting','cond':'','kw':['cont2'],
          'detail':[['type','upstream','centered','van leer']],
        'type':['choice'],'default':[0]},
'cont.3':{'comm':'activity update settings','cond':'','kw':['cont3'],
          'detail':[['type','no update','time lagged','double update']],
        'type':['choice'],'default':[0]},
'cont.4':{'comm':'tortuosity correction','cond':'','kw':['cont4'],
          'detail':[['type','millington','no correction']],
        'type':['choice'],'default':[0]},
'cont.5':{'comm':'degassing','cond':'','kw':['cont5'],
          'detail':['degassing rate'],'type':['float'],'default':[0.]},
'cont.6':{'comm':'update porosity','cond':'','kw':['cont6'],
          'detail':[],'type':['string'],'default':['']},
'cont.7':{'comm':'update permeability','cond':'','kw':['cont7'],
          'detail':[],'type':['string'],'default':['']},
'cont.8':{'comm':'user-specified underrelaxation factor','cond':'','kw':['cont8'],
          'detail':['factor'],'type':['float'],'default':[1.]},
'cont.9':{'comm':'newton iteration settings','cond':'',
          'kw':['cont9a','cont9b','cont9c','cont9d','cont9e','cont9f'],
          'detail':['num increment','nb of iteration','max nb of iteration',
                'conc updates','max conc updates','conc tolerance'],
        'type':['float','int','int','float','float','float'],
        'default':[1e-4,12,15,0.5,1.,1e-6]},
'cont.10':{'comm':'solver settings','cond':'',
          'kw':['cont10a','cont10b','cont10c','cont10d','cont10e'],
          'detail':['fact level','nb of iteration','info level',
                'residual tolerance','update tolerance'],
        'type':['float','int','int','float','float','float'],
        'default':[0,100,1,1e-7,1e-7]},
'cont.11':{'comm':'natural ordering','cond':'','kw':['cont11'],
          'detail':[],'type':['string'],'default':['']},
}
