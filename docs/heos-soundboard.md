# Hama-OK-Taste und HEOS-Küchenlautsprecher

## Aktueller Betrieb

Die **OK-Taste** der Hama spielt `audio/laughing.wav` auf **HEOS_Kueche** ab.
Die Datei wird einmalig als MP3 nach `audio/playback/` konvertiert und vom Pi
über HTTP bereitgestellt. Ein USB-Stick und Internetzugang sind dafür nicht nötig.

Bestätigt am 30.10.2026:

- Küche: Modell **HEOS 5**, IP **192.168.178.30**, Player-ID **1491570931**.
- Zweiter Player: Denon AVR-X3400H (`192.168.178.26`); erhält keine Wiedergabe-
  oder Lautstärkebefehle.
- Küchenlautstärke vor jedem Effekt: **10 %** über die HEOS-Lautstärkeregelung.
- MP3-Abruf und Wiedergabeende wurden technisch bestätigt; der Benutzer hat
  das Lachen auf dem Küchenlautsprecher gehört.
- OK am Hama-Empfänger: **KEY_ENTER, Code 28**, am 30.10.2026 eingelesen.

Der Effekt ist unabhängig von Show, Buzzer und lokaler Audiowiedergabe. OK ist
auch während der Hauptshow nutzbar, beeinflusst weder KORAD noch PAR und gibt
die Show nicht frei. Die Lautstärke der lokalen Show bleibt unverändert:
Das dortige `laugh_gain: 0.6` gilt nur für den lokalen Ausgang. HEOS verwendet
hier das Original mit eigener Lautstärke 10 %.

## Tasten und Mehrfachdrücke

| Taste | Funktion |
| --- | --- |
| 1 / KEY_KP1 (79) | Show nach Ende freigeben |
| Play/Pause / KEY_PLAYPAUSE (164) | KORAD während Sperre manuell an/aus |
| OFF / KEY_SLEEP (142) | Panic: alle Effekte stoppen, bis Taste 1 wieder freigibt |
| OK / KEY_ENTER (28) | Einmal Lachen auf HEOS_Kueche |
| Übrige Tasten | Noch nicht belegt |

Während eines HEOS-Effekts werden weitere OK-Drücke verworfen: kein Neustart,
keine Warteschlange. Die Sperre endet mit dem tatsächlichen UPnP-Transportzustand
STOPPED nach PLAYING, ohne geschätzte Soundlängen-Sperre oder zusätzliche Puffer.
Verspätet eingelesene OK-Ereignisse aus der laufenden Wiedergabe werden anhand
ihres Ereigniszeitpunkts verworfen. Läuft der eigene Titel nach einem
Verbindungsabbruch noch, wird ein neuer Aufruf verworfen, ohne einen Neustart
vorzumerken. Loslassen, Wiederholung und NumLock werden ignoriert.

Die Hama-USB-Schnittstellen werden nach USB-ID **05a4:9881** und Tastencodes
gefunden; wechselnde `/dev/input/event*`-Nummern sind kein Problem.

## Architektur und Einstellungen

Die Datei wird als **endlicher UPnP-Musiktitel** über AVTransport geladen
(SetAVTransportURI mit Titelmetadaten und NORMAL-Modus), nicht über den HEOS-
CLI-Befehl Play URL. Am HEOS_Kueche wurde gemessen, dass Play URL die MP3 selbst
immer wieder abrief, obwohl nur ein Startbefehl gesendet wurde. Das war keine
Tasten-Warteschlange. Der Vergleichstest mit UPnP ergab fünf OK-Drücke, einen
Start, einen Dateiabruf und selbstständiges Wiedergabeende ohne Wiederholung.
HEOS-CLI-Zwischenantworten „command under process“ werden nun ebenfalls
korrekt als Zwischenantwort behandelt.

`tools/heos.py` betreibt einen eigenen HTTP-Server und einen eigenen
Wiedergabe-Thread. Netzwerkabfragen blockieren den Showcontroller nicht.
Ein HEOS-Ausfall wird protokolliert; die lokale Hauptshow läuft weiter.
Bei einem belegten HTTP-Port wird das Soundboard beim Start deaktiviert und
dies im Terminal angezeigt.

`config/show.json` enthält unter `heos` Ziel-IP, Player-ID, Playername,
Lautstärke, lokale Pi-Adresse und HTTP-Port. `remote_heos_key` ist 28.

Die einzige freigegebene Audio-URL lautet:

```text
http://192.168.178.130:8081/laugh.mp3
```

HTTP unterstützt GET, HEAD und Byte-Range-Abrufe. Andere Pfade werden nicht
bereitgestellt. Webcam-Port 8080 und Show-Audio bleiben unabhängig.
Die WLAN-/LAN-IP-Adressen sollten in der Fritzbox dauerhaft zugeordnet bleiben.

Vor einer Wiedergabe wird die konfigurierte Player-Identität abgeglichen.
Bei Gruppierung mit anderen HEOS-Geräten wird der Effekt abgelehnt, damit
keine weiteren Lautsprecher mitspielen. Dann die Küche zuerst in der HEOS-App
entgruppieren. Repeat und Shuffle werden nur für den Küchenplayer ausgeschaltet.

Zum separaten, ausdrücklich hörbaren Test:

```bash
.venv/bin/python -m tools.heos --test
```

Dabei darf der HTTP-Port nicht gleichzeitig vom laufenden Showcontroller
belegt sein. Im normalen Betrieb genügt `sudo ./start-show.sh --play` und OK.
In der Simulation löst `o` + Enter einen protokollierten HEOS-Effekt ohne
Netzwerkzugriff aus.

## Standby

Der HEOS 5 geht nach etwa 20 Minuten ohne Wiedergabe/Netzwerkaktivität in den
Netzwerk-Standby und wacht bei Auswahl und Wiedergabe automatisch wieder auf.
Das Soundboard öffnet für jeden Effekt eine neue CLI-Verbindung; eine alte,
zwischenzeitlich abgebrochene Verbindung wird nicht wiederverwendet.
Eine Wiedergabe nach mehr als 20 Minuten Ruhe wurde noch nicht separat geprüft.

Bei über 60 Minuten verlorener Netzwerkverbindung kann Deep Standby eintreten.
Dann ist keine Netzwerksteuerung möglich; Aufwecken am Lautsprecher über Lautstärke
oder Mute. Es wird kein stiller Dauerstream zur Standby-Vermeidung erzeugt.

Quellen: [Denon HEOS CLI](https://assets.denon.com/DocumentMaster/us/HEOS_CLI_ProtocolSpecification-Version.pdf),
[HEOS-5-Handbuch](https://www.denon.com/on/demandware.static/-/Library-Sites-denon_apac_shared/default/dw9c353db9/downloads/archived/heos-3-5-7-owners-manual-en.pdf),
[Deep Standby](https://manuals.denon.com/HEOS753/ALL/en/PCIRSYcfocmihq.php).

## Verbindliche Vorgaben für neue Sounds

Diese Regeln gelten für **jede neue HEOS-Datei und jede neue Soundtaste**:

1. Datei in ein vom HEOS abspielbares Format bringen. Audiodauer und Größe
   pro Datei ermitteln; die Werte des Lachens nicht für andere Sounds übernehmen.
2. Eine eindeutige Audio-URL und passende DIDL-Lite-Titelmetadaten bereitstellen:
   `object.item.audioItem.musicTrack`, MIME-Typ, Ressource, Dauer und Dateigröße.
3. Ausschließlich endliche Titelwiedergabe über `Renderer.load_track()` /
   AVTransport mit NORMAL-Modus verwenden. Kein Play URL / `browse/play_stream`
   für diese Einzel-Sounds: Das hat am Küchen-HEOS zu selbstständiger Wiederholung
   geführt, obwohl nur ein Startbefehl gesendet wurde.
4. Alle Soundtasten desselben Players verwenden eine **gemeinsame Sperre**.
   Während eines Titels sämtliche weiteren Soundaufrufe verwerfen, auch von
   anderen Soundtasten. Kein Neustart, kein Abschneiden, keine Überlagerung und
   keine nachträgliche Warteschlange.
5. Am tatsächlichen Transportende nach PLAYING wieder freigeben. Keine festen
   oder geschätzten Soundlängen-Sperren. Dauerabhängige Fehler-Watchdogs bleiben
   erlaubt; sie ersetzen keine bestätigte Ende-Erkennung. Alte, verspätet
   eingelesene Tastendrücke bleiben verworfen.
6. Bei neuer Wiedergabelogik oder neuen Formaten einmal am HEOS prüfen: genau
   eine vollständige Wiedergabe, selbstständiger Stopp, kein Wiederholen und
   keine nachgeholten Aufrufe bei Mehrfachdruck/Tastenwechsel.

Aktuell ist nur das Lachen implementiert. Die Erweiterung muss Dateiauswahl,
HTTP-Routen, Metadaten und Tastenbelegung gemeinsam verallgemeinern; das bloße
Ergänzen einer Taste genügt nicht. Name, Player-ID, IP und Lautstärke bleiben
explizit dem gewünschten Lautsprecher zugeordnet.

## Spätere Erweiterungen

Weitere Soundtasten, alternative Quellen über USB oder Musikserver und
Wiederauffinden bei geänderter HEOS-IP sind noch nicht implementiert.
OFF ist als gemeinsamer Panic-Stopp umgesetzt; siehe [Showcontroller](show.md#panic-stopp-über-off).
