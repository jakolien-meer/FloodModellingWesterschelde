"""Prepare depth exports and reconcile existing consequences with exact model sources."""
from pathlib import Path
import sys,json,re
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent
sys.path[:0]=[str(BASE/'outputs/atlas_run_packages'),str(BASE)]
import numpy as np
from netCDF4 import Dataset
from export_ssm_10dagen import native_grid,write_grid,arr
OUT=BASE/'outputs/atlas_expansion_20261028';INV=json.loads((OUT/'inventory.json').read_text(encoding='utf-8'))
POST=BASE.parent/'post-processing bestanden'
known=[]
legacy_audit=[]
def scenario_key(name):return name.casefold().replace('_zonder_wisselpolder','').replace('_wisselpolder_pionier','_pionier').replace('_wisselpolder_volwassen','_volwassen')
for inp in (POST/'Invoer SSM').glob('DR*'):
 if (inp/'scenario.json').exists():
  meta=json.loads((inp/'scenario.json').read_text());output=POST/'Output SSM'/inp.name
  if (output/'Totaalschade.tif').exists():known.append((inp,output,meta))
  else:
   # Older SSM GUI runs store results in uitvoer/. Reuse only when all three
   # hazard input rasters numerically match the source-linked canonical inputs.
   for legacy in (POST/'Output SSM').glob('DR*'):
    if scenario_key(legacy.name)!=scenario_key(inp.name)or not(legacy/'uitvoer/Totaalschade.tif').exists():continue
    from osgeo import gdal
    matches=[]
    for key in ['waterdiepte','stroomsnelheid','stijgsnelheid']:
     pa,pb=inp/(key+'.tif'),legacy/'invoer'/(key+'.tif')
     if not pa.exists()or not pb.exists():matches.append(False);continue
     da,db=gdal.Open(str(pa)),gdal.Open(str(pb))
     aa,ab=da.ReadAsArray().astype(float),db.ReadAsArray().astype(float)
     for ds,a in [(da,aa),(db,ab)]:
      nd=ds.GetRasterBand(1).GetNoDataValue()
      if nd is not None:a[a==nd]=np.nan
     matches.append(aa.shape==ab.shape and np.allclose(da.GetGeoTransform(),db.GetGeoTransform())and np.allclose(aa,ab,atol=1e-6,rtol=1e-6,equal_nan=True))
    legacy_audit.append(dict(scenario=inp.name,input_rasters_match=all(matches)))
    if all(matches):known.append((inp,legacy/'uitvoer',meta))
for r in json.loads((BASE/'outputs/DP360_LIR_20261026/manifest.json').read_text()):
 if r.get('returncode')==0:known.append((Path(r['input_directory']),Path(r['output_directory']),r))
def norm(path):
 p=Path(path).resolve();return p.parent if p.name.lower()=='dflowfm' else p
sources=[];failed=[]
order={l['id']:not l['has_wisselpolder']for l in INV['locations']}
for r in sorted(INV['selected'],key=lambda r:(order[f"{r['dr']}-{r['dp']}"],r['dr'],r['dp'],r['zss'],r['variant'])):
 if not r['complete']:continue
 model=Path(r['model']);flow=model/'dflowfm';variant='Zonder_wisselpolder'if r['variant']=='Huidig'else'Wisselpolder_'+r['variant']
 sid=f"DR{r['dr']}_DP{r['dp']}_{r['zss']}mZSS_{variant}"
 matching=[(inp,out,meta)for inp,out,meta in known if meta.get('source_run')and norm(meta['source_run'])==model.resolve()and all(meta.get(k)==r[k]for k in ['dr','dp','zss','variant'])]
 if matching:
  inp,out,meta=matching[-1]
  # Old exports still need the complete four consequence products.
  if all((out/f).exists()for f in ['Totaalschade.tif','Slachtoffers.tif','Slachtoffers_getroffenen.tif','Slachtoffers_mortaliteit.tif']):
   sources.append(dict(id=sid,inp=str(inp),result=str(out),meta=meta,consequences_available=True));continue
 try:
  inp=OUT/'depth_inputs'/sid;inp.mkdir(parents=True,exist_ok=True)
  cached=inp/'scenario.json'
  if cached.exists()and(inp/'waterdiepte.tif').exists():
   meta=json.loads(cached.read_text())
   if meta.get('source_run')==str(model):
    sources.append(dict(id=sid,inp=str(inp),result=None,meta=meta,consequences_available=False));continue
  with Dataset(flow/'output/FlowFM_map.nc')as ds:
   times=arr(ds['time'][:]);assert np.any(np.isclose(times,864000,rtol=0,atol=.01)),'Geen exact dag-10-tijdstip'
   use=np.flatnonzero((times>0)&(times<=864000.01));assert len(use)
   depth=np.full(ds['Mesh2d_waterdepth'].shape[1],np.nan)
   for i in use:depth=np.fmax(depth,arr(ds['Mesh2d_waterdepth'][int(i),:]))
   assert np.all(depth[np.isfinite(depth)]>=0)
   grid=native_grid(ds)
   write_grid(inp,'waterdiepte',depth,grid,'Maximum waterdiepte uit MAP-uitvoer na t=0 tot dag 10','m',dict(source=str(flow/'output/FlowFM_map.nc'),method='maximum_beschikbare_MAP_na_start_tot_dag10'),asc=False)
  meta=dict(scenario=sid,dr=r['dr'],dp=r['dp'],zss=r['zss'],variant=r['variant'],end_day=10,source_run=str(model),depth_speed_method='maximum_beschikbare_MAP_na_start_tot_dag10',return_period=r['return_period'])
  (inp/'scenario.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
  sources.append(dict(id=sid,inp=str(inp),result=None,meta=meta,consequences_available=False))
 except Exception as e:
  failed.append(dict(location=f"{r['dr']}-{r['dp']}",zss=r['zss'],variant=r['variant'],reason=str(e)))
 print('EXPORTED',sid,flush=True)
report=dict(locations=INV['locations'],sources=sources,missing=INV['missing'],export_failures=failed,source_rule=INV['source_rule'],legacy_audit=legacy_audit)
(OUT/'sources.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print('READY',len(sources),'scenarios;',sum(s['consequences_available']for s in sources),'with consequences;',len(failed),'export failures')
