const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..'),catalog=JSON.parse(fs.readFileSync(path.join(root,'data/catalog.json'),'utf8')),availability=JSON.parse(fs.readFileSync(path.join(root,'data/availability.json'),'utf8'));
assert.equal(catalog.locations.length,52);assert.equal(catalog.scenarios.length,210);
assert.equal(new Set(catalog.locations.map(l=>l.id)).size,52);assert.equal(new Set(catalog.scenarios.map(s=>s.id)).size,210);
let seenWithout=false;for(const l of catalog.locations){if(!l.has_wisselpolder)seenWithout=true;else assert(!seenWithout,'Marsh locations must precede non-marsh locations');}
for(const s of catalog.scenarios){const loc=catalog.locations.find(l=>l.id===`${s.dr}-${s.dp}`);assert(loc);if(!loc.has_wisselpolder)assert.equal(s.variant,'Huidig');if(s.dr===29)assert.equal(s.source_group,'29_clean');const data=JSON.parse(fs.readFileSync(path.join(root,'data',s.id+'.json'),'utf8'));assert.equal(data.meta.id,s.id);assert(data.depth_image.url.startsWith('data:image/png;base64,'));for(const values of Object.values(data.values)){for(const key of s.available_metrics){if(values[key]!=null)assert(Number.isFinite(values[key])&&values[key]>=0);}if(!s.available_metrics.includes('damage'))assert.equal(values.damage,undefined);}}
assert.equal(availability.missing_hydraulics.length,54);assert.equal(availability.missing_consequences.length,183);
const inventoryPath=path.resolve(root,'../outputs/atlas_expansion_20261028/inventory.json');
if(fs.existsSync(inventoryPath)){const inv=JSON.parse(fs.readFileSync(inventoryPath,'utf8'));for(const r of inv.selected){const dir=['Productie_v20','Productie_v20_1mZSS','Productie_v20_2mZSS'][r.zss];assert([dir,dir+'_rerun_10d'].includes(r.directory),'ZSS source folder mismatch');}}
assert.equal(fs.readdirSync(path.join(root,'data')).filter(f=>/^DR.*\.json$/.test(f)).length,catalog.scenarios.length);
console.log('PASS: 52 ordered locations, 210 valid scenarios, strict 29_clean provenance, layer availability and missing-scenario reconciliation.');
