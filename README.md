# Halloween 🎃 — Raspberry-Pi-Horrorshow

Projekt zur automatischen Halloween-Show am Hauseingang. Ein wettergeschützter Buzzer startet Musik, Nebel und verschiedene Lichteffekte. Der Raspberry Pi koordiniert alles.

**Stand 26.10.2026:** Ideen und Entwurf; Hardware- und Softwareintegration noch nicht abgeschlossen. Halloween: 31.10.2026.

## Ablauf
1. Kind drückt Buzzer am Eingang („Traust du dich? Drück mich!“).
2. Pi startet eine konfigurierbare, etwa 35 Sekunden lange Show.
3. Musik, DMX-Licht, Nebel und zusätzliche LED laufen zeitlich koordiniert.
4. Während RUNNING/COOLDOWN werden weitere Tastendrücke ignoriert.
5. Fehler oder Abbruch führen zu sicheren Ausgangszuständen.

## Technischer Überblick
| Gerät | Plan |
|---|---|
| Raspberry Pi (wahrscheinlich Pi 4) | Python-Controller mit GPIO, BLE, USB, Art-Net und Audio |
| Buzzer | GPIO-Eingang, 3,3 V, wetterfest |
| Nebelmaschine mit Kabel-Fernbedienung | Mechanischer Bluetooth-Tastendrücker, der den Taster **gedrückt hält** |
| SwitchBot Bot | Möglicher Fingerbot; noch nicht als gekauft bestätigt; Langdruck/BLE testen |
| KORAD KKG305P | USB-steuerbares Labornetzteil für Zusatz-LED; erst testen |
| 10-W-Hochleistungs-LED | **Ohne eigene Stromregelung**; sichere Strombegrenzung erforderlich |
| Showtec NET-2/3 / Flat Par QA5X | Vorgesehene Art-Net/DMX-Lichtsteuerung; Bestand/Kanalmodus verifizieren |
| Lautsprecher | Audio/Musik, Anschluss noch offen |

## Dateien
- [Hardware](docs/hardware.md)
- [Technische Architektur und Integrationen](docs/integrationen.md)
- [Show-Ideen](docs/show-ideen.md)
- [Roadmap](docs/roadmap.md)
- [Sicherheit und Tests](docs/sicherheit.md)

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
