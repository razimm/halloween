# Webcam am Eingang – lokaler Live-Stream

## Zweck

Eine vorhandene **Trust-USB-Webcam** soll den Eingangsbereich zeigen, damit man im Haus erkennen kann, **wann Halloween-Besucher eintreffen**. **Keine Bewegungserkennung, Gesichtserkennung oder automatische Showauslösung geplant.** Die Kamera ist unabhängig vom roten Buzzer (Hauptshow) und der Hama-Fernbedienung (spontane Sounds).

## Vorhandene Kamera

Auf zwei Fotos ist eine ältere schwarze Trust-Webcam mit Standfuß, Kabel und **sechs ringförmig um das Objektiv angeordneten LEDs** zu erkennen. Das exakte Handelsmodell und die Art der LEDs (sichtbares Licht oder Infrarot) sind **noch unbekannt**. USB-Erkennung und Bildempfang am Pi sind inzwischen bestätigt; Auflösungen und Testergebnisse stehen unten. Die Kamera scheint nicht wetterfest; geschützt montieren, z. B. innerhalb des Hauses bzw. unter sicherem Wetterschutz.

## Browseransicht starten

Im Heimnetz aufrufen: **http://192.168.178.130:8080/**
Alternativ bei funktionierender Namensauflösung: `http://raspi-server.local:8080/`.
Die IP-Adresse kann sich bei neuer DHCP-Zuweisung ändern.

Die Seite bietet Livebild, Verbindungsstatus, Vollbild und erneutes Verbinden.
Für Samsung-Smart-TVs oder Browser ohne MJPEG-Unterstützung:
**http://192.168.178.130:8080/?mode=tv** (auch über die Schaltfläche TV-Modus).
Dieser Modus lädt jeweils ein aktuelles JPEG und zeigt es erst nach komplettem
Laden an; das vorherige Bild bleibt bis dahin sichtbar. Es gibt höchstens einen
laufenden Bildabruf, der nächste folgt frühestens 100 ms nach dessen Abschluss.
Keine Video-Warteschlange; bei langsamen TVs sinkt stattdessen die Bildrate.
Gängige Samsung-TV-Kennungen wählen diesen Modus automatisch.
Der Laptop kann mit `?mode=stream` ausdrücklich MJPEG verwenden.

Das Seitenskript verwendet ES5 und XMLHttpRequest statt async/await, fetch
oder AbortSignal.timeout, da TV-Browser je nach Baujahr ältere Engines nutzen.
Siehe [Samsung Web Engine Specifications](https://developer.samsung.com/smarttv/develop/specifications/web-engine-specifications.html).
Der JPEG-Endpunkt `/snapshot.jpg` liefert das aktuelle Bild ohne Speicherung
und mit deaktiviertem HTTP-Caching. TV-Darstellung vor Ort noch zu bestätigen.
Nach Kameraausfall wird ein altes Bild verdeckt; bei Rückkehr wird neu verbunden.
Andere Geräte im vertrauenswürdigen LAN können ohne Anmeldung zugreifen.

Der installierte Dienst `halloween-webcam.service` startet automatisch beim Booten:

```bash
systemctl status halloween-webcam
sudo systemctl stop halloween-webcam
sudo systemctl start halloween-webcam
sudo systemctl restart halloween-webcam
journalctl -u halloween-webcam -n 30 --no-pager
```

Manueller Start (vorher den Dienst stoppen, da die Kamera nur einmal geöffnet wird):

```bash
./start-webcam.sh
./start-webcam.sh --host 127.0.0.1 --port 8081 --fps 15
```

Voraussetzungen: Python 3, FFmpeg mit V4L2/MJPEG und Zugriff auf die Kamera
(Gruppe `video`). Keine weiteren Python-Pakete erforderlich.
Standardgerät ist der stabile `/dev/v4l/by-id/`-Pfad der vorhandenen Trust-Webcam;
mit `--device` kann eine andere passende YUYV-Kamera angegeben werden.
Die Auflösung beträgt 640 × 480, angefordert werden 15 fps.

## Architektur und geringe Verzögerung

**V4L2 → FFmpeg → JPEG im Arbeitsspeicher → HTTP/MJPEG → Browser.**

MJPEG ersetzt den ursprünglichen HLS-/Nginx-Plan, weil geringe Verzögerung
wichtiger ist als sparsame Bandbreite. Es gibt keine HLS-Segmente oder
Video-/Bilddateien und keine Ablage unter `/tmp`. Kein Mikrofon wird geöffnet.

- Eine einzige Kamera-/Encoderinstanz für alle Zuschauer.
- Nur das jeweils neueste Bild bleibt im Speicher; langsame Zuschauer
  überspringen alte Bilder statt eine Bildwarteschlange anzusammeln.
- Ein Encoder-Thread begrenzt die CPU-Last; sofortige Paket-Ausgabe und
  deaktiviertes HTTP-Caching vermeiden zusätzliche Puffer.
- Die Kamera liefert teilweise doppelte Zeitstempel. `setpts` nummeriert
  Bilder zeitlich neu, ohne sie für eine FPS-Konvertierung zurückzuhalten.
- Nach fünf Sekunden ohne Daten oder nach FFmpeg-Ausfall wird die Kamera
  erneut geöffnet. Nach drei Sekunden ohne aktuelles Bild wird sie offline gemeldet.
- Der Server bindet standardmäßig IPv4 auf Port 8080. Keine Änderungen an
  Radio-Diensten, Nginx oder Router-Portfreigaben.

Der HTTP-Dienst läuft getrennt von der Showsteuerung. MJPEG braucht mehr
Netzwerkbandbreite als H.264. Tatsächliche Verzögerung hängt auch von
Kamerabelichtung, WLAN und Browser ab; sie ist noch nicht Ende zu Ende gemessen.

## Noch zu testen

1. Bildqualität bei Abend-/Dämmerungslicht und Funktion der sechs LEDs.
2. Sichtbare Verzögerung mit Bewegung vor der Kamera im tatsächlichen Browser.
3. Dauerbetrieb mit paralleler Show und vorgesehenen WLAN-Geräten.
4. Physisches Abziehen und Wiederanschließen der Kamera.

## Installation auf einem frischen Pi

Die Dienstvorlage ist für den aktuellen Benutzer `brain` und Projektpfad ausgelegt;
auf anderen Systemen `User` und Pfade vorher anpassen.

```bash
sudo install -m 644 infra/halloween-webcam.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now halloween-webcam
```

## Datenschutz und Netzwerksicherheit

- Nur **eigener Eingangsbereich**, keine Nachbargrundstücke oder öffentliche Gehwege erfassen; Bildausschnitt entsprechend begrenzen.
- Bei Überwachung von Besuchern, insbesondere Kindern, Transparenz und mögliche Hinweispflichten beachten.
- **Keine Videoaufzeichnung** und **keine Veröffentlichung des Streams im Internet**; keine Portfreigabe.
- Der Stream sollte auf vertrauenswürdige LAN-Geräte beschränkt werden, bei Bedarf mit Zugriffsschutz.

## Gerätetest am 28.10.2026

- USB-ID **`0c45:6340`**, USB-Bezeichnung Microdia Camera; V4L2 meldet
  **Trust Webcam**, Treiber `uvcvideo`.
- Bildgerät beim Test `/dev/video0`, zusätzlich Metadaten-Gerät `/dev/video1`.
- Format **YUYV**; 640 × 480 mit 5/10/15/20/25/30 fps wird angeboten.
  1280 × 960 und 1280 × 1024 werden mit 5 oder 9 fps angeboten.
- FFmpeg konnte Bilder bei angeforderten 640 × 480 / 15 fps lesen.
  Ohne Normalisierung meldete die Kamera doppelte/nicht monotone Zeitstempel.
  Ein zweiter Test mit `-vf fps=15` lief ohne Warnungen durch.
- Beide kurzen Tests verwarfen alle Bilder direkt; keine Bild-/Videodateien,
  kein Ton und kein Netzwerkstream wurden erzeugt.
- Bildqualität, Dunkelheit, LED-Funktion, tatsächliche Live-Latenz und
  dauerhaft stabiler Betrieb sind noch zu prüfen.

**Status:** USB-/V4L2-Erkennung und FFmpeg-Bildempfang erfolgreich getestet.
Browseransicht per MJPEG ist eingerichtet und als systemd-Dienst aktiviert.
Zwei gleichzeitige HTTP-Zuschauer erhielten jeweils 30 vollständige JPEG-Bilder
in etwa 1,7 Sekunden; die LAN-Startseite antwortete mit HTTP 200.
Die Kamera lieferte im Test mehr Bilder als die angeforderten 15 fps.
Dies misst den Bilddurchsatz, nicht die Verzögerung zwischen Szene und Bildschirm.
Eine visuelle Browserprüfung steht noch aus.

Ein gestreamtes JPEG wurde erfolgreich dekodiert. Nach gezieltem Beenden
des Kamera-FFmpeg-Prozesses lief der Bildempfang automatisch wieder an.
Eine kurze Messung ergab etwa 10 % eines CPU-Kerns für den gesamten Dienst;
Last bei weiteren Zuschauern und paralleler Show kann abweichen.

FFmpeg-Optionen: [V4L2-Geräteparameter](https://ffmpeg.org/ffmpeg-devices.html#video4linux2_002c-v4l2)
und [sofortiges Flushen von Paketen](https://ffmpeg.org/ffmpeg-all.html).
