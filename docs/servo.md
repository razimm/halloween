# Miuzei MS24-UF (20 kg, 270°) – mechanischer Nebeldrücker

**Entscheidung:** Für die kabelgebundene Nebelmaschinen-Fernbedienung verwenden wir den **Miuzei MS24-UF (20 kg·cm-Klasse, 270°)** anstelle eines Bluetooth-SwitchBot. Der Knopf muss zum Nebeln **gedrückt gehalten** werden.

## Betrieb und Steuerung
- Raspberry Pi 4, Positionsansteuerung per PWM, vorgesehener Anschluss **GPIO18 / physischer Pin 12**.
- Servo **nicht** aus Pi-GPIO oder Pi-5-V-Pin speisen. Eigenes, geeignetes **5-V-/3-A-Netzteil**, mit gemeinsamer Signalmasse zum Pi (z. B. physischer Pin 14); Polarität und Steckerbelegung des konkreten Servos prüfen.
- **Laut fotografierter Originalanleitung:** Weiß = Signal, Rot = Plus, Schwarz = Minus/GND. Polarität vor dem Einschalten kontrollieren.
- Für den ersten Test ohne Servohebel und ohne Kontakt zur Fernbedienung mit kleinem Bewegungsbereich beginnen; erst danach Endpositionen vorsichtig kalibrieren.
- Ein einzelner Servo kann prinzipiell per GPIO angesteuert werden. Bei PWM-Zittern wäre ein separater PWM-Controller optional.
- Der Servotest nutzt jetzt Hardware-PWM0 an GPIO18 über Linux-sysfs statt
  Software-PWM. Boot-Konfiguration unter `[all]`: `dtparam=audio=off` und
  `dtoverlay=pwm,pin=18,func=2`. Anschließend ist ein Neustart erforderlich.
  Der analoge Pi-Audioausgang teilt die PWM-Hardware und wird deshalb
  deaktiviert; USB-Audio für die Show bleibt verfügbar.

## Mechanik
- Fest am Gehäuse der Fernbedienung montierter Servo mit kurzem Hebel und weicher Druckspitze.
- **Ruheposition:** Taste vollständig freigegeben.
- **Druckposition:** Taste zuverlässig gedrückt, ohne den Knopf oder Servo bis zum Anschlag zu überdrücken.
- Nach kurzer, begrenzter Haltezeit kontrolliert in Ruheposition zurückfahren.
- Falls möglich Feder oder unabhängige Rückstellung vorsehen, sodass auch ein stromloser bzw. gestörter Servo den Taster nicht dauerhaft blockiert.
- Nicht auf ein selbsthemmendes Schneckengetriebe vertrauen: Der Servo hält die Sollposition im Betrieb aktiv gegen den Tastendruck.

## Drehmoment und Strom
- **Fotografierte MS24-UF-Daten:** Betrieb 4,8–6,8 V; Spitzendrehmoment 20,5 kg·cm bei 4,8 V bzw. 22,8 kg·cm bei 6,8 V. Blockierstrom ca. 2,1 A ±10 % (4,8 V) bzw. 2,7 A ±10 % (6,8 V). Signal-Pulsbreite **500–2500 µs**, 270° Stellweg. Die Anleitung nennt Stall-Schutz. Für die mechanische Tasterbetätigung nur einen kleinen kalibrierten Teilbereich anfahren.
- **Blockierstrom ist kein konstanter Betriebsstrom.** Für beliebige Druckkräfte gibt es ohne Messung keine belastbare Tabelle der Halteströme.
- Bei idealisiert senkrechtem Kraftangriff gilt: Drehmoment = Kraft × Hebelarm. Ein kürzerer Hebel reduziert das benötigte Drehmoment. Die maximale Servo-Kraft ist für kleine Taster hoch; Druckweg und Kraft mechanisch begrenzen.
- Für eine tatsächliche Strommessung kann das KORAD als separate 5-V-Versorgung dienen, mit passender Stromgrenze; dabei USB-/LED-Aufgaben und Stromversorgungen sorgfältig trennen und die Messung kontrolliert durchführen.

## Sicherheitsanforderungen
- Nebelmaschine und Heizsicherheit unverändert lassen; die Original-Fernbedienung nur mechanisch drücken.
- Auf verlässliches Loslassen bei Fehler und eine **unabhängige Möglichkeit zum Abschalten der Nebelmaschine** achten.
- Test zunächst ohne Nebel, dann kurze beaufsichtigte Nebelstöße bei ausreichender Sicht und gemäß Herstellergrenzen.
- Software soll eine maximale Druckzeit, Sperrzeit und sichere Abbruchbehandlung vorsehen.

## Erster Bewegungstest

Servo ist laut Rückmeldung angeschlossen. Vor dem Test Hebel abnehmen und
Nebelmaschinen-Taster frei lassen. Auch die erste Fahrt zur Mitte kann einen
größeren Weg zurücklegen, wenn die Welle anders steht.

```bash
sudo .venv/bin/python -m tools.servo_test
```

Mit `m` und Enter zunächst die Mitte (1500 µs) anfahren. Danach einzeln `l`
(1450 µs), `m`, `r` (1550 µs), `m` testen. Jeder Befehl sendet bei 50 Hz nur
eine Sekunde lang Pulse; danach entfällt die aktive Positionshaltung.
`q`, Strg+C oder SIGTERM beendet den Test und gibt PWM0 frei. Die Pulse werden
nach jeder Bewegung abgeschaltet; während der Eingabe wartet der Test ohne
aktives Steuersignal. Hardware-PWM stoppt bei einem harten Prozessabbruch
(SIGKILL) nicht von selbst: bei einem solchen Fehler Servoversorgung trennen.
Bei Brummen ohne Bewegung, Anschlag oder starker Erwärmung Versorgung trennen.

Dies ist ein isolierter Konsolentest, noch keine Showintegration; die Hama
steuert diesen Test nicht. Der bestehende Showbetrieb bleibt unverändert.
Für den späteren Betrieb muss der Servo auch OFF/PANIC und Taste 2 beachten.
Der erste Test mit Software-PWM zeigte Zappeln während der Bewegung.
Mit Hardware-PWM erneut prüfen; bei weiterem Zittern Versorgung und Mechanik
prüfen, bevor ein Tastendruck kalibriert wird.

Technische Grundlage: [Linux-PWM-sysfs-Schnittstelle](https://www.kernel.org/doc/html/latest/driver-api/pwm.html).

**Status:** MS24-UF anhand von Verpackung, Anleitung und Gerätefotos bestätigt;
mechanischer Aufbau auf Holzträger fotografiert. Verdrahtung und Bewegung bestätigt. Hardware-PWM beseitigt laut
Rückmeldung das Zappeln, aber jeder der Befehle `m`, `l`, `r` führt zu großen,
wechselnden Hin- und Rückbewegungen statt reproduzierbaren kleinen Winkeln.
Ursache offen: Versorgung und Verhalten beim Signalabschalten prüfen;
die genaue Hersteller-Suffix-Zuordnung ist unten dokumentiert. Noch keine verlässliche Positionssteuerung bestätigt;
Hebel und Nebeltaster bis zur Klärung nicht koppeln. Kalibrierung,
Nebelbetätigung und Showintegration stehen aus.

## Eigene Gerätefotos

Folgende fünf Originalfotos liegen vor und sind für `images/servo/` vorgesehen (Bilddateien noch manuell ins Repository übernehmen):

1. `01-verpackung.jpg` – Miuzei-Verpackung (MS24-C-UF auf Etikett).
2. `02-anleitung-steuerung-und-anschluss.jpg` – Pulsbereich, Anschlussfarben, Stromversorgung.
3. `03-anleitung-technische-daten.jpg` – Handbuch mit Produktname MS24-UF und elektrischen Daten.
4. `04-servo-vorderansicht.jpg` – MS24-Servo und verzahnte Abtriebswelle.
5. `05-servo-montage.jpg` – vorhandene Servomontage mit Hebel am Holzträger.

**Hinweis zur Modellbezeichnung:** Der Verpackungsaufkleber nennt `MS24-C-UF`, die gedruckte Anleitung `MS24-UF`, und das Gehäuse `MS24`. Technische Daten dieser beiliegenden Anleitung entsprechen der gezeigten Hardware, eine exakte Hersteller-Suffix-Auflösung ist noch nicht bestätigt.
