# Miuzei MS24-UF (20 kg, 270°) – mechanischer Nebeldrücker

**Entscheidung:** Für die kabelgebundene Nebelmaschinen-Fernbedienung verwenden wir den **Miuzei MS24-UF (20 kg·cm-Klasse, 270°)** anstelle eines Bluetooth-SwitchBot. Der Knopf muss zum Nebeln **gedrückt gehalten** werden.

## Betrieb und Steuerung
- Raspberry Pi 4, Positionsansteuerung per PWM, vorgesehener Anschluss **GPIO18 / physischer Pin 12**.
- Servo **nicht** aus Pi-GPIO oder Pi-5-V-Pin speisen. Eigenes, geeignetes **5-V-/3-A-Netzteil**, mit gemeinsamer Signalmasse zum Pi (z. B. physischer Pin 14); Polarität und Steckerbelegung des konkreten Servos prüfen.
- **Laut fotografierter Originalanleitung:** Weiß = Signal, Rot = Plus, Schwarz = Minus/GND. Polarität vor dem Einschalten kontrollieren.
- Für den ersten Test ohne Servohebel und ohne Kontakt zur Fernbedienung mit kleinem Bewegungsbereich beginnen; erst danach Endpositionen vorsichtig kalibrieren.
- Ein einzelner Servo kann prinzipiell per GPIO angesteuert werden. Bei PWM-Zittern wäre ein separater PWM-Controller optional.

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

**Status:** MS24-UF ist anhand von Verpackung, Anleitung und Fotos des vorhandenen Servos bestätigt; mechanischer Aufbau auf Holzträger ist fotografiert. Sichere Funktion und Nebelmaschinen-Test noch nicht bestätigt. Kein Code in dieser Datei – Implementierung mit Codex.

## Eigene Gerätefotos

Folgende fünf Originalfotos liegen vor und sind für `images/servo/` vorgesehen (Bilddateien noch manuell ins Repository übernehmen):

1. `01-verpackung.jpg` – Miuzei-Verpackung (MS24-C-UF auf Etikett).
2. `02-anleitung-steuerung-und-anschluss.jpg` – Pulsbereich, Anschlussfarben, Stromversorgung.
3. `03-anleitung-technische-daten.jpg` – Handbuch mit Produktname MS24-UF und elektrischen Daten.
4. `04-servo-vorderansicht.jpg` – MS24-Servo und verzahnte Abtriebswelle.
5. `05-servo-montage.jpg` – vorhandene Servomontage mit Hebel am Holzträger.

**Hinweis zur Modellbezeichnung:** Der Verpackungsaufkleber nennt `MS24-C-UF`, die gedruckte Anleitung `MS24-UF`, und das Gehäuse `MS24`. Technische Daten dieser beiliegenden Anleitung entsprechen der gezeigten Hardware, eine exakte Hersteller-Suffix-Auflösung ist noch nicht bestätigt.
