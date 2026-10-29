# Roadmap – Halloween 2026

Zieldatum: **31.10.2026**. Priorität: sichere Grundversion vor optionalen Effekten.

## Bestandsaufnahme
- [x] Raspberry-Pi-Modell und OS-Architektur ermitteln.
- [x] Großen roten Buzzer auswählen und Schließerkontakt messen (offen / ca. 6 Ω gedrückt).
- [ ] Buzzer per GPIO17 mit internem Pull-up testen; Außenmontage/Wetterschutz fertigstellen.
- [ ] Nebel-Fernbedienung dokumentieren; Tastenkraft und Haltezeit feststellen.
- [x] **DS3218-Servo statt SwitchBot** als Nebel-Aktuator wählen.
- [ ] Separate 5-V-/3-A-Versorgung, Halterung, Kalibrierung und sichere Freigabe des Servos testen.
- [ ] LED-Datenblatt, Kühlung und zulässige Stromwerte prüfen.
- [ ] KORAD bei eingeschalteter LED: CC/CV und tatsächliche Werte messen.
- [ ] DMX-Node/LED-PAR: IP, Universum, Kanäle ermitteln.
- [x] Audioausgang klären: Logitech G433 USB mit Klinkenanschluss.

## Unabhängige Tests
- [x] Pi und Audio prüfen.
- [ ] GPIO-Tastendruck ohne Effektgeräte lesen.
- [x] KORAD über USB erkennen und sichere Abfragen testen.
- [x] Unbelasteter Schalttest bei 1 V / 50 mA.
- [x] LED-Funktion und Lichtmuster bis 500 mA Stromvorgabe testen.
- [x] Elektrischen Zap-Sound mit LED synchronisieren; vom Benutzer als passend bestätigt.
- [ ] KORAD-Schalten ohne LED / mit geeigneter Prüflast auf Latenz und Stromspitzen testen.
- [ ] DS3218 zunächst ohne Nebelmaschine bewegen; danach Taster unter Aufsicht drücken und zuverlässiges Freigeben prüfen.
- [ ] Nebel-Fernbedienung nur kurz und kontrolliert mechanisch auslösen.
- [ ] Art-Net-Gerät ansprechen und unkritische Lichtstimmung testen.

## Webcam / Eingangsansicht
- [ ] Trust-USB-Webcam am Pi mit USB/V4L2 identifizieren.
- [ ] Auflösung, Framerate und Betrieb bei Dunkelheit prüfen; LED-Typ verifizieren.
- [ ] Eigenständigen FFmpeg-/Nginx-HLS-Stream im Heimnetz testen (zunächst 640 × 480 / 15 fps, soweit unterstützt).
- [ ] HLS-Verzögerung messen; bei Bedarf MJPEG/WebRTC statt HLS evaluieren.
- [ ] Keine Archivierung, keine Internetfreigabe, eingegrenzten Bildausschnitt und Ressourcenlast sicherstellen.

## Software
- [ ] Modulare Python-Struktur und Simulation.
- [ ] Zustandsautomat mit Sperrzeit, Abbruch und Cooldown-Sprachansage „Noch nicht!“.
- [ ] Konfigurierbare Timeline mit Audio und DMX.
- [ ] Nebel- und KORAD-Module nur nach Tests aktivieren.
- [ ] Sicherer Fehlerzustand und Logging.
- [ ] Hama-USB-Fernbedienung mit Raspberry Pi erkennen und Tastencodes zuordnen.
- [ ] HEOS 5 via lokales Netzwerk erkennen, USB-Soundbibliothek testen und Einzel-Sounds über HEOS-CLI starten.
- [ ] Hama-Soundboard bewusst unabhängig vom Außen-Buzzer halten.
- [ ] Halloween-Schild „Auf keinen Fall den Knopf drücken“ als Asset hinzufügen.
- [ ] Optional Weboberfläche und mehrere Presets.

## Erfolgskriterien
Ein Druck startet höchstens eine Show; während RUNNING werden zusätzliche Drücke ignoriert, im COOLDOWN lösen sie ausschließlich eine nicht überlappende „Noch nicht!“-Ansage aus, Fehler lassen Nebel nicht dauerhaft weiterlaufen, sichere Stop-Funktion funktioniert; keine unnötigen Risiken für Kinder.

## Cooldown-Sound statt Status-LEDs
- [x] Idee für rote/grüne Buzzer-Status-LEDs verworfen; keine Status-LED-Verdrahtung einplanen.
- [ ] Gruselige Audiodatei mit den Worten „Noch nicht!“ bereitstellen (Datei/Rechte und Wiedergabegerät festlegen).
- [ ] Buzzer-Events nach Zustand trennen: IDLE = Show starten; RUNNING = stumm ignorieren; COOLDOWN = ausschließlich Ansage anfordern.
- [ ] Audiowiedergabe als single-instance/non-reentrant auslegen: weitere Drücke während laufender Ansage ignorieren, nicht neu starten, nicht abschneiden, keine Überlagerung und keine Queue.
- [ ] Wenn Ansage beendet und Cooldown noch aktiv ist, darf ein neuer Druck eine weitere vollständige Ansage starten.
- [ ] Übergang COOLDOWN → IDLE darf laufende Ansage nicht mitten im Satz abbrechen; gewünschtes Verhalten bzgl. erneuter Showstarts beim Übergang testen.
- [ ] Schnelles mehrfaches Drücken, Bounce, gleichzeitiger Zustandswechsel und sauberen Abbruch testen.
