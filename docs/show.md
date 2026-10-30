# Vollständiger Halloween-Ablauf

## Start und Bedienung

```bash
./setup.sh
./start-show.sh --demo          # Vollständiger Ablauf mit virtueller Uhr, ohne Hardware/Ton
./start-show.sh --simulate      # Interaktiv: b = Buzzer, 1 = Freigabe, p = KORAD (je + Enter), q = Ende
sudo ./start-show.sh --play     # Echte Hardware; startet im freigegebenen Idle
```

Ohne `--play` wird ausschließlich simuliert. Das frühere einzelne Zap-Testprogramm
bleibt über `tools/sound_light.py` verfügbar. `Strg+C` und SIGTERM stoppen Audio,
versuchen den KORAD-Ausgang abzuschalten und senden einen vollständigen DMX-Blackout.
Ein Prozess-/USB-/Netzwerkausfall kann die physische Abschaltung nicht garantieren.
Es wird kein Autostart eingerichtet und kein Nebel/Servo angesprochen.

Für einen frischen Pi werden zum Bau der Treiber zusätzlich `build-essential`,
`python3-dev`, `swig` und `liblgpio-dev` benötigt; Audio benötigt `ffmpeg` und
`alsa-utils`. Die Treiber sind auf diesem Pi installiert. Hama-Empfänger
(`/dev/input/event6`) und GPIO17 wurden erfolgreich ohne Auslösen der Show geöffnet.

Vor dem Hardwarestart müssen Buzzer GPIO17 gegen GND, LED am KORAD mit Kühlkörper,
Logitech G433, Hama-Empfänger und Showtec verbunden sein. Die erforderlichen Geräte
werden vor dem Idle-Beginn geöffnet. Es gibt keine gleichzeitige Nutzung des
KORAD-Ports durch mehrere Programme. GPIO17 verwendet einen internen Pull-up.

## Zustände und Reihenfolge

| Zustand | Hintergrundmusik | 10-W-LED am KORAD | Flat Par QA5X | Buzzer |
| --- | --- | --- | --- | --- |
| IDLE | Loop, 15 % | 300 mA, maximal 10 V | Grün (5 %) | Show starten |
| RUNNING | Aus | Beim Zap flackern (bis 700 mA), zum Soundende aus; danach aus | Showeffekte | Ignorieren |
| LOCKED | Loop mit 15 % nach 5 s; pausiert für Voice/Zap-up | Aus; Play/Pause erlaubt manuelles An/Aus | Rot | Zufällige Ansage und dreimal rot blinken |
| PANIC | Aus | Sofort 300 mA | Aus | Ignorieren |
| RELEASING | Wartet auf Ansageende | In 2 s wieder 300 mA | In 2 s Grün (5 %) | Bis Ansageende ignorieren |

Die Show spielt ohne Überlagerungen in dieser Reihenfolge:

1. `electric-zap_break_final.mp3`: aus derselben dekodierten Spur berechnete
   Strommodulation in 80-ms-Schritten. In den letzten 0,5 Sekunden blendet die
   LED vom letzten Stromwert aus; zum Soundende ist der Ausgang abgeschaltet.
   Es gibt keine zusätzliche Ausblendphase nach dem Sound. Der Flat Par leuchtet 1,05 Sekunden vor dem Zap-Ende schnell weiß mit 100 %
   auf, hält die Spitze 0,05 Sekunden und blendet über 0,5 Sekunden aus.
   RGB und Master erreichen 255, Amber und Strobe-Kanal bleiben 0.
   Danach folgt eine Sekunde dunkle/stille Pause vor der Kirchenglocke.
   Buzzer und Hama-Freigabe werden während dieser Pause weiter ignoriert.
   Die KORAD-Steuerung bleibt gleich.
2. `church_bell_final.mp3` bei ausgeschalteter KORAD-LED. Der PAR leuchtet
   auf jedem der drei Gong-Anschläge orange mit 100 % auf: Zeitmarken 0,08,
   5,62 und 11,10 Sekunden, je 0,2 Sekunden halten und über 3,5 Sekunden
   abblenden. Rot und Amber sowie der Master-Dimmer erreichen dabei DMX 255.
   Die Impulse laufen im unabhängigen 40-Hz-Sender; die Zeitmarken wurden aus
   der aktuellen Audiodatei ermittelt und können nach Hörtest nachjustiert werden.
3. `michael_myers_final.mp3`: langsame Rot-/Violett-/Amber-Pulse über Art-Net.
   Die Lichtfolge beginnt mit dem Track; Farben, Periode und Helligkeit sind konfigurierbar.
   Diese erste Lichtfassung benötigt noch eine Sicht-/Hörabstimmung.
4. `laughing.wav`
5. LOCKED bis zur manuellen Freigabe; kein zeitgesteuerter Cooldown.

In LOCKED wählt ein neuer Buzzer-Druck zufällig zwischen `voice_gruen_sein.mp3` und
`voice_habt_geduld.mp3`. `voice_noch_nicht.mp3` ist aus dem Zufallspool entfernt. Die Datei läuft vollständig durch.
Weitere Drücke während der Ansage werden verworfen, ohne Neustart, Warteschlange
oder Überlagerung. Es gibt drei Dunkel-/Rot-Zyklen (je 0,3 Sekunden pro Halbphase),
danach wieder dauerhaft Rot. Auch bei einer sehr kurzen Ansage wird die Blinkfolge
nicht durch einen weiteren Buzzer-Druck neu gestartet.

**Hama-Taste 1** (`KEY_KP1`, Code 79) gibt ausschließlich eine gesperrte Show frei.
Sie startet selbst keine Show. KORAD-LED und Grün beginnen sofort einen weichen Übergang über zwei Sekunden. Läuft eine
Ansage, endet sie vollständig vor dem Start der Hintergrundmusik und der erneuten
Buzzer-Bereitschaft. Taste 1 während der Hauptshow wird ignoriert und merkt keine
spätere Freigabe vor. Loslassen, Wiederholungs- und NumLock-Ereignisse lösen nichts aus.
**Play/Pause** (`KEY_PLAYPAUSE`, Code 164) schaltet die KORAD-LED ausschließlich
im weiterhin gesperrten LOCKED-Zustand manuell ein oder aus. Zum Einschalten
läuft `electric-zap_up_final.mp3` vollständig (etwa 3,987 Sekunden). Ihre aus den
dekodierten Samples neu analysierte Strom-Timeline verwendet dieselbe Methode
wie der Zap-Ausfall, mit maximal 700 mA und 10 V. Danach blendet die LED auf
300 mA ein. Ein erneuter Play/Pause-Druck blendet sie über zwei Sekunden aus.
Flat Par bleibt rot und die Show gesperrt. Die Hintergrundmusik pausiert für
den Einschalt-Sound und läuft anschließend wieder, sobald die fünf Sekunden
seit Beginn der Sperre abgelaufen sind.

Während einer Hauptshow, Ansage, Blinkfolge oder laufenden Einschaltsequenz wird
Play/Pause ignoriert. Während des Einschalt-Sounds werden auch Buzzer-Drücke
verworfen: keine Unterbrechung, Überlagerung oder Warteschlange. Taste 1 kann
weiterhin freigeben; der PAR wird grün, der Einschalteffekt läuft vollständig
zu Ende, danach starten Hintergrundmusik und Buzzer-Bereitschaft. Die KORAD-LED
geht anschließend auf 300 mA. Nach jeder regulären Show ist sie zunächst wieder aus.

Der Hama-Empfänger stellt Ziffernblock und Play/Pause auf getrennten Linux-
Eingabegeräten bereit; beide werden anhand der USB-ID und Tastencodes geöffnet.
**OK** (`KEY_ENTER`, Code 28) spielt Lachen auf HEOS_Kueche mit 10 % Lautstärke,
unabhängig vom lokalen Show-Audio. Ein eigener Netzwerk-Thread verhindert
Verzögerungen im Showablauf; weitere OK-Drücke während des Effekts werden verworfen.
Siehe [HEOS-Soundboard](heos-soundboard.md). Andere Hama-Tasten sind nicht belegt.

## Manueller Wechsel zwischen Idle und „Show fertig“

**Taste 1** führt zurück zum freigegebenen Idle mit Hintergrundmusik,
KORAD 300 mA und grünem PAR (5 %).

**Taste 2** (`KEY_KP2`, Code 80) stellt denselben LOCKED-Zustand her wie
nach dem vollständigen Showende: lokale Hintergrund-/Showmusik stoppen,
KORAD ausblenden und ausschalten, PAR über zwei Sekunden auf Rot wechseln.
Nach fünf Sekunden startet die Hintergrundmusik mit 15 % im Loop, genau wie
nach dem normalen Showende. Die Show bleibt bis Taste 1 gesperrt.
Der Buzzer startet jetzt keine Show, sondern nur die bestehende Blink-/Ansagenreaktion.

Taste 2 beendet eine gerade laufende Hauptshow oder einen manuellen
Zap-up-Einschalteffekt und verwirft deren weitere Licht-/Audioaktionen.
Eine laufende Voice-Ansage endet vollständig; eine vorgemerkte Rückkehr
zum Idle wird dabei aufgehoben. HEOS bleibt unabhängig bedienbar.
**PANIC kann Taste 2 nicht aufheben**; dafür bleibt ausschließlich Taste 1 zuständig.

In der Simulation: `2` + Enter für „Show fertig“, `1` + Enter für Idle.

## Panic-Stopp über OFF

**OFF** an der Hama ist `KEY_SLEEP`, Code **142**. Der Empfänger wird während
des laufenden Showprozesses exklusiv gelesen, damit die Taste keine Betriebssystem-
Schlaffunktion auslöst. Beim Schließen wird der Empfänger wieder freigegeben.

OFF wirkt aus jedem Zustand: Hintergrundmusik, Show, Ansagen, Zap-up und laufende
HEOS-Effekte werden abgebrochen. Alle PAR-Fades, Gong-Impulse und Blitze werden
verworfen; der PAR wird sofort schwarz. KORAD wechselt ohne Effekt auf den
normalen Wert von **300 mA bei maximal 10 V**. Das Programm bleibt in PANIC.

Buzzer, OK und Play/Pause werden während PANIC ignoriert. OFF hat auch Vorrang,
wenn mehrere Tasten einschließlich Taste 1 im selben Eingabepaket eintreffen.
Eine vor dem Panic-Stopp gedrückte, erst später eingelesene 1 darf nicht freigeben.

**Ein neuer Druck auf Taste 1** stellt normalen Idle-Betrieb wieder her:
Hintergrundmusik mit 15 %, PAR grün mit 5 %, KORAD 300 mA, Buzzer bereit.
Die abgebrochene Show wird nicht fortgesetzt. Läuft noch ein HEOS-Stop-Auftrag,
wird die Freigabe vorgemerkt und nach dessen Abschluss ausgeführt. Bereits alte
OK-Ereignisse werden auch beim Freigeben nicht nachgeholt.

Der HEOS-Stopp läuft im Hintergrund und sperrt neue Aufrufe sofort. Eine bereits
laufende Titelvorbereitung darf nach dem Stopp keinen verspäteten PLAY-Befehl
senden. Beim Hardwaretest wurde das Lachen auf HEOS_Kueche abgebrochen und der
Zustand STOP bestätigt. Der Denon-Receiver bleibt unverändert.

In der Simulation: `x` + Enter für OFF/PANIC, `1` + Enter zum Wiederfreigeben.
`Strg+C` beendet weiterhin das Programm vollständig und schaltet auch KORAD aus.
OFF ist ein Software-Stopp; Geräte-/USB-/Netzwerkausfälle können eine unabhängige
Abschaltmöglichkeit erforderlich machen. Fehler werden im Terminal angezeigt.

## Hintergrundmusik nach Showende

Im normalen LOCKED-Zustand startet die Hintergrundmusik **fünf Sekunden nach
Showende** wieder mit 15 % im Loop. Das gilt auch für den manuellen Wechsel
mit Taste 2. Es gibt weiterhin keine automatische Showfreigabe und keinen
Cooldown-Timer; PAR bleibt rot und KORAD aus, sofern nicht manuell eingeschaltet.

Für eine Voice-Ansage oder Zap-up wird der lokale Hintergrundloop gestoppt.
Die Datei spielt vollständig; anschließend startet der Loop wieder, wenn die
ursprünglichen fünf Sekunden bereits abgelaufen sind. Sonst wird nur die
Restzeit abgewartet. Die Pause gilt für die lokale Audioausgabe; das unabhängige
HEOS-Soundboard verändert die Hintergrundmusik nicht.

Taste 1 übernimmt einen bereits laufenden Hintergrundloop ohne Neustart in den
Idle-Modus. OFF beendet den Loop und verwirft seinen noch ausstehenden Start;
im Panic-Zustand läuft keine Hintergrundmusik.

## Einstellungen

[config/show.json](../config/show.json) enthält insbesondere:

- `locked_background_delay_s: 5.0`: Verzögerung des Hintergrundloops nach Showende.
- `background_gain: 0.15`: 15 % Sample-Amplitude, unabhängig von Show und Ansagen.
- `show_gain: 1.0` und `voice_gain: 1.0`: Zap und Ansagen mit 100 % Originalamplitude.
- `bell_gain: 0.75`: Kirchenglocke mit 75 %.
- `laugh_gain: 0.4`: Lachen mit 40 %.
- `myers_gain: 1.6807285669423218`: Michael Myers auf 98 % Sample-Spitzenpegel verstärkt.
  Die aktuelle Datei erreicht maximal 32112/32767. Vor dem Rendern wird
  auf Sample-Clipping geprüft; bei zu wenig Reserve bricht der Start vor Gerätezugriff ab.
- `korad_idle_current_A: 0.3`: KORAD-LED im Idle mit ausdrücklich 300 mA.
- `korad_max_current_A: 0.7`: maximale Zap-Stromvorgabe 700 mA.
  Analyse, Befehlsgrenze und Messwertprüfung verwenden dieselbe konfigurierte Grenze;
  die Messwertprüfung hat weiterhin 5 % Toleranz. Die Spannungsgrenze bleibt bei 10 V.
- `par_idle_brightness: 0.05`: Flat-Par-Grün im Idle mit 5 %.
- `zap_par_flash_s: 0.05`: kurze weiße 100-%-Spitze am Zap-Ende.
- `zap_par_flash_fade_s: 0.5`: anschließendes PAR-Ausblenden.
- `zap_par_flash_advance_s: 0.5`: Impuls und Fade um weitere 0,5 Sekunden vorziehen;
  der PAR ist dadurch 0,5 Sekunden vor Zap-Ende wieder aus.
- `zap_bell_pause_s: 1.0`: Pause zwischen Zap-Ende und Kirchenglocke.
- `zap_fade_out_s: 0.5`: KORAD in den letzten 0,5 Sekunden des Zap-Sounds ausblenden, mit Abschaltung zum Soundende.
  Beim Showstart blendet die KORAD-LED auf maximal 700 mA auf; die Myers-Lichtfolge hat
  jetzt 100 % Spitzenhelligkeit. Rot/Blinken während der Sperre bleibt bei 50 %.
- `audio_device`: Logitech-G433-ALSA-Ausgang. System-/Radio-Lautstärken bleiben unverändert.
- `transition_s: 2.0`: weiche Zustandswechsel am Flat Par und Aufblenden der KORAD-LED.
  Die Übergänge laufen ohne Wartepausen für Eingaben/Audio. Die Zap-Sequenz,
  das dreimalige rote Blinken, die Michael-Myers-Lichtfolge und der Stopp-Blackout
  behalten ihr bisheriges Timing.
- `bell_lighting`: Gong-Zeitmarken, Orange-Farbe, Haltedauer und Ausblenddauer.
- `myers_lighting`: Farben, Helligkeit, Pulsdauer und Farbhaltedauer.
  `minimum_brightness: 0.1` und `brightness: 1.0` ergeben 10–100 %.
  Jede Spitze wird mit `peak_hold_s: 0.25` für 0,25 Sekunden gehalten.
  Bei voller Helligkeit erreicht der stärkste Farbkanal 255 und der Master-Dimmer
  ebenfalls 255; Strobe und Farbmakros bleiben 0.
- `artnet`: Node-IP, nullbasierte Portadresse/Universe, DMX-Startadresse und Kanalmodus.

Eine andere Hintergrundlautstärke kann ohne Dateibearbeitung ausprobiert werden:

```bash
sudo ./start-show.sh --play --background-gain 0.25
```

Die Einstellung gilt beim nächsten Programmstart; es gibt noch keine Live-Lautstärkeregelung.
Die Originaldateien bleiben unverändert. Dekodierte und skalierte WAVs werden dauerhaft
unter `audio/playback/` zwischengespeichert und vor Gerätezugriff vorbereitet.
Audiofehler stoppen den Ablauf über den gemeinsamen Aufräumpfad.

## Art-Net und Gerätetest

Node `192.168.178.146` hat am 29.10.2026 per ArtPoll für Port 1 die tatsächliche
Portadresse **1**, für Port 2 **2** gemeldet. In dieser Konfiguration ist `universe: 1`
bereits die Adresse auf dem Netzwerk. Anders als im DMX-Show-Generator wird **keine 1
abgezogen**. Das dortige Software-Universe 2 entspricht hier dem Wert 1.

Das Profil stammt aus dem vorhandenen Projekt
[dmx-show-generator](https://github.com/razimm/dmx-show-generator/blob/main/src/dmx_lighting/fixtures/catalog.py):
Aktuell vom Benutzer bestätigt: **Ch.07**, DMX-Startadresse A.001.
Kanäle 1–4 = Rot, Grün, Blau, Amber; 5 = Master-Dimmer;
6 = Strobe (0–15 aus, 16–255 langsam bis schnell); 7 = Farbmakros.
Strobe und Farbmakros bleiben in der aktuellen Lichtfolge auf 0.
Der vorherige Farb-/Blackout-Test wurde mit RGBA und Master-Dimmer gesendet;
diese ersten fünf Kanäle sind in Ch.05 und Ch.07 gleich belegt.
Der rote Farbtest hat vor Ort reagiert. Die Blackout-Behandlung wurde anschließend
um Nullsetzen des Master-Dimmers, festen Quellport 6454, deaktivierte Sequenzsortierung
und eine Sekunde wiederholter Blackout-Pakete erweitert. Der Benutzer hat den verbesserten Blackout am 29.10.2026 vor Ort bestätigt. Ein erster Live-Durchlauf wurde vom Benutzer positiv bewertet; die neuen Zwei-Sekunden-Übergänge sind noch vor Ort zu prüfen.
Die Kanalbelegung stimmt mit dem [ADJ-Handbuch](https://www.adj.com/cdn/shop/files/f56888a87091f95f69f4e16724398e01ef38d47f_flat_par_qa5x.pdf?v=12201417117090809197)
überein; Paketformat nach [Art-Net-Spezifikation](https://art-net.org.uk/downloads/art-net.pdf).

```bash
# Nur Konfiguration lesen, keine Lichtwerte ändern
.venv/bin/python -m tools.artnet
# Drei Sekunden gedimmt grün, dann Blackout
.venv/bin/python -m tools.artnet --color green --universe 1 --address 1 --mode 7
# Vollständiger Blackout
.venv/bin/python -m tools.artnet --color black --universe 1 --address 1 --mode 7
```

Die Art-Net-Ausgabe läuft mit 40 Bildern pro Sekunde in einem eigenen Sender-Thread.
Fades werden dort zeitbasiert berechnet und laufen auch während serieller
KORAD-Abfragen weiter. Die 40-Hz-DMX-Einstellung am Showtec bleibt erhalten
([Herstellerhandbuch, S. 6](https://www.highlite.com/nl/mwdownloads/download/link/id/17431423)).
Die Ausgabe ist keine harte Echtzeitsteuerung; bei verpassten Terminen werden
aktuelle Werte gesendet, ohne alte Pakete als Burst nachzuholen.

Es wird gezielt Unicast an den Node gesendet. Die Anwendung belegt UDP-Port 6454;
keinen zweiten DMX-Controller parallel betreiben. Alle anderen DMX-Kanäle desselben
Universums werden mit Null ausgegeben. Der Controller unterstützt Ch.04, Ch.05 und Ch.07.

## Prüfungen

```bash
./test.sh
./start-show.sh --demo
```

Die automatischen Tests prüfen Reihenfolge, Dauersperre, Taste 1 während der Show,
Freigabe mitten in einer Ansage, Ende-zu-Ende-Sperre gegen überlappende Sounds,
drei Blinkzyklen, Hintergrund-Loop, KORAD-Grenzen und Art-Net-Paket-/Kanalbelegung.
Die Demo verwendet alle echten Audiodateien für Dauer und Zap-Analyse, aber keine Geräte.

`./test.sh` bleibt bei Erfolg still und zeigt nur bei Fehlern das Testprotokoll.
