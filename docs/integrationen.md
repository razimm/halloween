# Software und Integrationen

## Steuerungsarchitektur
Python-Anwendung mit austauschbaren Hardware-Adaptern und einem Simulationsmodus:
```text
IDLE --Buzzer--> RUNNING --Timeline fertig--> COOLDOWN --Timer--> IDLE
                    |
                    +-- Fehler/Stop --> sicherer Stopp / ERROR
```
Beim Start keine Aktoren automatisch auslösen. Während einer Show weitere Tastendrücke ignorieren; begrenzte Laufzeiten, Timeouts, Logging und physischer Not-Stopp.

## GPIO-Buzzer
`gpiozero` als Kandidat. Nur 3,3-V-kompatible Beschaltung und Entprellung; Wetterschutz beachten.

## Nebel via Bluetooth-Fingerbot
Original **SwitchBot Bot** als Kandidat, direkt per BLE vom Pi; Firmware/API auf Kompatibilität testen. Der Nebel-Taster muss **gehalten** werden: kurzes `press` reicht nicht. Geräteseitig eingestellten Langdruck bzw. Halten und Freigeben nach Kommunikationsausfall testen. Hersteller-/Community-BLE-Lösungen vor konkretem Code prüfen. Mechanische Befestigung darf nicht verklemmen. Die Nebelmaschine muss zusätzlich unabhängig vom Pi abschaltbar bleiben.

## KORAD über USB
USB-Kommunikation und tatsächliches Befehlsprotokoll **modellbezogen** prüfen (nicht jedes Gerät beherrscht allgemeines SCPI). Vorgehen:
1. USB verbinden, Gerät erkennen, Schnittstelle/Seriell-Einstellungen identifizieren.
2. Bei ausgeschaltetem Ausgang/ohne LED nur lesende Abfrage.
3. Ein-/Ausschaltfolgen mit geeigneter Prüflast, Stromgrenze und Messung der Latenz.
4. Erst nach LED-Datenblatt und Prüfung des Einschaltverhaltens Test mit LED.
Zeitliche Befehlsverzögerung (Jitter), Regelträgheit und Einschaltstromspitzen können schnelles Flackern begrenzen. **Keine sichere 50-ms-PWM-Funktion zusagen.** Für schnelles Flackern wäre ein passender **PWM-dimmbarer Konstantstrom-LED-Treiber** zuverlässiger; ein simpler MOSFET hinter dem KORAD schützt eine nackte LED nicht automatisch.

## Art-Net/DMX
Python sendet Art-Net an Showtec-Node; DMX-Kanalbelegung vorab einmessen. Sicheres Grundlicht statt blendender Strobo-Effekte.

## Musik
Lokale Datei, kabelgebundene Audioausgabe bevorzugt für geringere Latenz. Lautstärke begrenzen; Stop/Abbruch implementieren. Keine urheberrechtlich geschützten Songs im öffentlichen GitHub-Repository.

## Vorgeschlagene spätere Code-Struktur
```text
src/main.py
src/buzzer.py
src/fog.py
src/korad.py
src/lighting.py
src/audio.py
shows/michael_myers.json
requirements.txt
```
Erst Hardware-Simulator, anschließend jeweils ein Integrationstest. Optional lokale Weboberfläche für Presets, Diagnose, Sperrzeit und Lautstärke; nicht ungeschützt ins Internet exponieren.

## Codex
Codex CLI kann für Entwicklung im geklonten Repo verwendet werden; auf dem Pi zuerst OS/Architektur und aktuelle Installationsanleitung prüfen. Keine Passwörter oder Geräteschlüssel committen.
