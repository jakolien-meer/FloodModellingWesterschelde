from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'index.html';s=p.read_text(encoding='utf-8-sig')
if 'id="availability-open"'not in s:s=s.replace('<div id="scenario-status" role="status" class="scenario-status">Projectresultaten laden…</div>','<div id="scenario-status" role="status" class="scenario-status">Projectresultaten laden…</div><button id="availability-open" class="availability-link">Beschikbaarheid & ontbrekende scenario’s ↗</button>')
s=s.replace('Maximum over de simulatie','Maximum beschikbare uitvoer').replace('Export projectdata: 27 oktober 2026.','Export projectdata: 28 oktober 2026.')
dialog='''<dialog id="availability"><button id="availability-close" aria-label="Sluit beschikbaarheid">×</button><div class="eyebrow">PROJECTDEKKING</div><h2>Beschikbaarheid per scenario</h2><p id="availability-summary"></p><p>Wisselpoldervarianten zijn alleen selecteerbaar waar een berekend resultaat beschikbaar is. Een ontbrekend resultaat is geen nulwaarde.</p><p><a href="https://github.com/jakolien-meer/FloodModellingWesterschelde/blob/main/BESCHIKBAARHEID.md" target="_blank" rel="noopener">Volledig overzicht, inclusief ontbrekende SSM-gevolgen ↗</a></p><div class="availability-table"><table><thead><tr><th>DR–DP</th><th>ZSS</th><th>Inrichting</th><th>Status</th></tr></thead><tbody id="availability-rows"></tbody></table></div></dialog>'''
if 'id="availability"'not in s:s=s.replace('<script src="vendor/maplibre-gl.js">',dialog+'\n<script src="vendor/maplibre-gl.js">')
p.write_text(s,encoding='utf-8')
p=ROOT/'style.css';s=p.read_text(encoding='utf-8-sig')
css='''.availability-link{font-size:12px;color:#1f6f5f;background:transparent;border:0;text-align:left;padding:12px 0 0;line-height:1.5}.availability-link:hover{text-decoration:underline}.metric:disabled{opacity:.48;cursor:not-allowed}.metric:disabled:hover{background:transparent}#availability-close{position:absolute;right:12px;top:12px;border:0;background:transparent;font-size:26px;color:#62767b}.availability-table{overflow:auto;max-height:45vh}table{border-collapse:collapse;width:100%;font-size:12px}th{text-align:left;position:sticky;top:0;background:#fafbf9}td,th{padding:10px 8px;border-bottom:1px solid #dce3e1}td:nth-child(2){white-space:nowrap}#availability h2{margin-right:20px}'''
if '.availability-link{'not in s:s+='\n'+css+'\n'
p.write_text(s,encoding='utf-8')
