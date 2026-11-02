"""Read original and continuation output as one checked, ordered time series."""
from pathlib import Path
import json
import numpy as np
from netCDF4 import Dataset

def output_parts(model):
 model=Path(model);parts=[];p=model/'CONTINUATION_PROVENANCE.json'
 if p.exists():
  meta=json.loads(p.read_text(encoding='utf8'))
  if meta.get('mode')=='RESTART':
   parent=Path(meta['earlier_output']).parent.parent
   assert parent.resolve()!=model.resolve()
   parts+=output_parts(parent)
 parts.append(model/'dflowfm/output')
 return list(dict.fromkeys(parts))

def samples(parts,filename):
 mapping={};coords=None
 for part in parts:
  with Dataset(part/filename) as ds:
   times=np.asarray(ds['time'][:],dtype=float)
   assert np.all(np.diff(times)>0)
   if filename=='FlowFM_map.nc':
    xy=np.column_stack([ds['Mesh2d_face_x'][:],ds['Mesh2d_face_y'][:]])
    if coords is not None:assert np.array_equal(coords,xy),'Restart grid mismatch'
    coords=xy
    # The checkpoint must reconstruct the original state at the overlap.
    if times[0] in mapping:
     old,index=mapping[times[0]]
     with Dataset(old) as original:
      assert np.allclose(original['Mesh2d_waterdepth'][index,:],ds['Mesh2d_waterdepth'][0,:],atol=1e-5,rtol=1e-6,equal_nan=True),'Restart state discontinuity'
   for i,t in enumerate(times):
    if 0<=t<=864000.01:mapping[float(t)]=(part/filename,i)
 assert 0.0 in mapping and 864000.0 in mapping,'Incomplete full ten-day time coverage'
 return sorted(mapping.items())

def maximum(parts,variable):
 mapping=samples(parts,'FlowFM_map.nc');out=None
 for path in dict.fromkeys(v[0] for t,v in mapping):
  with Dataset(path) as ds:
   for t,(p,i) in mapping:
    if p!=path or t<=0:continue
    a=np.asarray(np.ma.filled(ds[variable][i,:],np.nan),dtype=float)
    out=a if out is None else np.fmax(out,a)
 assert out is not None
 return out

def continuous_clm(parts,target):
 if len(parts)==1:return parts[0]/'FlowFM_clm.nc'
 mapping=samples(parts,'FlowFM_clm.nc');times=np.array([t for t,_ in mapping]);assert np.allclose(np.diff(times),600)
 # Only the class field and its classification metadata are needed by temporal().
 with Dataset(mapping[0][1][0]) as src,Dataset(target,'w') as dst:
  var=src['Mesh2d_waterdepth'];bounds=var.flag_bounds
  for part in parts[1:]:
   with Dataset(part/'FlowFM_clm.nc') as continuation:
    other=continuation['Mesh2d_waterdepth']
    assert np.array_equal(var.flag_values,other.flag_values),'Restart depth classes changed'
    assert np.array_equal(src[bounds][:],continuation[other.flag_bounds][:]),'Restart depth class bounds changed'
    assert src['time'].units==continuation['time'].units,'Restart time reference changed'
  names=['time','Mesh2d_waterdepth',bounds]
  dims={d for name in names for d in src[name].dimensions}
  for dim in dims:dst.createDimension(dim,len(times) if dim=='time' else len(src.dimensions[dim]))
  for name in names:
   v=src[name];kw={'fill_value':v._FillValue} if '_FillValue'in v.ncattrs() else {}
   out=dst.createVariable(name,v.dtype,v.dimensions,zlib=True,complevel=2,**kw)
   out.setncatts({a:v.getncattr(a) for a in v.ncattrs() if a!='_FillValue'})
   if name=='time':out[:]=times
   elif name==bounds:out[:]=v[:]
  for path in dict.fromkeys(v[0] for t,v in mapping):
   selected=[(j,i) for j,(t,(p,i)) in enumerate(mapping) if p==path]
   with Dataset(path) as source:
    for offset in range(0,len(selected),96):
     block=selected[offset:offset+96];dst['Mesh2d_waterdepth'][[j for j,i in block],:]=source['Mesh2d_waterdepth'][[i for j,i in block],:]
 return target
