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
| Buzzer | GPIO-Eingang, 3,3 V, wetterfest |
| Nebelmaschine mit Kabel-Fernbedienung | Mechanischer Bluetooth-Tastendrücker, der den Taster **gedrückt hält** |
| SwitchBot Bot | Möglicher Fingerbot; noch nicht als gekauft bestätigt; Langdruck/BLE testen |
| KORAD KKG305P | USB-Steuerung und Sound-/LED-Ablauf erfolgreich getestet |
| 10-W-Hochleistungs-LED | **Ohne eigene Stromregelung**; sichere Strombegrenzung erforderlich |
| Showtec NET-2/3 / Flat Par QA5X | Vorgesehene Art-Net/DMX-Lichtsteuerung; Bestand/Kanalmodus verifizieren |
| Audio | Logitech G433 USB, Klinkenanschluss am Logitech-Gerät getestet |

## Dateien
- [Hardware](docs/hardware.md)
- [Technische Architektur und Integrationen](docs/integrationen.md)
- [Show-Ideen](docs/show-ideen.md)
- [Roadmap](docs/roadmap.md)
- [Sicherheit und Tests](docs/sicherheit.md)
- [Sound-/LED-Ablauf und Startanleitung](docs/sound-sync.md)

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
