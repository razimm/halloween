# Halloween 🎃 — Raspberry-Pi-Horrorshow

Projekt zur automatischen Halloween-Show am Hauseingang. Ein wettergeschützter Buzzer startet Musik, Nebel und verschiedene Lichteffekte. Der Raspberry Pi koordiniert alles.

**Stand 26.10.2026:** Erster Sound-/LED-Ablauf auf dem Pi erfolgreich getestet:
KORAD KKG305P über USB und Audio über Logitech G433. Die übrige Showintegration
ist noch offen. Halloween: 31.10.2026.

## Getesteten Sound-/LED-Ablauf starten

```bash
./setup.sh                    # Einmalig: lokale Python-Umgebung einrichten
./start-show.sh --simulate     # Ohne Gerätezugriff
sudo ./start-show.sh           # Einmal Sound + LED, danach automatisch aus
```

Die lokale WAV liegt unter `audio/electric-zap.wav`. Bei einem frischen Clone
siehe [Audio-Datei](audio/README.md). Der Start verwendet das Logitech-G433-Gerät,
10 V Spannungsgrenze, maximal 500 mA und 20 % Audio-Sample-Amplitude.
LED muss polrichtig angeschlossen sein und einen Kühlkörper haben.
Abbruch mit **Strg+C**. Details und Testergebnisse: [Sound-Synchronisation](docs/sound-sync.md).

## Ablauf
1. Kind drückt Buzzer am Eingang („Traust du dich? Drück mich!“).
2. Pi startet eine konfigurierbare, etwa 35 Sekunden lange Show.
3. Musik, DMX-Licht, Nebel und zusätzliche LED laufen zeitlich koordiniert.
4. Während RUNNING bleiben weitere Tastendrücke ohne Reaktion. Im COOLDOWN löst ein erneuter Druck ausschließlich eine gruselige Sprachansage „Noch nicht!“ aus – nie die Hauptshow.
5. Fehler oder Abbruch führen zu sicheren Ausgangszuständen.

## Technischer Überblick
| Gerät | Plan |
|---|---|
| Raspberry Pi 4 Model B Rev 1.4, 8 GB | Debian 13.4, aarch64; Python-Controller geplant |
| Roter Buzzer | Vorhanden; potentialfreier Schließer ausgemessen (offen / ca. 6 Ω gedrückt). GPIO17 vorgesehen. Startet **ausschließlich die vollständige automatische Show**. |
| Nebelmaschine mit Kabel-Fernbedienung | Mechanischer DS3218-Servo hält den Taster für einen begrenzten Nebelstoß gedrückt; unabhängig abschaltbar. |
| Miuzei DS3218 | Gewählter Servo statt SwitchBot; Pi-GPIO-PWM, separate 5-V-/3-A-Versorgung, Halterung und Rückstellung noch zu testen. |
| KORAD KKG305P | USB-Steuerung und Sound-/LED-Ablauf erfolgreich getestet |
| 10-W-Hochleistungs-LED | **Ohne eigene Stromregelung**; sichere Strombegrenzung erforderlich |
| Showtec NET-2/3 / Flat Par QA5X | Vorgesehene Art-Net/DMX-Lichtsteuerung; Bestand/Kanalmodus verifizieren |
| Audio | Logitech G433 USB für getesteten Sound-/LED-Ablauf; zusätzlicher HEOS 5 als geplanter Netzwerk-Soundplayer. |

## Zwei getrennte Bedienwege

- **Roter Buzzer draußen:** löst genau **eine komplette Halloween-Show** mit den dafür freigegebenen Effekten aus. Weitere Tastendrücke während der Show werden ignoriert; im Cooldown wird ausschließlich die Ansage „Noch nicht!“ ausgelöst (ohne Überlagerung).
- **Hama-USB-Fernbedienung:** dient **nur für zusätzliche spontane Einzel-Sounds** (z. B. Lachen, Donner, elektrisches Knistern) auf dem Denon HEOS 5; **startet weder die Hauptshow noch Nebel oder Lichteffekte**. Netzwerksteuerung und Tastenbelegung sind noch zu testen.

## Dateien
- [Hardware](docs/hardware.md)
- [Technische Architektur und Integrationen](docs/integrationen.md)
- [Show-Ideen](docs/show-ideen.md)
- [Roadmap](docs/roadmap.md)
- [Sicherheit und Tests](docs/sicherheit.md)
- [Sound-/LED-Ablauf und Startanleitung](docs/sound-sync.md)
- [Servo für die Nebelmaschine](docs/servo.md)
- [Hama-Soundboard und HEOS 5](docs/heos-soundboard.md)
- [Trust-Webcam / lokaler Nginx-HLS-Stream](docs/webcam.md)

## Eingangsbereich beobachten

Eine vorhandene Trust-USB-Webcam soll per FFmpeg und Nginx/HLS **nur im Heimnetz** ein Livebild des Eingangs liefern, damit Besucher rechtzeitig bemerkt werden. Keine Aufzeichnung, keine Personenerkennung und keine automatische Showauslösung durch die Kamera. Details: [Webcam-Konzept](docs/webcam.md).

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

## Rückmeldung während des Cooldowns

Keine grünen/roten Status-LEDs am Buzzer. Während die Show **RUNNING** ist, werden Tastendrücke still ignoriert. Im **COOLDOWN** bewirkt ein neuer Buzzer-Druck nur die gruselig gesprochene Audiodatei **„Noch nicht!“**. Solange die Ansage abgespielt wird, werden weitere Druckereignisse verworfen: **kein Neustart, kein Abschneiden, keine gleichzeitig abgespielten Instanzen, keine Warteschlange**. Nach Ende der Ansage kann ein weiterer Druck im weiterhin aktiven Cooldown die Ansage erneut auslösen. In **IDLE** startet der Buzzer wieder regulär die vollständige Show. Die Hama-Fernbedienung bleibt unabhängig für spontane HEOS-Sounds.
