# Hardware und Messdaten

## Bekannter Stand
- **Raspberry Pi:** bestätigt: Pi 4 Model B Rev 1.4, 8 GB, Debian 13.4 (trixie), aarch64, Kernel `6.12.75+rpt-rpi-v8`, Host `raspi-server`.
- **Buzzer:** noch auszuwählen; wettergeschützter, potentialfreier Taster auf sicherem 3,3-V-GPIO-Kreis.
- **Nebelmaschine:** vorhanden, kabelgebundene Fernbedienung. **Taster muss während des Nebelns gehalten werden.** Fernbedienung nicht öffnen; mechanischer Drücker erwünscht.
- **Fingerbot:** originaler Bluetooth SwitchBot Bot als Kandidat. Druckkraft, mechanische Passform, Haltemodus, Rückzug und lokale BLE-Ansteuerung vor Einsatz verifizieren.
- **KORAD KKG305P:** USB-Steuerung bestätigt, Firmware V1.3. USB-ID `0416:5011`, Nuvoton Virtual COM, `/dev/ttyACM0`; stabiler Pfad `/dev/serial/by-id/usb-Nuvoton_USB_Virtual_COM_001C1A770452-if00`. Protokoll: 9600 Baud, 8N1, keine Flusssteuerung, LF-Zeilenabschluss. Details: [Testprotokoll](sound-sync.md).
- **10-W-LED:** vorhanden, nackte Hochleistungs-LED **ohne Stromregler**. Erst wurden 12 V und 900 mA genannt, später 10 V und 800 mA als geplante Einstellungen. Das sind **keine bestätigten LED-Nennwerte und nicht zwingend gemessene Ausgangswerte**.
- **DMX:** Showtec NET-2/3 Art-Net-Node und Flat Par QA5X als vorhandene Lichtprojekt-Geräte genannt; Anschluss/Kanalbelegung noch prüfen.
- **LED-Kühlung:** Kühlkörper laut Benutzer montiert. 10 V / 900 mA wurden vom Benutzer als bisherige maximale Betriebswerte genannt, nicht als bestätigte Nennwerte.
- **Audio:** Logitech G433 USB, Klinkenanschluss am Logitech-Gerät; ALSA `plughw:CARD=Headset,DEV=0`. Gemeinsame Sound-/LED-Wiedergabe vom Benutzer bestätigt.

## Konzeptioneller Aufbau
```text
Buzzer --> Pi GPIO
               |-- Bluetooth LE --> mechanischer Fingerbot --> Nebel-Fernbedienung
               |-- USB/seriell --> KORAD --> 10-W-LED
               |-- Ethernet/Art-Net --> DMX-Node --> LED-PAR
               '-- Audio --> Aktivlautsprecher
```

## Zu prüfen
1. Pi-Modell, Raspberry Pi OS, Bluetooth (`bluetoothctl show`).
2. Modell und Foto der Nebel-Fernbedienung; Tastenkraft, maximal sinnvolle Haltezeit.
3. LED-Datenblatt (Vorwärtsspannung, **zulässiger** Strom), Kühlkörper.
4. KORAD: unter Last **CC oder CV?** Welche tatsächliche Ausgangsspannung und welcher Strom?
5. Bei USB: `lsusb` und `ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null`.
6. DMX-IP, Universum, Startadresse und Kanalmodus.
7. Audioausgabe sowie wetterfeste/zugentlastete Montage.
