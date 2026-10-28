# Sicherheit, Grenzen und Testplan

## Nebelmaschine
- Mechanischer Drücker betätigt nur die vorhandene Fernbedienung; keine Netzspannung und keine Heiz-/Temperatursicherungen verändern.
- Der Knopf benötigt **Dauerdruck**. Der gewählte DS3218-Servo ist nicht selbsthemmend und benötigt zur Positionshaltung Strom. Mechanik mit sicheren Endpunkten, begrenzter Druckkraft, zuverlässigem Rückzug und nach Möglichkeit einer unabhängigen mechanischen Rückstellung auslegen. Auch bei Pi-/Stromausfall darf der Knopf nicht dauerhaft hängen bleiben. Eine **unabhängige Abschaltmöglichkeit** für die Nebelmaschine muss bleiben.
- Kurze Nebelstöße und Sperrzeit; Hersteller-Aufwärmphase, zulässige Dauer, Flüssigkeit und Belüftung beachten.
- Keine Vernebelung von Stufen, Fluchtwegen oder Gehwegen; Windrichtung und Sicht beachten.

## Nackte 10-W-LED und KORAD
- LED **ohne integrierte Stromregelung**: geeignete Strombegrenzung und Kühlkörper sind zwingend.
- 12 V/900 mA und später 10 V/800 mA sind genannte **Einstellungen**, keine bestätigten Nenn- oder Messwerte.
- CC und CV unterscheiden: nur eine Regelart bestimmt den Betrieb unter Last, die andere Einstellung wirkt als Grenze.
- Vor USB-Schaltversuchen: Datenblatt/LED-Grenzen ermitteln. Zunächst ohne LED und mit geeigneter Prüflast testen.
- Schnelles Ein-/Ausschalten des Labornetzteils kann wegen Ausgangskapazität und Regelverzögerung Stromspitzen erzeugen. Die Grenze von 800 mA verhindert nicht zwingend kurze Peaks.
- **Keinen einfachen PWM-MOSFET hinter dem KORAD als automatisch sicheren LED-Treiber ansehen.** Für schnelle Dimmung geeigneten Konstantstrom-LED-Treiber mit PWM-DIM-Eingang verwenden.

## Kamera und Privatsphäre
- Trust-Webcam nur zur Livebeobachtung des eigenen Eingangs; keine Aufzeichnung und keine Analyse von Personen.
- Öffentliche Flächen und Nachbargrundstücke nicht erfassen; Zugriff nur im lokalen vertrauenswürdigen Netz.
- Transparenz/Hinweise bei Besuchern und einschlägige Datenschutzanforderungen prüfen.
- Kamera wettergeschützt montieren; ihr Dienst muss unabhängig von der sicherheitskritischen Showsteuerung laufen.

## Gäste und Elektrik
- Elektronik im geschützten Gehäuse, Netzstrom nur fachgerecht, keine Stolperkabel.
- GPIO nur mit 3,3-V-kompatiblen Schaltungen verbinden.
- Licht nicht auf Gesichter richten, keine intensiven Strobo-Folgen; moderate Lautstärke.
- Heiße LED und bewegliche Aktuatoren außerhalb der Reichweite.
- Show auf Hardwarefehler und unerwarteten Neustart testen: alle Geräte bleiben sicher.

## Testreihenfolge
1. Simulator: keine physische Aktivierung.
2. Buzzer und Audio mit begrenzter Lautstärke.
3. DMX mit unkritischer Lichtstimmung.
4. KORAD USB erst ohne LED, dann Prüflast.
5. Fingerbot allein, danach kontrolliert an Fernbedienung.
6. Fehlerszenarien: Pi-Neustart, Servostrom-Ausfall, verklemmter Taster, mehrfacher Buzzer; spontane Hama-Sounds dürfen die Showsteuerung nicht auslösen.
7. Gesamttest ohne Publikum und mit physischem Stop.
