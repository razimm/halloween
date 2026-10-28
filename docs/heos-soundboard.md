# Hama-Fernbedienung und HEOS 5 – spontanes Soundboard

## Zweck und klare Trennung

**Roter Buzzer draußen:** startet die **gesamte** Halloween-Show mit dem dafür vorgesehenen Ablauf.

**Hama-Fernbedienung:** dient **ausschließlich** dazu, spontane einzelne Sounds abzuspielen, unabhängig von der Show. Ein Hama-Tastendruck darf **weder die komplette Show starten noch Nebel, Servo, KORAD oder DMX auslösen**.

## Vorhandene Hardware
- Hama-Multimedia-Fernbedienung mit rotem USB-Empfänger (auf Foto gezeigt), vermutlich USB-HID/IR; genaue Identifikation und Tastenereignisse noch zu prüfen.
- Raspberry Pi 4 im gleichen Heimnetz.
- Denon **HEOS 5**, nach Aussage des Benutzers bereits im Heimnetz und per HEOS-App bedienbar.
- USB-Stick am HEOS 5 als mögliche lokale Soundquelle. Dateizugriff und Format (z. B. MP3, FAT32) anhand des Gerätes und der HEOS-App testen.

## Angestrebter Ablauf
1. Hama-Taste wird am Raspberry Pi über den USB-Empfänger erkannt.
2. Eine feste Zuordnung wählt **genau einen Sound**.
3. Raspberry Pi sendet über das Heimnetz einen HEOS-Wiedergabebefehl.
4. HEOS 5 spielt den Sound vom bereitgestellten Medium ab.
5. Wiedergaberegeln für schnelles mehrfaches Drücken sowie Stop/Überschreiben werden festgelegt.

## Geplante Soundbelegung (Beispiele, nicht final)
| Taste | Einzeleffekt |
|---|---|
| 1 | Gruseliges Lachen |
| 2 | Schrei |
| 3 | Elektrisches Knistern / Bzzzt |
| 4 | Donner / Gewitter |
| 5 | Wolfsgeheul |
| 6 | Knarrende Tür |
| Stop | Laufenden spontanen Sound beenden |

Die Hama-Remote ist **kein zweiter Show-Startknopf**.

## HEOS-Steuerung
- Dokumentierte lokale HEOS-CLI über TCP-Port **1255** als vorgesehener Weg.
- Zuerst HEOS-Player entdecken und Player-ID ermitteln.
- Über die HEOS-Browse-API die USB-Medienquelle und die konkreten Track-IDs ermitteln; nicht annehmen, dass ein Dateipfad direkt als Play-Befehl funktioniert.
- Wiedergabestart und Latenz vor Ort messen. HEOS ist kein Sample-genauer Echtzeit-Audioplayer.
- Lautstärke begrenzen; andere HEOS-Wiedergabe und bestehende Queue nur mit bewusst gewähltem Verhalten beeinflussen.

## Hama-Empfänger
- Empfänger am Pi mit USB-Geräteerkennung und Eingabeereignissen prüfen (z. B. evtest). Kein bestimmter Linux-Keycode ist vorab bestätigt.
- Sichtkontakt/Empfängerposition bei Infrarot beachten; Reichweite am vorgesehenen Ort testen.

## Offene Entscheidungen
- USB-Stick tatsächlich am HEOS verwendbar und Dateien durch HEOS-CLI adressierbar?
- Was passiert, wenn bei laufendem Sound eine neue Taste gedrückt wird: unterbrechen, ignorieren oder einreihen?
- Dürfen spontane Sounds parallel zur Hauptshow laufen? Standardvorschlag: getrennte Steuerlogik; akustische Überlagerung bewusst testen.
- Brauchen Soundboard und Show unterschiedliche Lautstärkegrenzen?

**Status:** Konzept dokumentiert, noch keine bestätigte Steuerung per Hama oder HEOS-CLI. Implementierung erfolgt mit Codex, hier bewusst ohne Codebeispiele.
