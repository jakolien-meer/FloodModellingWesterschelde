"""Export only public-facing aggregated project results; never copy raw model files.
Run with OSGeo4W Python (geopandas, GDAL, numpy). Paths remain local.
"""
from pathlib import Path
import json, re, base64, hashlib
import geopandas as gpd
import numpy as np
from osgeo import gdal, ogr, osr
from pyproj import Transformer

gdal.UseExceptions()
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent
POST=BASE.parent/'post-processing bestanden'
OUT=ROOT/'data'; OUT.mkdir(exist_ok=True)
GPKG=POST/'wijkenbuurten_2024_v1.gpkg'
MUNICIPALITIES=['Borsele','Goes','Hulst','Kapelle','Middelburg (Z.)','Noord-Beveland','Reimerswaal','Schouwen-Duiveland','Sluis','Terneuzen','Tholen','Veere','Vlissingen']
where="gemeentenaam IN ("+','.join("'"+s+"'" for s in MUNICIPALITIES)+")"
frames={}
def save(path,data):
 path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8')
for name in ['gemeenten','wijken','buurten']:
 d=gpd.read_file(GPKG,layer=name,where=where)
 code={'gemeenten':'gemeentecode','wijken':'wijkcode','buurten':'buurtcode'}[name]
 title={'gemeenten':'gemeentenaam','wijken':'wijknaam','buurten':'buurtnaam'}[name]
 keep=list(dict.fromkeys([code,title,'gemeentecode','gemeentenaam','water']+(['wijkcode'] if name=='buurten' else [])))
 d=d[keep+['geometry']].copy().reset_index(drop=True)
 frames[name]=d
 web=d.copy();web.geometry=web.geometry.simplify(12,preserve_topology=True)
 web=web.to_crs(4326)
 save(OUT/(name+'.geojson'),json.loads(web.to_json(drop_id=True)))
 print(name,len(d),flush=True)
buurten=frames['buurten'];land=buurten.water.str.upper()=='NEE'
zones={}
def zonemap(ds):
 key=(ds.RasterXSize,ds.RasterYSize,ds.GetGeoTransform())
 if key not in zones:
  v=ogr.GetDriverByName('Memory').CreateDataSource('zones')
  srs=osr.SpatialReference();srs.ImportFromEPSG(28992)
  layer=v.CreateLayer('zones',srs,ogr.wkbMultiPolygon);layer.CreateField(ogr.FieldDefn('zone',ogr.OFTInteger))
  for i,row in buurten[land].iterrows():
   f=ogr.Feature(layer.GetLayerDefn());f.SetField('zone',int(i+1));f.SetGeometry(ogr.CreateGeometryFromWkb(row.geometry.wkb));layer.CreateFeature(f)
  z=gdal.GetDriverByName('MEM').Create('',ds.RasterXSize,ds.RasterYSize,1,gdal.GDT_Int32)
  z.SetGeoTransform(ds.GetGeoTransform());z.SetProjection(srs.ExportToWkt())
  gdal.RasterizeLayer(z,[1],layer,options=['ATTRIBUTE=zone'])
  zones[key]=z.ReadAsArray()
 return zones[key]
def read(path):
 ds=gdal.Open(str(path));a=ds.ReadAsArray().astype(float);nodata=ds.GetRasterBand(1).GetNoDataValue()
 if nodata is not None:a[a==nodata]=np.nan
 a[a<0]=np.nan
 return ds,a
def overlay(ds,a):
 src=gdal.GetDriverByName('MEM').Create('',ds.RasterXSize,ds.RasterYSize,1,gdal.GDT_Float32)
 src.SetGeoTransform(ds.GetGeoTransform());srs=osr.SpatialReference();srs.ImportFromEPSG(28992);src.SetProjection(srs.ExportToWkt())
 # Export only Zeeland land cells. No visual data outside the province.
 a=a.copy();a[zonemap(ds)==0]=np.nan
 src.GetRasterBand(1).SetNoDataValue(-9999);src.GetRasterBand(1).WriteArray(np.nan_to_num(a,nan=-9999))
 w=gdal.Warp('',src,format='MEM',dstSRS='EPSG:3857',width=1000,resampleAlg='near',dstNodata=-9999)
 vals=w.ReadAsArray();edges=[.1,.5,1,2,3,5]
 colors=np.array([[223,239,246,185],[182,216,232,195],[124,183,211,210],[68,138,180,220],[32,95,145,230],[19,58,104,240],[11,31,67,245]],dtype=np.uint8)
 rgba=colors[np.searchsorted(edges,vals,side='left')];rgba[(vals<=0)|(vals==-9999),3]=0
 image=gdal.GetDriverByName('MEM').Create('',w.RasterXSize,w.RasterYSize,4,gdal.GDT_Byte)
 for j in range(4):image.GetRasterBand(j+1).WriteArray(rgba[:,:,j])
 image.GetRasterBand(4).SetColorInterpretation(gdal.GCI_AlphaBand)
 gdal.GetDriverByName('PNG').CreateCopy('/vsimem/depth.png',image)
 png=bytes(gdal.VSIGetMemFileBuffer_unsafe('/vsimem/depth.png'));gdal.Unlink('/vsimem/depth.png')
 gt=w.GetGeoTransform();t=Transformer.from_crs(3857,4326,always_xy=True)
 west,north=t.transform(gt[0],gt[3]);east,south=t.transform(gt[0]+w.RasterXSize*gt[1],gt[3]+w.RasterYSize*gt[5])
 return {'url':'data:image/png;base64,'+base64.b64encode(png).decode(),'bounds':[[south,west],[north,east]]}

sources={}
for inp in sorted((POST/'Invoer SSM').glob('DR*')):
 output=POST/'Output SSM'/inp.name
 if (inp/'scenario.json').exists() and (output/'Totaalschade.tif').exists():
  sources[inp.name]=(inp,output,json.loads((inp/'scenario.json').read_text()))
for r in json.loads((BASE/'outputs/DP360_LIR_20261026/manifest.json').read_text()):
 if r.get('returncode')==0:sources[r['scenario']]=(Path(r['input_directory']),Path(r['output_directory']),r)
index=[];qa=[]
for sid,(inp,result,meta) in sorted(sources.items()):
 metrics={'depth':inp/'waterdiepte.tif','damage':result/'Totaalschade.tif','fatalities':result/'Slachtoffers.tif','affected':result/'Slachtoffers_getroffenen.tif','mortality':result/'Slachtoffers_mortaliteit.tif'}
 if not all(p.exists() for p in metrics.values()):continue
 data={}; totals={};depth_image=None
 for metric,path in metrics.items():
  ds,a=read(path);zone=zonemap(ds)
  if metric=='mortality':assert np.nanmax(a)<=1
  valid=np.isfinite(a)&(zone>0)
  if metric in ['damage','fatalities','affected']:
   totals[metric]=float(a[valid].sum())
  for i,b in buurten[land].iterrows():
   mask=valid&(zone==i+1)
   if not mask.any():continue
   vals=a[mask]
   row=data.setdefault(b.buurtcode,{})
   if metric=='mortality':
    pos=vals[vals>0];row[metric]=float(np.median(pos)*100) if len(pos) else None
    row['mortality_cells']=int(len(pos))
   elif metric=='depth':row[metric]=float(vals.max());row['wet_ha']=float((vals>0).sum()*.25)
   else:row[metric]=float(vals.sum())
  if metric=='depth':depth_image=overlay(ds,a)
  if metric in totals:
   check=sum(r.get(metric,0) for r in data.values());assert np.isclose(check,totals[metric],rtol=1e-10,atol=1e-5)
  ds=None
 desc=dict(id=sid,dr=meta['dr'],dp=meta['dp'],zss=meta['zss'],variant=meta['variant'],end_day=meta.get('end_day',10),depth_method=meta.get('depth_speed_method','onbekend'),buurten=len(data),totals=totals)
 save(OUT/(sid+'.json'),dict(meta=desc,values=data,depth_image=depth_image))
 index.append(desc);qa.append(dict(scenario=sid,reconciled=True,buurten=len(data)))
 print(sid,len(data),flush=True)
assert len(frames['gemeenten'].gemeentecode.unique())==13
# Reconcile existing DP360 medians independently, retaining full precision.
for r in json.loads((BASE/'outputs/DP360_LIR_20261026/buurtmedianen.json').read_text()):
 p=OUT/(r['scenario']+'.json')
 if p.exists():
  actual=json.loads(p.read_text(encoding='utf-8'))['values'][r['buurtcode']]['mortality']
  assert np.isclose(actual,r['mediane_mortaliteit_pct'],rtol=1e-6)
save(OUT/'catalog.json',dict(scenarios=index,geography_year=2024,export_date='2026-10-27',municipalities=MUNICIPALITIES,quality='Voorlopige scenarioresultaten; geen gewogen trajectrisico. Ontbrekende stijgsnelheden en onvolledig permanentwatermasker.'))
save(ROOT/'scripts/data_qa.json',dict(scenarios=len(index),municipalities=13,checks=qa,dp360_medians_reconciled=True,source_geography_sha256=hashlib.sha256(GPKG.read_bytes()).hexdigest()))
print('VALIDATED',len(index),'scenarios')
