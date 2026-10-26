# Hardware und Messdaten

## Bekannter Stand
- **Raspberry Pi:** vermutlich Pi 4 statt Pi 5. Modell prüfen mit `cat /proc/device-tree/model`; 64-Bit-System mit `uname -m` (`aarch64`). Pi 4 Model B hat BLE an Bord.
- **Buzzer:** noch auszuwählen; wettergeschützter, potentialfreier Taster auf sicherem 3,3-V-GPIO-Kreis.
- **Nebelmaschine:** vorhanden, kabelgebundene Fernbedienung. **Taster muss während des Nebelns gehalten werden.** Fernbedienung nicht öffnen; mechanischer Drücker erwünscht.
- **Fingerbot:** originaler Bluetooth SwitchBot Bot als Kandidat. Druckkraft, mechanische Passform, Haltemodus, Rückzug und lokale BLE-Ansteuerung vor Einsatz verifizieren.
- **KORAD KKG305P:** vorhandenes programmierbares Labornetzteil, über USB/serielle Verbindung zu testen.
- **10-W-LED:** vorhanden, nackte Hochleistungs-LED **ohne Stromregler**. Erst wurden 12 V und 900 mA genannt, später 10 V und 800 mA als geplante Einstellungen. Das sind **keine bestätigten LED-Nennwerte und nicht zwingend gemessene Ausgangswerte**.
- **DMX:** Showtec NET-2/3 Art-Net-Node und Flat Par QA5X als vorhandene Lichtprojekt-Geräte genannt; Anschluss/Kanalbelegung noch prüfen.
- **Audio:** Lautsprechertyp/Anschluss offen.

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
