"""Build a PMTiles v3 archive with clipped MVT geometry and stable CBS IDs."""
from pathlib import Path
import sys,json,math,gzip
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.build_packages'))
import geopandas as gpd
from shapely.geometry import box, mapping
import mapbox_vector_tile
from pmtiles.writer import write
from pmtiles.tile import zxy_to_tileid,TileType,Compression

DATA=ROOT/'data';R=20037508.342789244
frames={}; search=[]
for layer in ['gemeenten','wijken','buurten']:
 d=gpd.read_file(DATA/(layer+'.geojson'))
 code={'gemeenten':'gemeentecode','wijken':'wijkcode','buurten':'buurtcode'}[layer]
 name={'gemeenten':'gemeentenaam','wijken':'wijknaam','buurten':'buurtnaam'}[layer]
 for _,row in d[d.water=='NEE'].iterrows():
  p=row.geometry.representative_point()
  search.append(dict(code=row[code],name=row[name],municipality=row.gemeentenaam,municipality_code=row.gemeentecode,level=layer,bounds=list(row.geometry.bounds),center=[p.x,p.y],wijkcode=row.get('wijkcode','')))
 d['code']=d[code];d['name']=d[name]
 frames[layer]=d.to_crs(3857)
bounds=frames['gemeenten'].total_bounds
def xy(x,y,z):
 n=2**z
 return max(0,min(n-1,int((x+R)/(2*R)*n))),max(0,min(n-1,int((R-y)/(2*R)*n)))
tiles=[]
for z in range(6,13):
 x0,y1=xy(bounds[0],bounds[1],z);x1,y0=xy(bounds[2],bounds[3],z)
 for x in range(x0,x1+1):
  for y in range(y0,y1+1):tiles.append((zxy_to_tileid(z,x,y),z,x,y))
with write(str(DATA/'zeeland.pmtiles')) as writer:
 count=0
 for tid,z,x,y in sorted(tiles):
  span=2*R/(2**z);b=(-R+x*span,R-(y+1)*span,-R+(x+1)*span,R-y*span);clip=box(*b);layers=[]
  for name,d in frames.items():
   if name=='buurten' and z<8:continue
   if name=='wijken' and z<7:continue
   feats=[]
   for i in d.sindex.query(clip,predicate='intersects'):
    row=d.iloc[i];geom=row.geometry.intersection(clip).simplify(span/4096*.6,preserve_topology=True)
    if geom.is_empty or geom.geom_type not in ['Polygon','MultiPolygon']:continue
    props={k:str(row[k]) for k in ['code','name','gemeentecode','gemeentenaam','water']}
    feats.append(dict(geometry=mapping(geom),properties=props))
   if feats:layers.append(dict(name=name,features=feats))
  if not layers:continue
  mvt=mapbox_vector_tile.encode(layers,default_options={'quantize_bounds':b,'extents':4096})
  writer.write_tile(tid,gzip.compress(mvt,mtime=0));count+=1
 writer.finalize(dict(tile_type=TileType.MVT,tile_compression=Compression.GZIP,min_lon_e7=33000000,min_lat_e7=512000000,max_lon_e7=42500000,max_lat_e7=518000000,center_zoom=9),dict(name='Zeeland · CBS 2024',attribution='CBS en Kadaster · CC BY 4.0',vector_layers=[dict(id=n,fields={'code':'String','name':'String','water':'String'},minzoom=6,maxzoom=12) for n in frames]))
(DATA/'areas.json').write_text(json.dumps(search,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print('PMTiles validated:',count,'tiles;',len(search),'searchable areas;', (DATA/'zeeland.pmtiles').stat().st_size,'bytes')
