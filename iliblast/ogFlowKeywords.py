# -*- coding: utf-8 -*-
"""
Created on Wed Aug 27 10:54:19 2014

@author: olive
"""
grpList=['DOMN','FLOW'] #,'DENS','UNSAT','XIPHASE']
groups={
'DOMN':['domn.'+str(a) for a in range(1,8)],
'FLOW':['flow.'+str(a) for a in range(1,9)],
}
lines={
'domn.1': {'comm':'dimensions','cond':'','kw':['O_GRID','NLAY','NCOL','NROW','EPS'],
        'detail':[['type of grid','rectangular','triangle'],
                  'nb of layers','nb of columns','nb of rows','epsilon distance'],
        'type':['choice','int','int','int','float']},
'domn.2':{'comm':'Col width','cond':'','kw':['DELR(NCOL)'],'detail':['Col width'],
                'type':['vecfloat'],'default':[10],'units':['L']},
'domn.3':{'comm':'Row height','cond':'','kw':['DELC(NROW)'],'detail':['Row height'],
                'type':['vecfloat'],'default':[10],'units':['L']},
'domn.4': {'comm':'mesh','cond':'','kw':['O_MESH'],
        'detail':[''],
        'type':['arrfloat']},
'domn.5': {'comm':'top','cond':'','kw':['O_TOP'],
        'detail':[''],'type':['arrfloat'],'default':[10.],'units':['L']},
'domn.6': {'comm':'bottom','cond':'','kw':['O_BOTM'],
        'detail':[''],'type':['arrfloat'],'default':[0.],'units':['L']},
'domn.7': {'comm':'units','cond':'','kw':['TUNIT','LUNIT','MUNIT'],
        'detail':[['time units','-','years','days','hours','seconds'],['Length unit','-','M','ft'],['Mass unit','-','kg','lb']],
        'type':['choice','choice','choice'],'default':[2,1,1]},
#flow
'flow.1': {'comm':'initial head','cond':'','kw':['O_HINIT'],
        'detail':[''],'type':['arrfloat']},
'flow.2': {'comm':'fixed head (1st)','cond':'','kw':['O_HFIXED'],
        'detail':[''],'type':['arrfloat']},
'flow.3': {'comm':'water flux (2nd)','cond':'','kw':['O_HFLUX'],
        'detail':[''],'type':['arrfloat']},
'flow.4': {'comm':'head gradient (3rd)','cond':'','kw':['O_HGRAD'],
        'detail':[''],'type':['arrfloat']},
'flow.5': {'comm':'Medium number','cond':'','kw':['O_MEDN'],
        'detail':[''],'type':['arrint'],'default':[0]},
'flow.6': {'comm':'Ratio Horiz Vertic K','cond':'','kw':['O_KHKV'],
        'detail':[''],'type':['float'],'default':[1.]},
'flow.7': {'comm':'Flux (wells)','cond':'','kw':['O_WELL'],
        'detail':[''],'type':['arrfloat']},
'flow.8': {'comm':'Recharge','cond':'','kw':['O_RECH'],
        'detail':[''],'type':['arrfloat']},
}
