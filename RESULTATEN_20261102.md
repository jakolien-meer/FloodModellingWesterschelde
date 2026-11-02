# Aanvulling atlas - 2 november 2026

De hydraulische catalogus groeit van 210 naar 239 scenario's. Acht aanvullende scenario's bestaan uit een oorspronkelijke run en een vervolg uit een restart. Voor die scenario's worden MAP- en CLM-uitvoer langs de vastgelegde bronketen samengevoegd: tijdstippen worden chronologisch gebruikt, overlap gebruikt de vervolguitvoer, roosters en de waterdieptetoestand op het restarttijdstip moeten overeenkomen. De aaneengesloten CLM-reeks moet alle 600-secondenstappen van t=0 tot dag 10 bevatten. Maxima uit uitsluitend het restartdeel worden niet als tiendaags resultaat gepubliceerd.

Bestaande complete, exact aan de geselecteerde bronrun gekoppelde SSM-sets blijven behouden. Ontbrekende sets worden opnieuw berekend met SSM2023 v4.2, binnendijks, objectdatabase en prijspeil 2022, zonder evacuatie. Nieuwe invoer gebruikt maximale beschikbare MAP-waterdiepte en -snelheid na t=0 tot dag 10. Stijgsnelheid en aankomsttijd zijn afgeleid uit CLM-klasseovergangen vanaf bresuur 4. Onoplosbare stijgsnelheid blijft NoData; niet stilzwijgend nul. De gevolgen blijven daarom voorlopig.

De atlas publiceert de vier gevolgenrasters als buurtaggregaten: schade, dodelijke slachtoffers, getroffenen en mediaan van positieve mortaliteitscellen. Ruwe MAP-, HIS-, CLM-, restart- en SSM-objectbestanden blijven lokaal. HIS-SSM wordt hier gebruikt als naam van de gevolgenberekening; dit levert geen afzonderlijke dagelijkse gevolgencurves op.

Private uitvoer en bronkoppeling: outputs/atlas_ssm_20261102. scripts/hydraulic_series.py bevat de controle van voortgezette uitvoer. BESCHIKBAARHEID.md en data/availability.json worden uit de gepubliceerde catalogus gegenereerd.

Uitgevoerd: 212 aanvullende complete SSM-sets; samen met 27 bestaande gekoppelde sets zijn alle 239 hydraulisch beschikbare scenario’s voorzien van gevolgenlagen. De vier uitvoerrasters zijn per set gecontroleerd op hetzelfde 50 m-rooster als de invoer. Waar SSM geen CRS-metadata schreef, is EPSG:28992 overgenomen uit het exact overeenkomende invoerrooster, zonder wijziging van rasterwaarden.
