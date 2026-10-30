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
- [x] Trust-USB-Webcam am Pi mit USB/V4L2 identifizieren (`0c45:6340`, uvcvideo).
- [ ] Auflösung, Framerate und Betrieb bei Dunkelheit prüfen; LED-Typ verifizieren.
- [x] Eigenständige FFmpeg-/MJPEG-Browseransicht im Heimnetz einrichten (640 × 480, angefordert 15 fps), HTTP und zwei Zuschauer getestet.
- [ ] MJPEG-Verzögerung im Browser vor Ort beurteilen; bei Bedarf WebRTC evaluieren.
- [ ] Keine Archivierung, keine Internetfreigabe, eingegrenzten Bildausschnitt und Ressourcenlast sicherstellen.

## Software
- [x] Showcontroller mit getrennten Adaptern und Simulation.
- [x] Zustandsautomat mit manueller Hama-1-Freigabe, Abbruch und zwei zufälligen Voice-Ansagen.
- [x] Audiofolge, Zap-Timeline und konfigurierbare Art-Net-Lichtfolge implementiert; komplette Hardwareabnahme offen.
- [ ] Nebel- und KORAD-Module nur nach Tests aktivieren.
- [ ] Sicherer Fehlerzustand und Logging.
- [x] Hama-USB-Empfänger erkennen (`05a4:9881`); 1/2/3 und Play/Pause getestet.
- [x] OFF (KEY_SLEEP, 142) als Panic-Stopp mit Rückkehr über Taste 1 implementiert.
- [ ] Übrige Hama-Tasten nach Bedarf zuordnen.
- [x] HEOS_Kueche per Netzwerk erkannt; OK spielt Lachen per HTTP vom Pi bei 10 %.
- [ ] Wiederanlauf nach längerer Standby-Zeit prüfen; weitere Soundtasten optional.
- [ ] Hama-Soundboard bewusst unabhängig vom Außen-Buzzer halten.
- [ ] Halloween-Schild „Auf keinen Fall den Knopf drücken“ als Asset hinzufügen.
- [ ] Optional Weboberfläche und mehrere Presets.

## Erfolgskriterien

Ein Druck startet höchstens eine Show. Während RUNNING werden weitere Drücke
ignoriert; in LOCKED gibt es drei rote Blinkzyklen und eine zufällige vollständige
Voice-Ansage. Hama-Taste 1 gibt frei, ohne eine laufende Ansage abzuschneiden.
Kein zeitgesteuerter Cooldown. Fehler führen zum gemeinsamen Stopp.

## Aktueller Showcontroller

- [x] Idle-Hintergrundloop mit einstellbaren 30 % Sample-Amplitude.
- [x] Zap mit LED-Ausfall → Bell → Myers mit Flat-Par-Licht → Lachen.
- [x] Dauersperre bis Hama-Taste 1, roter/grüner Flat-Par-Status.
- [x] Zufällige Ansagen ohne Überlagerung, Neustart oder Warteschlange.
- [x] Freigabe während Ansage: Lampen sofort, Musik/Buzzer nach Ansageende.
- [x] ArtPoll: Node 192.168.178.146, Portadresse 1; roter Farbtest reagiert.
- [x] Vollständigen Blackout vor Ort bestätigt (29.10.2026).
- [ ] Grün/Rot und vollständige Show vor Ort testen.
- [ ] Buzzer, Hama und komplette Show gemeinsam auf Hardware testen.
- [ ] Myers-Lichtfolge mit Sicht-/Hörtest abstimmen.

Bedienung und Konfiguration: [Showcontroller](show.md).
