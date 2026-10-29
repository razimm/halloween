# Software und Integrationen

## Steuerungsarchitektur
Python-Anwendung mit austauschbaren Hardware-Adaptern und einem Simulationsmodus:
```text
IDLE --Buzzer--> RUNNING --Timeline fertig--> COOLDOWN --Timer--> IDLE
                    |
                    +-- Fehler/Stop --> sicherer Stopp / ERROR
```
Beim Start keine Aktoren automatisch auslösen. Während RUNNING zusätzliche Tastendrücke ignorieren; während COOLDOWN stattdessen nur die Sprachansage „Noch nicht!“ anfordern. Keine weitere Show starten. Begrenzte Laufzeiten, Timeouts, Logging und physischer Not-Stopp.

## GPIO-Buzzer
Der rote, bereits ausgemessene Buzzer ist ein Schließer (offen / ca. 6 Ω gedrückt). Geplant: GPIO17 gegen GND mit internem Pull-up und Entprellung; wetterfeste Leitung und geeignete Eingangssicherung bei Außenverkabelung prüfen. **Nur der Buzzer startet die gesamte Show, und zwar ausschließlich im IDLE-Zustand.** Im RUNNING-Zustand keine Reaktion, im COOLDOWN-Zustand ausschließlich die Ansage „Noch nicht!“.

## Nebel über DS3218-Servo
Der **Miuzei DS3218** ist die getroffene Entscheidung (kein Bluetooth-Fingerbot). Der Pi gibt ein Positionssignal über GPIO18 aus; der Servo wird separat mit 5 V versorgt, mit gemeinsamer Signalmasse. Er hält den Taster der kabelgebundenen Fernbedienung nur für eine kurze, begrenzte Zeit gedrückt und fährt zurück. Die Endpunkte sind mechanisch zu kalibrieren. Der Servo hält unter Last aktiv seine Position; er ist **nicht selbsthemmend**. Es braucht eine sichere Freigabe, auch bei Ausfall, Verklemmen oder Pi-Neustart. Keine Änderung der Netzspannung oder der Sicherheitsschaltungen der Nebelmaschine. Siehe [Servo](servo.md).

## KORAD über USB
USB-Kommunikation und tatsächliches Befehlsprotokoll **modellbezogen** prüfen (nicht jedes Gerät beherrscht allgemeines SCPI). Vorgehen:
1. USB verbinden, Gerät erkennen, Schnittstelle/Seriell-Einstellungen identifizieren.
2. Bei ausgeschaltetem Ausgang/ohne LED nur lesende Abfrage.
3. Ein-/Ausschaltfolgen mit geeigneter Prüflast, Stromgrenze und Messung der Latenz.
4. Erst nach LED-Datenblatt und Prüfung des Einschaltverhaltens Test mit LED.
Zeitliche Befehlsverzögerung (Jitter), Regelträgheit und Einschaltstromspitzen können schnelles Flackern begrenzen. **Keine sichere 50-ms-PWM-Funktion zusagen.** Für schnelles Flackern wäre ein passender **PWM-dimmbarer Konstantstrom-LED-Treiber** zuverlässiger; ein simpler MOSFET hinter dem KORAD schützt eine nackte LED nicht automatisch.

## Art-Net/DMX
Python sendet Art-Net an Showtec-Node; DMX-Kanalbelegung vorab einmessen. Sicheres Grundlicht statt blendender Strobo-Effekte.

## Musik und separates Soundboard
Der bereits getestete Ablauf verwendet Logitech G433 USB-Audio. Zusätzlich soll die **Hama-Fernbedienung ausschließlich einzelne spontane Sounds** auslösen, die der **Denon HEOS 5** im Netzwerk abspielt. Sie darf die Hauptshow nicht starten und weder Servo/Nebel noch DMX/KORAD automatisch aktivieren. Die HEOS-CLI kann über TCP/1255 für Player- und Mediensteuerung verwendet werden; USB-Medien am HEOS müssen über die passende Mediennavigation identifiziert werden. HEOS-Startlatenz ist zu messen; keine präzise Synchronisation annehmen. Einzelheiten: [HEOS-Soundboard](heos-soundboard.md).

Lokale Dateien rechtmäßig verwenden; Lautstärke begrenzen, Stop/Abbruch implementieren. Keine urheberrechtlich geschützten Songs im öffentlichen GitHub-Repository.

## Webcam / separater Live-Stream
Eine Trust-USB-Webcam soll ausschließlich den Eingang im Heimnetz sichtbar machen. Konzeption: V4L2-Kamera → FFmpeg → HLS-Segmente/Playlist im flüchtigen Speicher → Nginx → Browser/Player. Kein Recording, keine Bewegungserkennung und **keine Webcam-Auslösung** von Show oder Sounds. HLS-Latenz und Pi-Last separat testen. Siehe [Webcam](webcam.md).

## Vorgeschlagene spätere Code-Struktur
```text
src/main.py
src/buzzer.py
src/fog.py       # DS3218-Servo, keine Bluetooth-Fingerbot-Steuerung
src/korad.py
src/lighting.py
src/audio.py
src/remote.py    # Hama-Tastenevents / HEOS-Sounds
shows/michael_myers.json
requirements.txt
```
Erst Hardware-Simulator, anschließend jeweils ein Integrationstest. Optional lokale Weboberfläche für Presets, Diagnose, Sperrzeit und Lautstärke; nicht ungeschützt ins Internet exponieren.

## Codex
Codex CLI kann für Entwicklung im geklonten Repo verwendet werden; auf dem Pi zuerst OS/Architektur und aktuelle Installationsanleitung prüfen. Keine Passwörter oder Geräteschlüssel committen.

## Cooldown-Sprachansage (statt Status-LEDs)

Die rot/grünen Buzzer-Status-LEDs sind gestrichen. Beim Drücken des roten Buzzers gilt:

| Showzustand | Reaktion |
| --- | --- |
| IDLE | Einmaliger Start der vollständigen Halloween-Show |
| RUNNING | Weitere Drücke ohne akustische Rückmeldung ignorieren |
| COOLDOWN | Nur die gruselige Ansage **„Noch nicht!“** anfordern; weder Show noch Nebel/Licht neu starten |
| ERROR/STOP | Kein neuer Showstart; sichere Fehlerbehandlung |

**Wiedergabe-Semantik:** Ein eigener non-reentrant Audioeffekt mit genau einer aktiven Instanz. Drücke während der laufenden Ansage werden verworfen, nicht gepuffert oder neu gestartet. Der Sound läuft bis zu seinem regulären Ende und kann danach erneut ausgelöst werden, solange der Cooldown aktiv ist. Der Cooldown-Timer läuft unabhängig weiter; der Übergang in IDLE darf eine laufende Ansage nicht ungewollt abschneiden (Ende abwarten oder Showstart bis zum Ende sperren). Fehler/Not-Stopp darf bei Bedarf Audio sicher abbrechen. Taster-Entprellung getrennt von dieser Wiedergabesperre vorsehen.

Das ist ein **Buzzer-Effekt**, kein Hama-Fernbedienungs-Soundboard-Effekt. Für geringe Latenz zunächst den vorhandenen lokalen Logitech-G433-Audiopfad prüfen; Ausgabe und Mischung mit etwaigen weiteren Sounds müssen in Codex konkretisiert werden. Keine Audiodatei oder Implementierung in diesem Dokument.
