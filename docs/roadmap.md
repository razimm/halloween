# Roadmap – Halloween 2026

Zieldatum: **31.10.2026**. Priorität: sichere Grundversion vor optionalen Effekten.

## Bestandsaufnahme
- [ ] Raspberry-Pi-Modell und OS-Architektur ermitteln.
- [ ] GPIO-Buzzer und wetterfestes Gehäuse auswählen.
- [ ] Nebel-Fernbedienung dokumentieren; Tastenkraft und Haltezeit feststellen.
- [ ] Fingerbot-Modell, lokale BLE-Steuerbarkeit, Halte-/Freigabefunktion klären.
- [ ] LED-Datenblatt, Kühlung und zulässige Stromwerte prüfen.
- [ ] KORAD bei eingeschalteter LED: CC/CV und tatsächliche Werte messen.
- [ ] DMX-Node/LED-PAR: IP, Universum, Kanäle ermitteln.
- [ ] Lautsprecher und Audioausgang klären.

## Unabhängige Tests
- [ ] Pi und Audio prüfen.
- [ ] GPIO-Tastendruck ohne Effektgeräte lesen.
- [ ] KORAD über USB erkennen und sichere Abfragen testen.
- [ ] KORAD-Schalten ohne LED / mit geeigneter Prüflast auf Latenz und Stromspitzen testen.
- [ ] Fingerbot-Tastendrücker ohne Nebelmaschine testen, zuverlässiges Loslassen prüfen.
- [ ] Nebel-Fernbedienung nur kurz und kontrolliert mechanisch auslösen.
- [ ] Art-Net-Gerät ansprechen und unkritische Lichtstimmung testen.

## Software
- [ ] Modulare Python-Struktur und Simulation.
- [ ] Zustandsautomat mit Sperrzeit und Abbruch.
- [ ] Konfigurierbare Timeline mit Audio und DMX.
- [ ] Nebel- und KORAD-Module nur nach Tests aktivieren.
- [ ] Sicherer Fehlerzustand und Logging.
- [ ] Optional Weboberfläche und mehrere Presets.

## Erfolgskriterien
Ein Druck startet höchstens eine Show, zusätzliche Drücke werden ignoriert, Fehler lassen Nebel nicht dauerhaft weiterlaufen, sichere Stop-Funktion funktioniert; keine unnötigen Risiken für Kinder.
