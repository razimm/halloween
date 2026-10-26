# Lokale Audiodateien

`electric-zap.wav` wird auf diesem Pi lokal aufbewahrt und von Git ignoriert.

- Quelle: https://www.youtube.com/watch?v=Zfcaj7M0Qnk
- Titel: Electric Shock / Taser Zap | Free Sound Effect
- Urheber: Jochi SFX
- Format: Mono, 16 kHz, 16 Bit PCM, 7,4188125 Sekunden
- Original-Beschreibung: Nutzung in kreativen Projekten erlaubt;
  Verkauf, Weiterverteilung der Sounddatei und Ausgabe als eigenes Werk untersagt.
- Download des Urhebers: https://jochi.bandcamp.com/album/youtube-sfx-pack

Nach einem frischen Clone die Datei separat vom Urheber beziehen und konvertieren:

```bash
ffmpeg -i /pfad/zur/originaldatei -ac 1 -ar 16000 -c:a pcm_s16le audio/electric-zap.wav
```

Andere Schnittfassungen ändern die Zeitmarken. Das Programm analysiert die
bereitgestellte WAV beim Start neu; `shows/electric-zap.json` dokumentiert
die auf diesem Pi getestete Fassung.
