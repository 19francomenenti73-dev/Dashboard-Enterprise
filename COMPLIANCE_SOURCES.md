
# NOWCASTING ITALIA
## Registro unico delle fonti e conformità

Versione: 1.0
Aggiornamento: 18 novembre 2026

Questo documento definisce le regole comuni per i
repository di Nowcasting Italia.

Non costituisce una certificazione legale.
La conformità delle singole fonti richiede la verifica
delle condizioni ufficiali del relativo servizio.

## 1. PRINCIPI VINCOLANTI

1. Utilizzare soltanto fonti autorizzate.
2. Rispettare le licenze dei dati e dei servizi.
3. Non aggirare autenticazioni o limitazioni.
4. Non effettuare scraping non autorizzato.
5. Rispettare quote, timeout e politiche di caching.
6. Riportare le attribuzioni richieste.
7. Distinguere osservazioni, elaborazioni e previsioni.
8. Non pubblicare dati inventati.
9. Non presentare dati scaduti come aggiornati.
10. Verificare i diritti di redistribuzione.

L'accessibilità pubblica di un endpoint non equivale
automaticamente all'autorizzazione per ogni utilizzo.

## 2. REGISTRO DELLE FONTI

### IRIDE - Radar OPERA

Provider: EUMETNET OPERA
Archivio utilizzato: CloudFerro openradar-24h
Prodotto: compositi radar

Verifiche aperte:
- Condizioni di accesso al bucket.
- Licenza applicabile ai prodotti scaricati.
- Redistribuzione dei dati derivati.
- Attribuzione obbligatoria.
- Frequenza delle interrogazioni.

Non dichiarare conformità completa finché queste
condizioni non siano documentate.

### IRIDE - Radar DPC

Provider: Dipartimento della Protezione Civile
Prodotti: VMI e volumi CAPPI
Licenza dichiarata nel codice: CC BY-SA 4.0

Verifiche:
- Condizioni ufficiali delle API.
- Attribuzione.
- Redistribuzione.
- Obblighi ShareAlike per i prodotti derivati.
- Numero complessivo delle richieste.

I prodotti VMI e CAPPI devono essere contabilizzati
separatamente.

### IRIDE - Radar di riserva

Provider: RainViewer

Verifiche:
- Condizioni API e tile.
- Attribuzione.
- Frequenza di accesso.
- Caching.
- Utilizzo pubblico dei prodotti.

### ARGO

Provider: RainViewer
Utilizzo: osservazioni radar e tracking sperimentale

Regole:
- Non interpretare automaticamente i colori HSV
  come valori quantitativi dBZ.
- Non dichiarare misurazioni non disponibili.
- Distinguere vettori osservati e predittivi.
- Conservare timestamp e fonte.
- Verificare condizioni di utilizzo dei tile.

### SIBILLA - NOAA GFS

Provider: NOAA / NCEP
Servizio: NOMADS
Prodotto: GFS

Verifiche:
- Condizioni di accesso.
- Limiti di frequenza.
- Attribuzione.
- Validità temporale dei prodotti.

### SIBILLA - ECMWF

Provider: ECMWF
Servizio: Open Data

Verifiche:
- Licenza del prodotto.
- Condizioni API.
- Attribuzione.
- Redistribuzione dei prodotti derivati.

### SIBILLA - ICON-2I

Provider: Agenzia ItaliaMeteo
Servizio: MeteoHub
Prodotto: ICON-2I
Licenza documentata: CC BY 4.0

Fonti ufficiali:

https://meteohub.agenziaitaliameteo.it/ui/user-guide

https://dati.agenziaitaliameteo.it/dataset/previsioni-meteorologiche-modello-icon-2i

https://meteohub.agenziaitaliameteo.it/nwp/

La documentazione descrive la navigazione delle
directory pubbliche e il download dei prodotti.

Regole operative:
- Conservare ICON-2I.
- Rispettare le condizioni di fair use.
- Evitare download duplicati dello stesso ciclo.
- Conservare il ciclo e la validità del modello.
- Non dichiarare aggiornati prodotti scaduti.

La modalità automatica di consultazione degli indici
deve restare coerente con le condizioni del gestore.

### SIBILLA - Natural Earth

Utilizzo: maschera geografica terrestre.

Verificare licenza e attribuzione del dataset
specifico impiegato.

### ZEUS

Provider: EUMETSAT
Servizio: EUMETView WMS
Prodotto: MTG Lightning Imager

Verifiche:
- Condizioni del servizio WMS.
- Autorizzazione al riutilizzo.
- Attribuzione.
- Validità temporale.

Se il prodotto non è disponibile, pubblicare
uno stato di indisponibilità, non osservazioni
simulate.

### HURRICANE TRACKER

Provider: NOAA / National Hurricane Center
Utilizzo: prodotti tropicali ufficiali

Verifiche:
- Condizioni dell'endpoint.
- Attribuzione.
- Validità temporale.
- Corretta distinzione tra osservazioni
  e traiettorie previste.

### DASHBOARD E SATELLITE

Fonti individuate:
- OpenStreetMap
- NASA GIBS
- RainViewer
- EUMETSAT

Per ogni layer verificare:
- Licenza.
- Condizioni del servizio tile o WMS.
- Attribuzione visibile.
- Frequenza e caching.
- Redistribuzione, se prevista.

## 3. METADATI OBBLIGATORI

Ogni nuovo prodotto dati deve documentare,
quando applicabile:

- Provider.
- Identificativo del prodotto.
- URL o identificativo della sorgente.
- Licenza.
- Attribuzione.
- Timestamp dell'osservazione o ciclo modello.
- Timestamp di acquisizione.
- Timestamp di validità.
- Stato della sorgente.
- Elaborazioni effettuate.
- Natura osservativa o previsionale.

Non inventare valori assenti.

## 4. GESTIONE DEGLI ERRORI

Se una sorgente fallisce:

1. Registrare l'errore.
2. Applicare timeout e retry limitati.
3. Non aggirare blocchi o quote.
4. Non trasformare dati vecchi in dati attuali.
5. Utilizzare fallback solo se autorizzati.
6. Segnalare la sorgente effettivamente utilizzata.

## 5. REGOLE SCIENTIFICHE

Le osservazioni radar reali devono rimanere
distinte dalle elaborazioni e dalle previsioni.

Le classificazioni sperimentali non devono
essere presentate come conferme scientifiche.

La riuscita di una GitHub Action non dimostra
la correttezza dei dati meteorologici.

## 6. CONFIGURAZIONI APPROVATE

SIBILLA:
- Orizzonti: 4, 8, 16, 24, 36 ore.
- Classi: A, B, C.
- Frequenze operative già approvate.

IRIDE:
- Conservare rendering 3D approvato.
- Conservare i dati radar osservativi.
- Non alterare i vettori senza verifica.

ARGO:
- Conservare la distinzione tra osservazioni
  reali e proiezioni.

Queste configurazioni non devono essere
modificate da interventi di conformità.

## 7. STATO DELL'AUDIT

La presenza di una fonte in questo registro
non certifica automaticamente la conformità.

Le verifiche documentali ancora aperte devono
essere completate prima di dichiarare che
l'intero sistema è conforme al 100%.

## 8. AMBITO

La politica si applica a tutti i repository
attivi di Nowcasting Italia, compresi quelli
che non possiedono workflow GitHub Actions.

Fine documento.
