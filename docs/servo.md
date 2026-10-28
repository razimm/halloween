# DS3218-Servo – mechanischer Nebeldrücker

**Entscheidung:** Für die kabelgebundene Nebelmaschinen-Fernbedienung verwenden wir den **Miuzei DS3218 (20 kg·cm-Klasse)** anstelle eines Bluetooth-SwitchBot. Der Knopf muss zum Nebeln **gedrückt gehalten** werden.

## Betrieb und Steuerung
- Raspberry Pi 4, Positionsansteuerung per PWM, vorgesehener Anschluss **GPIO18 / physischer Pin 12**.
- Servo **nicht** aus Pi-GPIO oder Pi-5-V-Pin speisen. Eigenes, geeignetes **5-V-/3-A-Netzteil**, mit gemeinsamer Signalmasse zum Pi (z. B. physischer Pin 14); Polarität und Steckerbelegung des konkreten Servos prüfen.
- Servo-Leitung typischerweise Signal, Plus und GND; Kabelbelegung vor Anschluss anhand der Modellunterlagen verifizieren.
- Für den ersten Test ohne Servohebel und ohne Kontakt zur Fernbedienung mit kleinem Bewegungsbereich beginnen; erst danach Endpositionen vorsichtig kalibrieren.
- Ein einzelner Servo kann prinzipiell per GPIO angesteuert werden. Bei PWM-Zittern wäre ein separater PWM-Controller optional.

## Mechanik
- Fest am Gehäuse der Fernbedienung montierter Servo mit kurzem Hebel und weicher Druckspitze.
- **Ruheposition:** Taste vollständig freigegeben.
- **Druckposition:** Taste zuverlässig gedrückt, ohne den Knopf oder Servo bis zum Anschlag zu überdrücken.
- Nach kurzer, begrenzter Haltezeit kontrolliert in Ruheposition zurückfahren.
- Falls möglich Feder oder unabhängige Rückstellung vorsehen, sodass auch ein stromloser bzw. gestörter Servo den Taster nicht dauerhaft blockiert.
- Nicht auf ein selbsthemmendes Schneckengetriebe vertrauen: Der DS3218 hält die Sollposition im Betrieb aktiv gegen den Tastendruck.

## Drehmoment und Strom
- DS3218 wird als Servo der **20-kg·cm-Klasse** angeboten; im Gespräch ca. **18 kg·cm bei 5 V** und **1,8 A Blockierstrom bei 5 V** als typische Datenblattwerte genannt; konkrete Variante prüfen.
- **Blockierstrom ist kein konstanter Betriebsstrom.** Für beliebige Druckkräfte gibt es ohne Messung keine belastbare Tabelle der Halteströme.
- Bei idealisiert senkrechtem Kraftangriff gilt: Drehmoment = Kraft × Hebelarm. Ein kürzerer Hebel reduziert das benötigte Drehmoment. Die maximale Servo-Kraft ist für kleine Taster hoch; Druckweg und Kraft mechanisch begrenzen.
- Für eine tatsächliche Strommessung kann das KORAD als separate 5-V-Versorgung dienen, mit passender Stromgrenze; dabei USB-/LED-Aufgaben und Stromversorgungen sorgfältig trennen und die Messung kontrolliert durchführen.

## Sicherheitsanforderungen
- Nebelmaschine und Heizsicherheit unverändert lassen; die Original-Fernbedienung nur mechanisch drücken.
- Auf verlässliches Loslassen bei Fehler und eine **unabhängige Möglichkeit zum Abschalten der Nebelmaschine** achten.
- Test zunächst ohne Nebel, dann kurze beaufsichtigte Nebelstöße bei ausreichender Sicht und gemäß Herstellergrenzen.
- Software soll eine maximale Druckzeit, Sperrzeit und sichere Abbruchbehandlung vorsehen.

**Status:** Servo ausgewählt; tatsächlicher Einbau und erfolgreichen Test noch nicht bestätigt. Kein Code in dieser Datei – Implementierung mit Codex.
