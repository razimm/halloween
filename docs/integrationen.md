# Software und Integrationen

## Steuerungsarchitektur

Implementiert in `tools/show_controller.py`, Hardwareadapter in `tools/show_hardware.py`.
Bedienung und Konfiguration: [Showcontroller](show.md).

```text
IDLE --Buzzer--> RUNNING --Showende--> LOCKED --Hama 1--> IDLE
                                        |                ^
                                        +--Buzzer: Voice--+
```

Eine Ansage läuft vollständig zu Ende. Bei Freigabe während der Ansage wechseln
beide Lampen sofort; Hintergrundmusik und Buzzer warten bis zum Ansageende.
Kein automatischer Cooldown. Buzzer während RUNNING wird verworfen.

## GPIO-Buzzer

GPIO17 gegen GND mit internem Pull-up und Entprellung. Nur IDLE startet die Show;
LOCKED löst zufällige Ansage plus drei rote Blinkzyklen aus. Während Ansagen gibt
es keine neuen Sounds, Neustarts oder Warteschlangen. Hama-Taste 1 (`KEY_KP1`, 79)
ist ausschließlich die Freigabe, kein Showstart. Außenschutz weiter prüfen.

## Nebel über MS24-UF-Servo
Der **Miuzei MS24-UF** ist die getroffene Entscheidung (kein Bluetooth-Fingerbot). Der Pi gibt ein Positionssignal über GPIO18 aus; der Servo wird separat mit 5 V versorgt, mit gemeinsamer Signalmasse. Er hält den Taster der kabelgebundenen Fernbedienung nur für eine kurze, begrenzte Zeit gedrückt und fährt zurück. Die Endpunkte sind mechanisch zu kalibrieren. Der Servo hält unter Last aktiv seine Position; er ist **nicht selbsthemmend**. Es braucht eine sichere Freigabe, auch bei Ausfall, Verklemmen oder Pi-Neustart. Keine Änderung der Netzspannung oder der Sicherheitsschaltungen der Nebelmaschine. Siehe [Servo](servo.md).

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

Alle Show-, Hintergrund- und Voice-Dateien laufen über den lokalen Logitech-G433-Pfad.
Idle-Hintergrundmusik: einstellbare 15 % Sample-Amplitude; Zap/Voice 100 %, Kirchenglocke 75 %, Lachen 60 %, Michael Myers mit 98 % Spitzenpegel (ohne Sample-Clipping). Im Idle: PAR 5 %, KORAD 300 mA; in der Show bis 100 % (KORAD maximal 700 mA). KORAD blendet in den letzten 0,5 Sekunden des Zap-Sounds aus. Reihenfolge: Zap → Kirchenglocke → Myers → Lachen.
Hama-Taste 1 ist für Freigabe reserviert; Play/Pause steuert KORAD bei Sperre.
OK spielt Lachen auf HEOS_Kueche. Für jeden weiteren Sound gelten die
[verbindlichen HEOS-Vorgaben](heos-soundboard.md#verbindliche-vorgaben-für-neue-sounds):
endlicher UPnP-Titel, eigene Dateimetadaten und eine gemeinsame Sperre bis zum
tatsächlichen Wiedergabeende.

## Webcam / separater Live-Stream
Eine Trust-USB-Webcam soll ausschließlich den Eingang im Heimnetz sichtbar machen. Umgesetzt: V4L2-Kamera → FFmpeg → jeweils neuestes JPEG im Arbeitsspeicher → HTTP/MJPEG → Browser auf Port 8080. Eigenständiger Dienst `halloween-webcam`, ohne Nginx, Bilddateien oder HLS-Segmentpuffer. Kein Recording, keine Bewegungserkennung und **keine Webcam-Auslösung** von Show oder Sounds. Ende-zu-Ende-Latenz im Browser und Pi-Last bei paralleler Show noch testen. Siehe [Webcam](webcam.md).

## Vorgeschlagene spätere Code-Struktur
```text
src/main.py
src/buzzer.py
src/fog.py       # MS24-UF-Servo, keine Bluetooth-Fingerbot-Steuerung
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
