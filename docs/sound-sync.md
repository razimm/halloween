# Einzeltest: Sound und LED synchronisieren

Für den vollständigen Dauerbetrieb mit Buzzer, Hama und Idle-Musik siehe
[Showcontroller](show.md). Die folgenden Netzteil-Messungen und Python-Aufrufe
beschreiben den separaten Zap-Test. `start-show.sh` startet jetzt den vollständigen Controller.

Referenz: [Electric Shock / Taser Zap – Jochi SFX](https://www.youtube.com/watch?v=Zfcaj7M0Qnk).
Die aktuelle Schnittfassung liegt unter `audio/electric-zap_break_final.mp3`
und ersetzt `audio/electric-zap.wav`. Die dekodierte Audiospur dauert
9,335 Sekunden. Die Timeline wird bei jedem Start aus der aktuellen Datei
berechnet; die Zeitmarken der alten 7,419-Sekunden-Fassung gelten nicht mehr.
Audiodateien werden lokal bereitgestellt und von Git ignoriert.

`tools/sound_light.py` dekodiert MP3 mit FFmpeg einmalig in eine Mono-WAV
(44,1 kHz, 16 Bit PCM) unter `audio/playback/`. Analyse und Wiedergabe
verwenden dieselben dekodierten Samples, einschließlich der MP3-Verzögerungskorrektur.
Die Analyse erfolgt weiterhin in 80-ms-Fenstern.
In den Pausen bleibt die LED dauerhaft hell (500 mA). In den Entladungen
folgt die Stromvorgabe dem Lautstärkeverlauf (5–500 mA). Der Benutzer hat
die gemeinsame Wiedergabe über Logitech G433 am 26.10.2026 als passend
bestätigt (»perfekt«), damals mit der alten WAV-Fassung. Die neue MP3-Fassung
ist in Simulation geprüft; ein erneuter Hör-/Lichttest steht aus.

## Einrichtung und täglicher Start

```bash
./setup.sh
./start-show.sh --simulate
sudo ./start-show.sh --play
```

`setup.sh` erstellt `.venv/` dauerhaft im Projekt und installiert die
festgelegten Treiberpakete. Voraussetzungen: Python 3 mit venv/pip und
`alsa-utils` (`aplay`) und `ffmpeg`. Das Startskript funktioniert auch aus einem anderen
Arbeitsverzeichnis. Lautstärkeangepasste Wiedergabedateien liegen dauerhaft in `audio/playback/`, nicht in `/tmp`.
Nach einem frischen Clone muss die MP3 separat bereitgestellt werden:
[Audio-Herkunft und Format](../audio/README.md).

Das Startskript simuliert standardmäßig; `--play` startet echte Hardware. Weitere Optionen werden weitergereicht:

```bash
sudo .venv/bin/python tools/sound_light.py audio/electric-zap_break_final.mp3 --play --audio-device 'plughw:CARD=Headset,DEV=0' --gain 0.2 --light-lead-ms 0
```

Getesteter Ausgang: `plughw:CARD=Headset,DEV=0` (Logitech G433 USB mit
Klinkenanschluss am Logitech-Gerät, nicht der Klinkenausgang des Pi).
Keine Radio-Dienste wurden gestoppt oder umkonfiguriert.

## Direkter Python-Aufruf

```bash
# Standard ist Simulation, ohne Hardwarezugriff oder Wiedergabe
python tools/sound_light.py audio/electric-zap_break_final.mp3 --timeline shows/electric-zap.json

# Nur bei angeschlossener LED auf Kühlkörper und freiem Audioausgang:
python tools/sound_light.py audio/electric-zap_break_final.mp3 --play --audio-device 'plughw:CARD=Headset,DEV=0'
```

Python benötigt `pyserial`, die MP3-Dekodierung `ffmpeg`, die Wiedergabe `aplay`. Der Benutzer benötigt
Zugriff auf den seriellen Port und das Audiogerät. Nicht parallel zu anderen
Netzteil-Steuerprogrammen starten. Port und Audioausgang sind explizit wählbar.
Standardmäßig wird nur diese Wiedergabe auf 20 Prozent Sample-Amplitude reduziert;
Systemlautstärke und laufende Radio-Dienste werden nicht verändert.

Vorbereitung: Gerätekennung und ausgeschalteten Ausgang prüfen, bei 1 mA von
0 auf 10 V Spannungsgrenze hochfahren, dann langsam auf 500 mA aufblenden.
Am Ende folgt eine Sekunde Dauerhell, danach Ausgang aus, 0 V / 10 mA.
Bei Python-Fehler, Strg+C oder SIGTERM versucht `finally` denselben Stopp.
Bei Strom-/USB-Ausfall oder SIGKILL kann Software keinen Stopp garantieren.

Audio und Licht werden anhand derselben monotonen Uhr gestartet. Der Start von
ALSA und die Reaktionszeit des Netzteils verursachen zusätzliche Latenz.
`--light-lead-ms` verschiebt Lichtbefehle bei positiven Werten nach vorn.
Die USB-Messwerte sind verzögert und erfassen weder einzelne kurze Impulse
noch Stromspitzen zuverlässig. Dies ist keine samplegenaue Synchronisation
und kein Nachweis für einen sicheren LED-Dauerbetrieb.

## Testprotokoll vom 26.10.2026

- USB-Kennung: `KORAD KKG305P V1.3`; 9600 Baud, 8N1, LF erforderlich.
- Rein lesende Anfangsabfrage: Ausgang aus, 11,40 V / 1,500 A eingestellt,
  gemeldet 0 V / 0 A. OVP und OCP deaktiviert; Schwellen 31 V und 5,1 A.
  Diese Schutzfunktionen wurden nicht umkonfiguriert.
- Unbelastet: 1 V / 50 mA eingestellt, kurz eingeschaltet, gemeldet 1 V / 0 A,
  danach Ausgang aus. Multimeter- und Prüflastmessungen wurden übersprungen.
- LED auf Kühlkörper angeschlossen. Zunächst 10 mA Stromgrenze, Spannung von
  0 V langsam erhöht: bei 8,5 V Vorgabe etwa 7,53 V / 9 mA gemeldet, LED sichtbar.
- Drei langsame Lichtimpulse erfolgreich. Spannungsmoduliertes Flackern wirkte
  künstlich; Strommodulation wurde als bessere Grundlage gewählt.
- Kerzenlicht: geglättete unregelmäßige Stromvorgaben, fünf Sekunden. Bis 50 mA
  und anschließend bis 100 mA getestet; der Benutzer bewertete den Effekt positiv.
  8,5 V und 10 V Spannungsgrenze getestet; tatsächliche Spannung bei kleinen
  Strömen ungefähr 7,6–7,9 V.
- Horrorflackern: kurze unregelmäßige Impulse und längere schwache Phasen,
  zunächst bis 100 mA, danach bis 500 mA Vorgabe bei 10 V Spannungsgrenze.
  Schnelle Fassung etwa 5 s, langsame Fassung etwa 10 s. Beide sichtbar getestet.
- Gemischte Folge: 2 s Dauerhell, 3 s helles Flackern, 2 s Dauerhell,
  3 s dunkleres Flackern, 2 s Dauerhell, 3 s helles Flackern, 2 s Dauerhell.
  Dauerhell 500 mA, helles Flackern 5–500 mA, dunkleres etwa 2–150 mA.
  Danach gleiche Folge mit halbierten Impuls-/Pausenzeiten nur im Flackern.
- Dauerhell meldete ungefähr 8,81 V / 499 mA. Das ist die tatsächliche
  LED-Betriebsspannung bei diesem Test, keine fest eingestellte 8,81-V-Grenze.
- Endgültiger Soundtest zweimal erfolgreich über Logitech wiedergegeben;
  zweite Wiedergabe ausdrücklich als zeitlich passend bestätigt.
- Nach jedem Test Ausgang ausgeschaltet und ausgeschalteten Zustand ausgelesen.
  Übliche Endeinstellung: 0 V / 10 mA.

Die gespeicherte JSON-Timeline enthält nur Steuerwerte, keine Audiodaten.
Das Programm erzeugt sie aus der aktuellen Audiodatei beim Start neu, damit Datei und
Ablauf zusammenpassen. Aktorsteuerung für Nebel, GPIO-Buzzer und DMX ist noch offen.

## Softwareprüfungen

```bash
./test.sh
./start-show.sh --simulate
```

Die Tests prüfen Stromgrenzen und Lautlosigkeit der Simulation sowie das
Aufräumen nach einem Wiedergabefehler. Sie ersetzen keine elektrischen Messungen.

`./test.sh` bleibt bei Erfolg still und zeigt nur bei Fehlern das Testprotokoll.
