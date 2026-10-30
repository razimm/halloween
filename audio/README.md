# Lokale Audiodateien

Aktueller Sound für die Netzteil-/LED-Steuerung: `electric-zap_break_final.mp3`.
Er ersetzt die bisherige `electric-zap.wav`. Die MP3 liegt lokal vor und wird
von Git ignoriert. Das Programm dekodiert sie mit FFmpeg dauerhaft nach
`audio/playback/` (Mono, 44,1 kHz, 16 Bit PCM, etwa 9,335 Sekunden).
Originaldatei und Systemlautstärke bleiben unverändert.

## Herkunft der ursprünglichen Fassung

Die folgenden Angaben dokumentieren die bisherige `electric-zap.wav`:

- Quelle: https://www.youtube.com/watch?v=Zfcaj7M0Qnk
- Titel: Electric Shock / Taser Zap | Free Sound Effect
- Urheber: Jochi SFX
- Format: Mono, 16 kHz, 16 Bit PCM, 7,4188125 Sekunden
- Original-Beschreibung: Nutzung in kreativen Projekten erlaubt;
  Verkauf, Weiterverteilung der Sounddatei und Ausgabe als eigenes Werk untersagt.
- Download des Urhebers: https://jochi.bandcamp.com/album/youtube-sfx-pack

Historische Konvertierung der ursprünglichen Fassung:

```bash
ffmpeg -i /pfad/zur/originaldatei -ac 1 -ar 16000 -c:a pcm_s16le audio/electric-zap.wav
```

Andere Schnittfassungen ändern die Zeitmarken. Das Programm analysiert die
bereitgestellte WAV beim Start neu; `shows/electric-zap.json` dokumentiert
die aktuelle Schnittfassung (Simulation, Hardwaretest noch offen).

## Ablage weiterer Sounds

Alle lokalen Sounddateien gehören dauerhaft in diesen Ordner `audio/`,
z. B. `lachen.mp3`, `donner.wav` oder `wolfsgeheul.mp3`. WAV, MP3, OGG,
FLAC und M4A werden hier von Git ignoriert. Die aktuelle Sound-/LED-Wiedergabe
verarbeitet MP3 über FFmpeg sowie Mono-WAV mit 16 Bit PCM; HEOS-Formate sind noch zu testen.

Lautstärkeangepasste WAVs erzeugt das Programm dauerhaft in `audio/playback/`.
Diese Dateien werden wiederverwendet und ebenfalls nicht eingecheckt.
Es werden keine Audiodateien unter `/tmp` angelegt. Originale bleiben unverändert.
