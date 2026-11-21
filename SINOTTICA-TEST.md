# N.I. SINOTTICA — stato verifiche

- Cartografia Natural Earth vettoriale: caricata sul branch.
- Frontend: legge i dati GeoJSON e, se disponibili, i raster terrain.json.
- Backend NOAA GFS: implementato ma NON ancora eseguito con successo su GitHub Actions.
- NOAA NOMADS può imporre limiti di accesso e disponibilità. Non sono ammessi aggiramenti.
- La scheda Actions potrebbe non mostrare workflow presenti solo su branch non predefiniti.
- Non sono stati pubblicati dati sinottici fittizi.
- Fronti: volutamente disattivati finché non esiste un algoritmo meteorologico validato.
- Raster ombreggiatura: codice pronto, GeoTIFF sorgente ancora da acquisire con licenza verificata.
- Licenza dei dati Natural Earth: pubblico dominio; Leaflet BSD-2-Clause.
- NON un sistema operativo completo, né un rilascio su main.

## Verifiche necessarie prima della pubblicazione
1. Verificare autorizzazione e accessibilità dei dataset NOAA NOMADS.
2. Eseguire backend e test offline, correggere eventuali problemi cfgrib/GRIB2.
3. Verificare frame, timestamp, pressione hPa, vento km/h, geometrie e posizionamento.
4. Acquisire DEM e batimetria con licenze di redistribuzione controllate.
5. Testare su GitHub Pages in anteprima isolata, mobile e desktop.
6. Validare un algoritmo per i fronti su casi reali e documentare incertezze.
7. Approvazione esplicita prima di modificare main.
