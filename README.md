# Halloween 🎃 — Raspberry-Pi-Horrorshow

Projekt zur automatischen Halloween-Show am Hauseingang. Ein wettergeschützter Buzzer startet Musik, Nebel und verschiedene Lichteffekte. Der Raspberry Pi koordiniert alles.

**Stand 29.10.2026:** Vollständiger Showcontroller mit Simulation, Hama-Freigabe,
KORAD-LED und Art-Net implementiert. Der gemeinsame Hardwaretest steht noch aus.

## Start

```bash
./setup.sh
./start-show.sh --demo          # Vollständiger simulierter Ablauf, ohne Hardware/Ton
./start-show.sh --simulate      # b = Buzzer, 1 = Freigabe, p = KORAD (je + Enter), q = Ende
sudo ./start-show.sh --play     # Echte Hardware; Idle beginnt mit Musik und Licht
```

Hintergrundmusik läuft im Idle als Loop mit **15 % Sample-Amplitude**, einstellbar
über `background_gain` in `config/show.json` oder `--background-gain 0.15`.
Die KORAD-LED leuchtet im Idle mit 300 mA, der Flat Par zeigt Grün mit 5 %.
Die Show verwendet bis zu 700 mA und 100 % Flat-Par-Helligkeit; Show-Audio und
Ansagen laufen mit 100 % Originalamplitude, Kirchenglocke mit 75 % und Lachen mit 40 %,
Michael Myers mit 98 % Spitzenpegel. Die Spannungsgrenze bleibt bei 10 V.
LED auf Kühlkörper und polrichtig anschließen. Abbruch mit **Strg+C**.
Details: [Showablauf und Konfiguration](docs/show.md).

## Ablauf

1. Buzzer stoppt die Hintergrundmusik und startet `electric-zap_break_final.mp3`.
   Die KORAD-LED flackert und blendet in den letzten 0,5 Sekunden aus; sie ist zum Soundende aus. Ein früher weißer PAR-Impuls blendet über 0,5 Sekunden aus
   und endet bereits 0,5 Sekunden vor Soundende; anschließend folgt eine Sekunde Pause.
2. `church_bell_final.mp3`: drei orange PAR-Lichtimpulse mit 100 % auf den Gongs; KORAD bleibt aus.
3. `michael_myers_final.mp3` mit Flat-Par-Lichtfolge über Art-Net.
4. `laughing.wav`, danach gesperrt: KORAD-LED aus, Flat Par rot. Nach fünf Sekunden läuft die Hintergrundmusik wieder im Loop.
5. Buzzer während der Sperre: dreimal rot blinken und eine zufällige Voice-Datei
   vollständig abspielen; weitere Drücke währenddessen werden verworfen.
6. Hama-Taste **1** gibt wieder frei: Grün und KORAD-LED blenden über zwei Sekunden auf. Eine laufende
   Ansage endet zuerst, dann starten Hintergrundmusik und Buzzer-Bereitschaft.

Kein automatischer Cooldown-Timer. Nebel/Servo sind noch nicht eingebunden.

## Technischer Überblick
| Gerät | Plan |
|---|---|
| Raspberry Pi 4 Model B Rev 1.4, 8 GB | Debian 13.4, aarch64; Python-Showcontroller implementiert |
| Roter Buzzer | Vorhanden; potentialfreier Schließer ausgemessen (offen / ca. 6 Ω gedrückt). GPIO17 vorgesehen. Startet **ausschließlich die vollständige automatische Show**. |
| Nebelmaschine mit Kabel-Fernbedienung | Mechanischer DS3218-Servo hält den Taster für einen begrenzten Nebelstoß gedrückt; unabhängig abschaltbar. |
| Miuzei MS24-UF | Gewählter Servo statt SwitchBot; Pi-GPIO-PWM, separate 5-V-/3-A-Versorgung, Halterung und Rückstellung noch zu testen. |
| KORAD KKG305P | USB-Steuerung und Sound-/LED-Ablauf erfolgreich getestet |
| 10-W-Hochleistungs-LED | **Ohne eigene Stromregelung**; sichere Strombegrenzung erforderlich |
| Showtec NET-2/3 / Flat Par QA5X | Art-Net an 192.168.178.146, Universe 1, A.001 / Ch.07 |
| Audio | Logitech G433 USB für getesteten Sound-/LED-Ablauf; zusätzlicher HEOS 5 als geplanter Netzwerk-Soundplayer. |

## Bedienung

- **Roter Buzzer:** startet eine vollständige Show im freigegebenen Idle. Während
  der Show ignoriert, bei Sperre nur Blink-/Voice-Rückmeldung.
- **Hama-OFF:** Panic-Stopp: lokales Audio und HEOS stoppen, PAR aus, KORAD auf 300 mA.
  Buzzer, OK und Play bleiben gesperrt.
- **Hama-Taste 1:** Freigabe nach Showende oder Panic; startet normalen Idle-Betrieb, keine Show.
- **Hama-Taste 2:** „Show fertig“: KORAD aus, PAR rot, Show gesperrt; Hintergrundloop nach fünf Sekunden.
- **Hama-Play/Pause:** KORAD im gesperrten Zustand an/aus; Einschalten mit
  `electric-zap_up_final.mp3` und Strommodulation, danach 300 mA. Keine Showfreigabe.
- **Hama-OK:** Lachen auf HEOS_Kueche über das Heimnetz, mit 10 % Lautstärke.
- **Weitere Hama-Tasten:** noch nicht belegt.

## Dateien

- [Vollständige Show: Bedienung, Einstellungen und Gerätetest](docs/show.md)
- [Hardware](docs/hardware.md)
- [Technische Architektur und Integrationen](docs/integrationen.md)
- [Show-Ideen](docs/show-ideen.md)
- [Roadmap](docs/roadmap.md)
- [Sicherheit und Tests](docs/sicherheit.md)
- [Sound-/LED-Ablauf und Startanleitung](docs/sound-sync.md)
- [Servo für die Nebelmaschine](docs/servo.md)
- [Hama-Soundboard und HEOS 5](docs/heos-soundboard.md)
- [Trust-Webcam / lokale Browseransicht](docs/webcam.md)

## Eingangsbereich beobachten

Die Trust-USB-Webcam liefert per FFmpeg/MJPEG **im Heimnetz** eine Browseransicht mit geringer Pufferung: **http://192.168.178.130:8080/**. Der Dienst `halloween-webcam` startet automatisch mit dem Pi. Keine Aufzeichnung, keine Personenerkennung und keine automatische Showauslösung durch die Kamera. Details: [Webcam-Konzept](docs/webcam.md).

## Entwicklungsstrategie
Zuerst jedes Gerät einzeln erkennen und gefahrlos testen. Danach eine Python-Zustandsmaschine mit Simulationsmodus und Timeline aufbauen. Später optional eine lokale Weboberfläche für Shows, Lautstärke und Testfunktionen.

```bash
git clone https://github.com/razimm/halloween.git
cd halloween
cat /proc/device-tree/model
uname -m
bluetoothctl show
```

Die Halloween-Titelmelodie (John Carpenter/Michael Myers) ist musikalische Inspiration. Keine geschützten Audiodateien ins Repository aufnehmen; Rechte für die Nutzung klären.

## Softwaretests

`./test.sh` führt alle Tests aus. Bei Erfolg bleibt die Ausgabe leer; bei Fehlern
erscheint das Testprotokoll und der Aufruf liefert einen Fehlerstatus.
