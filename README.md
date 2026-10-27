# Westerschelde · Overstromingsatlas

Publieke, statische GitHub Pages-kaart met **MapLibre GL JS + PMTiles v3**. Alle 13 Zeeuwse gemeenten, wijken en buurten (CBS 2024 v1). Bestaande D-HYDRO / SSM-projectresultaten voor 28 beschikbare bresscenario’s, met +0/+1/+2 m ZSS en huidige/pionier/volwassen inrichting waar beschikbaar.

## Gebruik

Open de atlas, kies breslocatie, zeespiegelstijging en inrichting. Kies waterdiepte, schade, slachtoffers, getroffenen of mortaliteit. Klik een buurt voor alle waarden. Zoek op gebiedsnaam of CBS-code, filter op gemeente en download de geselecteerde buurttabel via Bronnen & methode. Scenarioselectie is deelbaar via de URL.

## GIS-architectuur

- `data/zeeland.pmtiles`: eigen, gzip-gecomprimeerde MVT-vectortegels, zoom 6–12, HTTP Range requests. Alleen Zeeland, geen mondiale basemap. Overzoom tot zoom 16.
- `promoteId: code` en GPU `feature-state` voor buurtchoropleten. Geen vervanging of hercodering van geometrie bij scenariowisseling.
- Per scenario een klein JSON-bestand met buurtwaarden en gegeorefereerde rasterafbeelding van maximale waterdiepte. Rasterweergave gebruikt Web Mercator, nearest neighbour en transparantie buiten de Zeeuwse landbuurten. De rasterafbeelding is een webvisualisatie, geen downloadbaar analyseraster.
- Geen server, API-sleutel, tracking of account nodig. Bibliotheken lokaal meegeleverd: MapLibre GL JS 5.6.2 (BSD-3-Clause), PMTiles JS 4.3.0 (BSD-3-Clause).
- `scripts/build_data.py` en `scripts/build_pmtiles.py`: reproduceerbare verwerking met lokale projectdata, geopandas, GDAL, numpy, pmtiles, mapbox-vector-tile. Originele modellen worden niet gepubliceerd.

## Data en betekenis

Brongeometrie: CBS / Kadaster Wijk- en Buurtkaart 2024 v1, CC BY 4.0. Bron: lokaal project-GPKG. Middelburg heet in deze bron **Middelburg (Z.)**. Waterbuurten uitgesloten bij aggregatie. Berekeningen op oorspronkelijke RD-geometrie; weergave vereenvoudigd met 12 m tolerantie en tegelafhankelijke vereenvoudiging. Celmiddelpunt bepaalt buurt. Alleen buurten met geldige rastercellen krijgen waarden; ontbrekend is nooit stilzwijgend nul.

| Laag | Eenheid | Aggregatie per buurt |
|---|---|---|
| Waterdiepte | m | Maximum van geldige cellen over de beschikbare simulatie-export |
| Schade | euro | Som Totaalschade; prijspeil en objectdatabase 2022, excl. BTW |
| Slachtoffers | personen | Som dodelijke slachtoffers, zonder evacuatie |
| Getroffenen | personen | Som SSM-getroffenen |
| Mortaliteit | % | Mediaan positieve mortaliteitscellen, geen bevolkingsweging |

Mortaliteit is **niet** slachtoffers/getroffenen en **geen** jaarlijkse overlijdenskans. Verwachte aantallen kunnen fracties bevatten. Scenario’s worden niet opgeteld; geen gewogen trajectrisico. FOU-maxima en dagelijkse MAP-maxima zijn verschillende exportmethoden; de exacte methode staat per scenario in `meta.depth_method`. Rastermaxima zijn niet gelijktijdig. De weergegeven gemeenten/wijken zijn context; gevolgen blijven per buurt.

**Voorlopig:** ontbrekende stijgsnelheden en onvolledig permanentwatermasker. Geen resultaat betekent niet automatisch droog/veilig. Niet alle scenario-combinaties beschikbaar. DP360-volwassen 0/2 m ontbrak in de gebruikte gevolgenanalyse. Geen nieuwe hydraulische of SSM-simulaties uitgevoerd voor de atlas. Exportdatum: 27 oktober 2026.

## Controle en hosting

`scripts/data_qa.json` bevat controles op sommen en onafhankelijke reconciliatie van bestaande DP360-buurtmedianen. PMTiles is structureel gecontroleerd en in de browser getest. Voor lokaal gebruik: `node scripts/serve.cjs`, open `http://localhost:8098`. De server ondersteunt HTTP Range voor PMTiles.

GitHub Pages: publiceer de `main`-branch, map `/ (root)`. Alle URLs zijn relatief en werken onder de repository-submap. Er is geen buildstap nodig.

Bronnen: [CBS / PDOK](https://api.pdok.nl/cbs/wijken-en-buurten-2024/ogc/v1?f=html&lang=nl), [PMTiles](https://docs.protomaps.com/pmtiles/maplibre), [MapLibre GL](https://maplibre.org/maplibre-gl-js/docs/).
