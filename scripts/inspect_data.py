from pathlib import Path
import geopandas as gpd
from osgeo import gdal
import json
B=Path(__file__).resolve().parents[2]
p=B.parent/'post-processing bestanden'
for layer in ['gemeenten','wijken']:
 d=gpd.read_file(p/'wijkenbuurten_2024_v1.gpkg',layer=layer,rows=1)
 print(layer,list(d.columns)[:12])
for folder in [p/'Invoer SSM',p/'Output SSM']:
 print(folder.name,len(list(folder.glob('DR*'))))
r=gdal.Open(str(B/'outputs/DP360_LIR_20261026/DR30_DP360_0mZSS_Zonder_wisselpolder/ssm/Slachtoffers.tif'))
print('raster',r.RasterXSize,r.RasterYSize,r.GetGeoTransform(),r.GetProjection()[:60])
