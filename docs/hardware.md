# Hardware und Messdaten

## Bekannter Stand
- **Raspberry Pi:** bestätigt: Pi 4 Model B Rev 1.4, 8 GB, Debian 13.4 (trixie), aarch64, Kernel `6.12.75+rpt-rpi-v8`, Host `raspi-server`.
- **Roter Buzzer:** vorhanden; Kontaktpaar mit Multimeter identifiziert: ungedrückt unendlicher Widerstand, gedrückt etwa 6 Ω. Für einen internen Pull-up an GPIO17 (physischer Pin 11) und GND (Pin 9) vorgesehen. Nur zum Start der vollständigen Show; Außenschutz noch prüfen.
- **Nebelmaschine:** vorhanden, kabelgebundene Fernbedienung. **Taster muss während des Nebelns gehalten werden.** Fernbedienung nicht öffnen; mechanischer Drücker erwünscht.
- **Servo für Nebel:** **Miuzei DS3218** als mechanische Lösung ausgewählt, **kein SwitchBot**. Vorgesehen: GPIO18 (Pin 12) PWM-Signal; separate, ausreichend dimensionierte 5-V-/3-A-Stromversorgung; gemeinsame Masse (z. B. Pin 14). Montage, Druckweg, Federrückstellung und sichere Freigabe noch zu prüfen.
- **KORAD KKG305P:** USB-Steuerung bestätigt, Firmware V1.3. USB-ID `0416:5011`, Nuvoton Virtual COM, `/dev/ttyACM0`; stabiler Pfad `/dev/serial/by-id/usb-Nuvoton_USB_Virtual_COM_001C1A770452-if00`. Protokoll: 9600 Baud, 8N1, keine Flusssteuerung, LF-Zeilenabschluss. Details: [Testprotokoll](sound-sync.md).
- **10-W-LED:** vorhanden, nackte Hochleistungs-LED **ohne Stromregler**. Erst wurden 12 V und 900 mA genannt, später 10 V und 800 mA als geplante Einstellungen. Das sind **keine bestätigten LED-Nennwerte und nicht zwingend gemessene Ausgangswerte**.
- **DMX:** Showtec NET-2/3 Art-Net-Node und Flat Par QA5X als vorhandene Lichtprojekt-Geräte genannt; Anschluss/Kanalbelegung noch prüfen.
- **LED-Kühlung:** Kühlkörper laut Benutzer montiert. 10 V / 900 mA wurden vom Benutzer als bisherige maximale Betriebswerte genannt, nicht als bestätigte Nennwerte.
- **Audio:** Logitech G433 USB, Klinkenanschluss am Logitech-Gerät; ALSA `plughw:CARD=Headset,DEV=0`. Gemeinsame Sound-/LED-Wiedergabe vom Benutzer bestätigt.
- **Hama-Multimedia-Fernbedienung:** vorhanden, mit kleinem rotem USB-Empfänger; als separate Steuerung für spontane Sounds vorgesehen. Eingabecodes am Pi noch nicht ermittelt.
- **Denon HEOS 5:** im gleichen Heimnetz, laut Benutzer bereits über HEOS-App bedienbar. Geplante Wiedergabe von Einzel-Sounds über HEOS-Netzwerksteuerung; USB-Stick am HEOS als mögliche Medienquelle noch testen.

- **Webcam:** ältere Trust-USB-Webcam mit Standfuß und sechs LEDs um das Objektiv auf Fotos bestätigt. Exaktes Modell, V4L2-Unterstützung, Auflösung und LED-Typ offen. Geplant als reine LAN-Livebildquelle am Eingang; Nginx/HLS, ohne Aufnahme.

## Konzeptioneller Aufbau
```text
Buzzer --> Pi GPIO
               |-- GPIO18/PWM --> DS3218-Servo --> Nebel-Fernbedienung
               |-- USB/seriell --> KORAD --> 10-W-LED
               |-- Ethernet/Art-Net --> DMX-Node --> LED-PAR
               |-- USB-Audio --> Logitech G433 (Show-Audio)
               '-- LAN/WLAN --> HEOS 5 (spontane Sounds)
Hama-USB-Empfänger --> Pi --> nur spontane Sounds auf HEOS 5
```

## Zu prüfen
1. Mechanische Montage und sichere Stromversorgung des DS3218; GPIO-Ausgabe und Rückstellung prüfen.
2. Nebel-Fernbedienung: Tastenkraft, maximal sinnvolle Haltezeit und freie Rückstellung bestimmen.
3. LED-Datenblatt (Vorwärtsspannung, **zulässiger** Strom), Kühlkörper.
4. KORAD: unter Last **CC oder CV?** Welche tatsächliche Ausgangsspannung und welcher Strom?
5. Bei USB: `lsusb` und `ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null`.
6. DMX-IP, Universum, Startadresse und Kanalmodus.
7. Hama-Empfänger und Tastenereignisse prüfen; HEOS-IP und USB-Mediennavigation ermitteln; wetterfeste/zugentlastete Montage.

## Buzzer-Statusanzeige (neu geplant)

Zwei **bereits vorhandene, normale diskrete LEDs** am Hauseingang sollen den Besuchern anzeigen, ob der rote Buzzer eine Show starten kann. Keine zusätzlichen Netzteile für die LEDs vorgesehen.

| Zustand | Grün | Rot | Buzzer |
| --- | --- | --- | --- |
| IDLE / bereit | Dauerhaft an | Aus | Start erlaubt |
| RUNNING / Show läuft | Aus | Dauerhaft an | Weitere Tastendrücke ignorieren |
| COOLDOWN | Aus | Langsam blinkend | Weitere Tastendrücke ignorieren |
| ERROR / Initialisierung | Aus | Fehleranzeige (noch festzulegen) | Gesperrt |

**Vorgesehene GPIOs:** grün GPIO22 (physischer Pin 15), rot GPIO23 (Pin 16), beide Kathoden an GND (z. B. physischer Pin 20). Jede LED erhält **einen eigenen Vorwiderstand von zunächst 470 Ω** in Reihe an der 3,3-V-GPIO-Seite. Gilt für gewöhnliche Einzel-LEDs; Polarität und Vorwärtsspannung vor Anschluss prüfen. Kein GPIO darf mit externer Spannung gespeist werden. Bei längeren Außenleitungen Störschutz, Wetterfestigkeit und mechanische Zugentlastung berücksichtigen.

**Zustandslogik:** LEDs zeigen den tatsächlichen Status der zentralen Show-Zustandsmaschine, nicht nur einen Zeitplan. Grün darf erst leuchten, wenn die Show wirklich startbereit ist. Nach Boot/Crash zunächst keine falsche grüne Bereitschaft signalisieren. Der Buzzer bleibt der **einzige Startauslöser für die vollständige Show**; die Hama-Fernbedienung bleibt ausschließlich für spontane Einzel-Sounds. Noch nicht implementiert, Umsetzung mit Codex.
