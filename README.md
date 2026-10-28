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
4. Während RUNNING/COOLDOWN werden weitere Tastendrücke ignoriert.
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

- **Roter Buzzer draußen:** löst genau **eine komplette Halloween-Show** mit den dafür freigegebenen Effekten aus. Weitere Tastendrücke während Show und Sperrzeit werden ignoriert.
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
