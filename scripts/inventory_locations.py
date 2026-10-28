"""Inventory all Westerschelde locations; use only 29_clean for DR29 results."""
from pathlib import Path
import sys,re,json,hashlib
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent
sys.path.insert(0,str(BASE/'outputs/atlas_run_packages'))
from netCDF4 import Dataset
import numpy as np
from pyproj import Transformer
OUT=BASE/'outputs/atlas_expansion_20261028';OUT.mkdir(exist_ok=True)
pattern=re.compile(r'^(29|30|31|32)_(?:WSNoo|Wszui)-DP(\d+)(?:_(Pionier|Volwassen))?_(\d+)(.*)$',re.I)
products={0:'Productie_v20',1:'Productie_v20_1mZSS',2:'Productie_v20_2mZSS'}
locations={};candidates={};transform=Transformer.from_crs(28992,4326,always_xy=True)
for rootname in ['29','29_clean','30','31','32','Wisselpolders']:
 for z,product in products.items():
  for directory in (BASE/rootname).glob(product+'*'):
   if not directory.is_dir():continue
   if directory.name not in [product,product+'_rerun_10d']:continue
   if any(s in directory.name.lower() for s in ['diagnos','test','backup']):continue
   for model in directory.iterdir():
    if not model.is_dir() or not (m:=pattern.match(model.name)):continue
    dr,dp=int(m[1]),int(m[2]);variant=(m[3]or'Huidig').capitalize();suffix=m[5].lower()
    if any(s in suffix for s in ['diagnos','test','backup','restart']):
     # This completed standard-kernel control is the verified deduplicated base.
     if not(dr==29 and dp==760 and z==2 and suffix=='_test_unieke_1d2d_links_10d'):continue
    key=f'{dr}-{dp}';loc=locations.setdefault(key,dict(id=key,dr=dr,dp=dp,has_wisselpolder=False,coordinates=None,return_periods=[]))
    if variant!='Huidig':loc['has_wisselpolder']=True
    if int(m[4])not in loc['return_periods']:loc['return_periods'].append(int(m[4]))
    structure=model/'dflowfm/structures.ini'
    if loc['coordinates'] is None and structure.exists():
     text=structure.read_text(errors='replace')
     dams=[b for b in re.split(r'(?im)^\s*\[Structure\]',text) if re.search(r'(?im)^\s*type\s*=\s*dambreak\s*$',b)]
     if dams:
      b=dams[0];coords=[]
      for axis in ['X','Y']:
       a=re.search(r'(?im)^\s*StartLocation'+axis+r'\s*=\s*([-+\d.eE]+)',b)
       coords.append(float(a[1]) if a else None)
      if all(v is not None for v in coords):loc['coordinates']=list(transform.transform(*coords))
    if dr==29 and rootname!='29_clean':continue
    if dr!=29 and rootname not in [str(dr),'Wisselpolders']:continue
    row=dict(dr=dr,dp=dp,zss=z,variant=variant,model=str(model),return_period=int(m[4]),directory=directory.name)
    output=model/'dflowfm/output';mp=output/'FlowFM_map.nc';fp=output/'FlowFM_fou.nc';cp=output/'FlowFM_clm.nc'
    dia=output/'FlowFM.dia';log=dia.read_text(errors='replace') if dia.exists() else ''
    row['fatal']=bool(re.search(r'\*\*\s*(?:FATAL|ERROR)\s*:',log));row['finished']='Computation finished' in log
    row['end_seconds']=None;row['has_fou']=fp.exists();row['has_clm']=cp.exists()
    if mp.exists():
     try:
      with Dataset(mp) as ds:
       if 'time'in ds.variables and len(ds['time']):row['end_seconds']=float(ds['time'][-1])
     except Exception as e:row['read_error']=type(e).__name__
    row['complete']=bool(row['finished'] and not row['fatal'] and (row['end_seconds']or 0)>=864000)
    row['mtime']=mp.stat().st_mtime if mp.exists() else model.stat().st_mtime
    row['preferred']=('_atlas_20261027'in suffix or '_clean_unieke_links_10d_20261027'in suffix or suffix=='_test_unieke_1d2d_links_10d')
    row['rank']=(int(row['preferred'])*100+int(row['complete'])*10+int('_10d_piekinit'in suffix)*3+int('rerun_10d'in directory.name)*2)
    candidates.setdefault((dr,dp,z,variant),[]).append(row)
# Presence of a polygon also establishes a planned wisselpolder even if no run exists.
for p in (BASE/'ModelgeneratieScript').glob('wisselpolder_*_DP*.shp'):
 if m:=re.match(r'wisselpolder_(29|30|31|32)_DP(\d+)\.shp',p.name):
  dr,dp=map(int,m.groups());key=f'{dr}-{dp}'
  if key in locations:locations[key]['has_wisselpolder']=True
selected=[];missing=[]
for key,loc in sorted(locations.items(),key=lambda kv:(not kv[1]['has_wisselpolder'],kv[1]['dr'],kv[1]['dp'])):
 loc['label']=f"{'Walcheren' if loc['dr']==29 else 'Dijkring '+str(loc['dr'])} · DP{loc['dp']}"
 for z in range(3):
  for variant in (['Huidig','Pionier','Volwassen'] if loc['has_wisselpolder'] else ['Huidig']):
   options=candidates.get((loc['dr'],loc['dp'],z,variant),[])
   best=max(options,key=lambda r:(r['rank'],r['mtime'])) if options else None
   if best:selected.append(best)
   if not best or not best['complete']:
    missing.append(dict(location=key,zss=z,variant=variant,status='loopt of nog niet afgerond' if best and best.get('end_seconds')is not None and not best['fatal'] else 'model ontbreekt' if not best else 'geen volledige dag-10-uitvoer',model=best['model'] if best else None))
report=dict(locations=list(locations.values()),selected=selected,missing=missing,source_rule='DR29 uitsluitend 29_clean; overige dijkringen eigen productiemappen en Wisselpolders. Voorkeur geverifieerde nieuwe runs, piekinit en 10d-reruns.')
(OUT/'inventory.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(dict(locations=len(locations),with_wisselpolder=sum(l['has_wisselpolder']for l in locations.values()),selected=len(selected),complete=sum(s['complete']for s in selected),missing=len(missing),by_dr={dr:sum(l['dr']==dr for l in locations.values())for dr in [29,30,31,32]}),indent=2))
for l in sorted(locations.values(),key=lambda x:(x['dr'],x['dp'])):print(l['id'],'wisselpolder' if l['has_wisselpolder']else'huidig',sum(s['complete']and s['dr']==l['dr']and s['dp']==l['dp']for s in selected))
