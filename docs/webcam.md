# Webcam am Eingang – lokaler Live-Stream

## Zweck

Eine vorhandene **Trust-USB-Webcam** soll den Eingangsbereich zeigen, damit man im Haus erkennen kann, **wann Halloween-Besucher eintreffen**. **Keine Bewegungserkennung, Gesichtserkennung oder automatische Showauslösung geplant.** Die Kamera ist unabhängig vom roten Buzzer (Hauptshow) und der Hama-Fernbedienung (spontane Sounds).

## Vorhandene Kamera

Auf zwei Fotos ist eine ältere schwarze Trust-Webcam mit Standfuß, Kabel und **sechs ringförmig um das Objektiv angeordneten LEDs** zu erkennen. Das exakte Modell, die Bildauflösung und die Art der LEDs (sichtbares Licht oder Infrarot) sind **noch unbekannt**. Es wurde noch kein erfolgreicher Raspberry-Pi-Test bestätigt. Die Kamera scheint nicht wetterfest; geschützt montieren, z. B. innerhalb des Hauses bzw. unter sicherem Wetterschutz.

## Architektur

- USB-Webcam am Raspberry Pi 4 Model B.
- Linux Video4Linux2 (V4L2) als mögliche Videoquelle.
- **FFmpeg** liest das Kamerabild, erzeugt HLS-Playlist und kurze Video-Segmente.
- **Nginx** stellt diese Dateien über HTTP **ausschließlich im Heimnetz** bereit.
- Ein Browser mit HLS-Unterstützung bzw. HLS.js oder ein geeigneter Player ruft den Stream auf.
- Keine Speicherung/Archivierung von Aufnahmen vorgesehen. HLS-Segmente nur flüchtig (z. B. RAM/tmpfs), begrenzte Aufbewahrung und regelmäßiges Entfernen alter Segmente.

## Streaming-Ziel

- Zunächst **640 × 480 Pixel, 15 fps, ohne Ton**, sofern die Webcam diesen Modus unterstützt.
- Kurze HLS-Segmente (als Ziel etwa 1 Sekunde) für möglichst geringe Verzögerung.
- **HLS hat trotzdem mehrere Sekunden Latenz**, je nach Encoder, Segmentgröße, Client und Browser; nicht als Echtzeitansicht mit garantiert sofortigem Bild behandeln.
- Wenn die Latenz zum rechtzeitigen Erkennen der Besucher zu groß ist, MJPEG oder WebRTC als Alternativen bewerten.
- Kamera-Encoderlast und Speicher-I/O dürfen die GPIO-/Audio-/Licht-/Nebel-Steuerung nicht beeinträchtigen. Dienste und Ressourcen getrennt halten.

## Noch zu testen

1. Kamera per USB anschließen und mit `lsusb` identifizieren.
2. Mit V4L2-Geräteauflistung prüfen, ob ein `/dev/video*`-Gerät erscheint.
3. Unterstützte Formate, Bildraten und Auflösungen ermitteln.
4. Testbild und Verhalten bei Abend-/Dämmerungslicht prüfen; Funktion der sechs LEDs feststellen.
5. FFmpeg-Aufnahme und CPU-Belastung auf dem Pi ermitteln.
6. Nginx/HLS-Konzept im LAN testen, Verzögerung messen und Browserkompatibilität prüfen.
7. Neustart-/Fehlerverhalten testen, sodass die Kamera die Halloween-Hauptshow nicht stört.

## Datenschutz und Netzwerksicherheit

- Nur **eigener Eingangsbereich**, keine Nachbargrundstücke oder öffentliche Gehwege erfassen; Bildausschnitt entsprechend begrenzen.
- Bei Überwachung von Besuchern, insbesondere Kindern, Transparenz und mögliche Hinweispflichten beachten.
- **Keine Videoaufzeichnung** und **keine Veröffentlichung des Streams im Internet**; keine Portfreigabe.
- Der Stream sollte auf vertrauenswürdige LAN-Geräte beschränkt werden, bei Bedarf mit Zugriffsschutz.

**Status:** Geplant und mit Fotos der vorhandenen Trust-Webcam konkretisiert; Kamera, FFmpeg und Nginx sind noch nicht als funktionierend bestätigt. Diese Datei ist ausschließlich Konzept- und Testdokumentation, **kein Implementierungscode**.
