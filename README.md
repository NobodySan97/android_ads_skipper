# Android Ads Skipper (per LlamaLab Automate)

Un sistema ad alte prestazioni per il rilevamento e la gestione automatica degli annunci pubblicitari su Android tramite **[LlamaLab Automate](https://llamalab.com/automate/)**.

Il progetto genera query XPath 2.0 / 3.0 ottimizzate per il motore **Saxon-HE** utilizzato da Automate, consentendo a un unico flusso di:
1. **Mute Audio Automatico**: Rileva quando un annuncio è in riproduzione (tramite `ad_playing_indicators_xpath`) e azzera il volume multimediale (`STREAM_MUSIC`).
2. **Auto-Skip & Close**: Individua non appena compaiono i pulsanti "Salta", "Chiudi" o "X" (tramite `ad_skip_buttons_xpath`) e simula il tocco via Accessibility Service.

---

## 🚀 Novità e Migliorie della Versione Aggiornata

- **Supporto Multilingua Globale (10+ lingue)**:
  - 🇮🇹 **Italiano**: *"Salta annunci"*, *"Salta annuncio"*, *"Chiudi annuncio"*, *"Visita l'inserzionista"*, *"No, grazie"*, *"Non ora"*.
  - 🇬🇧 **Inglese**: *"Skip ad(s)"*, *"Close ad panel"*, *"Visit advertiser"*, *"No thanks"*, *"Not now"*.
  - 🇪🇸 **Spagnolo**: *"Saltar anuncio(s)"*, *"Omitir anuncio(s)"*, *"Cerrar anuncio"*, *"Visitar anunciante"*.
  - 🇫🇷 **Francese**: *"Passer l'annonce"*, *"Ignorer l'annonce"*, *"Fermer l'annonce"*, *"Non merci"*.
  - 🇩🇪 **Tedesco**: *"Werbung überspringen"*, *"Werbung schließen"*, *"Nein danke"*.
  - 🇵🇹 **Portoghese**: *"Pular anúncio(s)"*, *"Fechar anúncio"*.
  - 🇯🇵 **Giapponese**: *"広告をスキップ"*, *"広告を閉じる"*.
  - 🇰🇷 **Coreano**: *"광고 건너뛰기"*, *"광고 닫기"*.
  - 🇷🇺 **Russo**: *"Пропустить рекламу"*, *"Закрыть рекламу"*.
  - 🇨🇳 **Cinese (Semplificato e Tradizionale)**: *"略過廣告"*, *"跳过广告"*, *"关闭广告"*.

- **Copertura Ad Network e App Moderne**:
  - **YouTube & YouTube Music**: Nuovi identificatori (`modern_skip_ad_button`, `secondary_action` per dismiss upsell, `countdown_text`).
  - **Principali SDK Pubblicitari (Giochi e App Freemium)**: Google AdMob, AppLovin / MAX, Unity Ads, IronSource, Pangle / TikTok Ads, Mintegral, Vungle.

- **Ottimizzazione Performance per Automate**:
  - Inserimento dei controlli booleani veloci (`@android:clickable='true'`, `@android:enabled='true'`) prima delle espressioni regex `fn:matches()` per sfruttare il *short-circuit evaluation* ed evitare cali di frame rate e consumi anomali di batteria.
  - Salvaguardia contro falsi positivi: esclusione automatica di campi di testo modificabili (`not(../@android:editable='true')`).

- **Tooling Completo**:
  - `build.py`: Compilatore automatico da regole JSON a XPath pronto per Automate.
  - `test_suite.py`: Suite di verifica su casi reali per garantire zero falsi positivi.
  - `tools/inspect_layout.py`: Strumento CLI per ispezionare dump XML o catturare al volo la schermata del telefono via ADB.

---

## 📦 Struttura del Progetto

```
android_ads_skipper/
├── detection_criteria.json         # Regole sorgente modulari (ID e Testi)
├── android_ads_skip_watchlist.json # Watchlist compilata per Automate (JSON)
├── android_ads_skip_watchlist.hjson# Watchlist compilata in formato HJSON
├── build.py                       # Compilatore XPath
├── test_suite.py                  # Test di regressione anti-falsi-positivi
├── tools/
│   └── inspect_layout.py          # Tool di cattura e analisi layout da ADB
└── examples/                      # Campioni reali XML di schermate Android
```

---

## 📲 Configurazione in LlamaLab Automate

Puoi scegliere uno dei due metodi:

### Metodo A (Consigliato - Diretto con file .flo già pronto)
1. Scarica direttamente sul telefono il file già pre-configurato:
   **[Universal_ads_mute_and_skip_improved_v3.flo](https://raw.githubusercontent.com/NobodySan97/android_ads_skipper/main/Universal_ads_mute_and_skip_improved_v3.flo)**
2. Aprilo con l'app **Automate**: il flusso è già impostato con l'URL del tuo repository e pronto all'avvio!

### Metodo B (Se hai già installato il flusso dalla community)
1. Apri il flusso esistente [#39642](https://llamalab.com/automate/community/flows/39642).
2. Tocca il blocco **HTTP Request** (o *Download*) e imposta come Request URL:
   `https://raw.githubusercontent.com/NobodySan97/android_ads_skipper/main/android_ads_skip_watchlist.json`
   - Il flusso legge le variabili contenute in `android_ads_skip_watchlist.json`.
   - Puoi caricare il file direttamente sulla memoria interna del dispositivo oppure puntare all'URL raw del file JSON/HJSON.
3. **Permessi Android necessari**:
   - **Accessibilità (Accessibility Service)**: Richiesto da Automate per ispezionare l'albero UI e simulare il click.
   - **Controllo Audio / Non Disturbare**: Richiesto per impostare il volume multimediale a 0 durante la riproduzione dell'annuncio e ripristinarlo al termine.

---

## 🛠️ Come Compilare e Testare

### 1. Compilare le regole
Modifica `detection_criteria.json` aggiungendo nuovi ID o parole chiave, poi esegui:
```bash
python build.py
```

### 2. Eseguire la suite di test
Verifica che le nuove regole non provochino falsi positivi su riproduzioni video normali:
```bash
python test_suite.py
```

### 3. Ispezionare un annuncio non riconosciuto (via ADB)
Collega il telefono con Debug USB attivo e visualizza l'annuncio sullo schermo, quindi esegui:
```bash
python tools/inspect_layout.py --adb
```
Il tool analizzerà la schermata e ti mostrerà gli ID e i testi esatti dell'elemento cliccabile da inserire nei criteri.
