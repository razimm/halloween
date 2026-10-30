# Projektvorgaben

## Neue HEOS-Sounds

Bei jedem neuen HEOS-Sound die Vorgaben in `docs/heos-soundboard.md`, Abschnitt
„Verbindliche Vorgaben für neue Sounds“, anwenden.

- Als endlichen UPnP-Musiktitel über `Renderer.load_track()` / AVTransport
  abspielen, mit passenden DIDL-Lite-Metadaten und Wiedergabemodus NORMAL.
- Nicht `browse/play_stream` / Play URL für einzelne Effekte verwenden:
  Der Küchen-HEOS hat damit die Datei selbstständig wiederholt.
- Pro Datei das abspielbare Format, die tatsächliche Audiodauer und Dateigröße
  ermitteln. Keine vom Lachen kopierten festen Werte für andere Sounds.
- Eine gemeinsame Wiedergabesperre für alle Soundtasten desselben Players.
  Drücke während der Wiedergabe verwerfen: kein Neustart, keine Überlagerung,
  keine Warteschlange, auch nicht beim Wechsel zwischen verschiedenen Tasten.
- Die Sperre endet mit dem tatsächlichen Transportende nach PLAYING.
  Sounddauer nur für Metadaten und Fehler-Watchdogs verwenden, nicht als
  geschätzten Ersatz für das Wiedergabeende. Verspätete alte Tastendrücke
  weiterhin anhand ihres Ereigniszeitpunkts verwerfen.
- Zielplayer ausdrücklich anhand Name, Player-ID und IP prüfen. Andere
  HEOS-Geräte nicht unbeabsichtigt mitsteuern; Gruppierungen berücksichtigen.

## Prüfungen

Reine kleine Parameter- und Dokumentationsänderungen ohne Tests umsetzen.
Bei relevanten Änderungen an Logik, Geräteansteuerung oder Wiedergabeverhalten
gezielt prüfen. `./test.sh` verwenden: keine Ausgabe bei Erfolg, Protokoll nur
bei Fehlern. Bei Änderungen der HEOS-Wiedergabe auch den tatsächlichen
Wiedergabeschluss und Mehrfachdrücke am Lautsprecher prüfen.

## Panic-Stopp

OFF an der Hama (`KEY_SLEEP`, 142) hat Vorrang vor allen anderen Eingaben.
PANIC stoppt alle Effekte und Audio einschließlich HEOS, setzt PAR auf Schwarz
und KORAD auf 300 mA. Keine automatische Wiederaufnahme; nur ein neuer Druck
auf Taste 1 gibt den normalen Idle-Betrieb frei. Neue Effekte/Aktoren müssen
ebenfalls diesen Stopppfad unterstützen. Bereits gestartete oder vorgemerkte
Netzwerkaktionen dürfen nach dem Stopp keine verspätete Wiedergabe auslösen.
Taste 2 (`KEY_KP2`, 80) stellt den normalen Show-Endzustand LOCKED her:
lokale Show aus, KORAD aus, PAR rot. Nach fünf Sekunden läuft die
Hintergrundmusik mit 15 % im Loop, ohne die Show freizugeben. Vor Voice-Ansagen
und Zap-up die Musik unterbrechen, danach wieder starten; keine Überlagerung
auf dem lokalen Audioausgang. PANIC stoppt und verwirft auch diesen Musikstart.
Taste 2 hebt PANIC nicht auf.
Neue Showaktoren müssen auch bei diesem manuellen Showende zurückgesetzt werden.
