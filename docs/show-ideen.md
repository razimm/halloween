# Ideen für die Halloween-Show

## Vorschlag: 35-Sekunden-Michael-Myers-inspirierte Show

| Zeit | Audio | DMX-Licht | Nebel / Zusatz-LED |
|---|---|---|---|
| 0–3 s | Leises unheimliches Intro | Dimmen | Noch kein Nebel |
| 3–8 s | Spannung steigt | Dunkelrot | Kurzer Nebelstoß **nach Freigabe des Tests** |
| 8–15 s | Horror-/Halloween-Musik | Langsame Farbwechsel | Langsames LED-Flackern, sofern USB-Steuerung geeignet |
| 15–25 s | Musikalischer Höhepunkt | Kurze gemäßigte Lichtakzente | Nebel nur falls sicher, genügend Sicht |
| 25–35 s | Ausklang / „Süßes oder Saures!“ | Grundlicht | Nebel aus, LED sicher zurücksetzen |

Zeitpunkte sind vorläufig. Kein lautes Erschrecken direkt neben Kindern, keine blendenden schnellen Stroboskope. Die bekannte Titelmelodie von John Carpenter ist nur eine kreative Referenz; Rechte klären.

## Varianten
- **Kinderfreundlich:** kürzer, leiser, wenig Nebel, warme Farben, kein Schock.
- **Horror:** düstere Geräusche, rote Akzente, vorsichtiger Nebeleinsatz.
- **Zufall:** zufällige Auswahl mehrerer **freigegebener** Show-Presets.

## Visuelle Ideen
- Feuerflackern (sanft und unregelmäßig).
- Gewitterblitze (nur milde, isolierte Akzente).
- Dramatischer Lichtpuls zu ausgewählten Musik-Zeitpunkten.
- **Fertiges Schildmotiv:** querformatiges Halloween-Design mit frech grinsendem Kürbis, rotem Knopf und einzigem großen Text **„Auf keinen Fall den Knopf drücken“**. Bild noch als Asset ins Repository übernehmen.
- Buzzer-Text im Konzept wurde durch dieses Motiv ersetzt.

## Interaktion
**Roter Außen-Buzzer:** In IDLE startet er die vollständige Show. Während RUNNING
werden weitere Drücke ignoriert. Nach Showende ist LOCKED aktiv: Flat Par rot,
KORAD-LED aus; Hintergrundmusik startet nach fünf Sekunden wieder mit 15 % im Loop. Ein Druck lässt den Flat Par dreimal rot
blinken und spielt eine zufällige Voice-Datei vollständig, ohne Überlagerung.
Kein automatischer Cooldown-Timer. Siehe [implementierter Ablauf](show.md).

**Hama-Fernbedienung:** Taste 1 ist für die manuelle Freigabe reserviert (Flat Par grün und KORAD-LED an). Die übrigen Tasten können später unabhängig davon spontane Einzelgeräusche auf dem HEOS 5, z. B. gruseliges Lachen, Schrei, Donner, Wolfsgeheul, knarrende Tür oder elektrisches *Bzzzt*. Keine Show-, Nebel- oder Lichtauslösung über die Hama-Fernbedienung. Überschneidungen zwischen spontanen Sounds und Show-Audio später bewusst festlegen.

Perspektivisch Weboberfläche für Shows, Lautstärke, Licht/Nebel ein/aus und Tests.
